# food_analyzer/api_views.py
import os
import re
import json
import logging
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser

from .models import UserProfile, MedicalReport, FoodDetectionLog, DietRecommendation, ChatHistory
from .serializers import (
    UserProfileSerializer, MedicalReportSerializer, FoodDetectionLogSerializer,
    DietRecommendationSerializer, ChatHistorySerializer
)
from .ocr_engine import run_hybrid_biomarker_pipeline
from .rag_engine import retrieve_relevant_chunks
from . import ml_utils

logger = logging.getLogger(__name__)

# Medical Disclaimer CONSTANT
DISCLAIMER = "Disclaimer: All recommendations and analysis provided by NutriVision AI are for educational and informational purposes only. This is not a medical diagnosis or a substitute for professional medical advice, diagnosis, or treatment. Please consult a healthcare professional before making any major changes to your diet or medical regimen."

# -------------------------------------------------------------
# 1. AUTHENTICATION & PROFILE APIs
# -------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """User signup endpoint."""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    
    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        profile = UserProfile.objects.create(user=user)
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """User login endpoint."""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """Revoke user token."""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_api(request):
    """GET or UPDATE user profile details."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
        
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------------------------------------------------
# 2. MEDICAL REPORT APIS
# -------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_medical_report_api(request):
    """Uploads a PDF or image medical report, parses text via hybrid pipeline, and saves biomarkers."""
    if 'file' not in request.FILES:
        return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        
    uploaded_file = request.FILES['file']
    
    # Validation
    if uploaded_file.size > 5 * 1024 * 1024:
        return Response({'error': 'File size exceeds the 5MB limit.'}, status=status.HTTP_400_BAD_REQUEST)
        
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.webp']:
        return Response({'error': 'Invalid file format. Allowed: PDF, JPG, PNG, WEBP.'}, status=status.HTTP_400_BAD_REQUEST)
        
    profile = request.user.userprofile
    
    # Save the file temporarily
    path = default_storage.save(f"medical_reports/{uploaded_file.name}", ContentFile(uploaded_file.read()))
    full_path = default_storage.path(path)
    
    try:
        # Run hybrid OCR / Extraction pipeline
        extracted_data, error = run_hybrid_biomarker_pipeline(full_path)
        if error:
            # Clean up file
            if default_storage.exists(path):
                default_storage.delete(path)
            return Response({'error': error}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        # Create DB record
        report = MedicalReport.objects.create(
            user_profile=profile,
            report_file=path,
            extracted_text=extracted_data["text"],
            summary=extracted_data["summary"],
            blood_sugar=extracted_data["biomarkers"].get("blood_sugar"),
            hba1c=extracted_data["biomarkers"].get("hba1c"),
            cholesterol=extracted_data["biomarkers"].get("cholesterol"),
            ldl=extracted_data["biomarkers"].get("ldl"),
            hdl=extracted_data["biomarkers"].get("hdl"),
            vitamin_d=extracted_data["biomarkers"].get("vitamin_d"),
            vitamin_b12=extracted_data["biomarkers"].get("vitamin_b12"),
            iron=extracted_data["biomarkers"].get("iron"),
            hemoglobin=extracted_data["biomarkers"].get("hemoglobin"),
            blood_pressure=extracted_data["biomarkers"].get("blood_pressure"),
            weight=extracted_data["biomarkers"].get("weight"),
            height=extracted_data["biomarkers"].get("height"),
            bmi=extracted_data["biomarkers"].get("bmi")
        )
        
        # If height/weight are in report, update profile
        if report.height and not profile.height_cm:
            profile.height_cm = report.height
        if report.weight and not profile.weight_kg:
            profile.weight_kg = report.weight
        profile.save()
        
        serializer = MedicalReportSerializer(report)
        return Response({
            'report': serializer.data,
            'disclaimer': DISCLAIMER
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error parsing medical report: {e}")
        # Clean up file
        if default_storage.exists(path):
            default_storage.delete(path)
        return Response({'error': f"Failed to process report: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def medical_report_history_api(request):
    """Retrieves all uploaded medical reports for the user."""
    profile = request.user.userprofile
    reports = MedicalReport.objects.filter(user_profile=profile).order_by('-uploaded_at')
    serializer = MedicalReportSerializer(reports, many=True)
    return Response(serializer.data)

# -------------------------------------------------------------
# 3. FOOD DETECTION & HEALTH SCORE APIS
# -------------------------------------------------------------

def calculate_meal_health_score(food_totals, profile, latest_report):
    """
    Calculates Meal Health Score (0-100) based on user profile goals and latest medical report.
    Returns: score (int), strengths (list), concerns (list), alternatives (list)
    """
    score = 100
    strengths = []
    concerns = []
    alternatives = []
    
    calories = food_totals.get("calories", 0)
    protein = food_totals.get("protein_g", 0)
    carbs = food_totals.get("carbs_g", 0)
    fat = food_totals.get("fat_g", 0)
    
    # 1. Base Macronutrient checks
    if calories > 700:
        score -= 15
        concerns.append("High caloric density in this single meal.")
        alternatives.append("Reduce the portion size or swap deep-fried items for roasted ones.")
    elif calories < 250:
        strengths.append("Light, calorie-controlled meal.")
        
    # 2. Check User Goals
    if profile.diet_low_carb:
        if carbs > 40:
            score -= 15
            concerns.append("Carbohydrate content is high for your Low Carb goal.")
            alternatives.append("Swap white rice, pasta, or bread with cauliflower rice, spiralized zucchini, or leafy greens.")
        else:
            strengths.append("Excellent low-carbohydrate choice.")
            
    if profile.diet_high_protein:
        if protein < 15:
            score -= 15
            concerns.append("Low protein content for a High Protein goal.")
            alternatives.append("Add a protein source like chicken breast, eggs, tofu, fish, or tempeh.")
        else:
            strengths.append("High in protein, supporting your muscle/fitness goal.")
            
    if profile.goal == 'lose' and calories > 550:
        score -= 10
        concerns.append("High calories might hinder your Weight Loss target.")
        
    # 3. Check Medical Report Biomarkers
    if latest_report:
        # High Cholesterol or LDL check
        has_high_cholesterol = False
        if latest_report.cholesterol and latest_report.cholesterol > 200:
            has_high_cholesterol = True
        if latest_report.ldl and latest_report.ldl > 100:
            has_high_cholesterol = True
            
        if has_high_cholesterol:
            if fat > 15:
                score -= 20
                concerns.append("High fat content is risky for elevated cholesterol levels.")
                alternatives.append("Avoid butter, full-fat cheese, and fatty meats. Use olive oil in moderation.")
            else:
                strengths.append("Low fat levels, heart-healthy composition.")
                
        # High Blood Sugar or HbA1c check (Diabetic)
        has_high_sugar = profile.diet_diabetic
        if latest_report.blood_sugar and latest_report.blood_sugar > 100:
            has_high_sugar = True
        if latest_report.hba1c and latest_report.hba1c >= 5.7:
            has_high_sugar = True
            
        if has_high_sugar:
            if carbs > 30:
                score -= 20
                concerns.append("High carbohydrate load can cause a blood sugar spike.")
                alternatives.append("Opt for complex carbohydrates with a low glycemic index, such as beans, oats, or vegetables.")
            else:
                strengths.append("Low glycemic loading, suitable for blood sugar management.")
                
    # Safeguard bounds
    score = max(0, min(100, score))
    
    if score >= 80:
        strengths.append("Overall nutritional balance is excellent.")
    if not concerns:
        strengths.append("No critical dietary concerns identified.")
        
    return score, strengths, concerns, alternatives

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def detect_food_api(request):
    """
    POST image file. Detects food using existing YOLOv8 model (falls back to Gemini / EfficientNetB0).
    Calculates Meal Health Score based on user's active report and goals.
    """
    if 'image' not in request.FILES:
        return Response({'error': 'No image uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        
    image_file = request.FILES['image']
    profile = request.user.userprofile
    latest_report = MedicalReport.objects.filter(user_profile=profile).order_by('-uploaded_at').first()
    
    # Save the file temporarily
    path = default_storage.save(f"food_images/{image_file.name}", ContentFile(image_file.read()))
    full_path = default_storage.path(path)
    
    try:
        # Call the existing handle_uploaded_image (YOLOv8 -> Gemini -> B0)
        # Note: handle_uploaded_image deletes the temp file, but wait!
        # It takes care of deletion inside its finally block. Let's make sure we log correctly.
        # We need to preserve the image if we want to save it to FoodDetectionLog!
        # Let's read the image first so we can save it to our database if needed, or pass it.
        # Let's save a permanent copy of the image.
        permanent_path = f"logged_meals/{request.user.id}_{image_file.name}"
        permanent_file_path = default_storage.save(permanent_path, ContentFile(image_file.read()))
        
        # Reset pointer for handle_uploaded_image
        image_file.seek(0)
        aggregated_nutrition, error = ml_utils.handle_uploaded_image(image_file)
        
        if error or not aggregated_nutrition or not aggregated_nutrition.get("items"):
            # Delete permanent copy
            if default_storage.exists(permanent_file_path):
                default_storage.delete(permanent_file_path)
            return Response({'error': error or "Could not detect food in image."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        # Calculate Meal Health Score
        score, strengths, concerns, alternatives = calculate_meal_health_score(
            aggregated_nutrition["totals"], profile, latest_report
        )
        
        # Save detection log
        first_item = aggregated_nutrition["items"][0]
        logged_detection = FoodDetectionLog.objects.create(
            user_profile=profile,
            image=permanent_file_path,
            food_name=first_item["name"].title(),
            quantity=first_item["quantity"],
            confidence=0.90,  # YOLOv8 default/estimated confidence
            calories=aggregated_nutrition["totals"]["calories"],
            protein_g=aggregated_nutrition["totals"]["protein_g"],
            carbs_g=aggregated_nutrition["totals"]["carbs_g"],
            fat_g=aggregated_nutrition["totals"]["fat_g"],
            health_score=score,
            health_analysis={
                "strengths": strengths,
                "concerns": concerns,
                "alternatives": alternatives
            }
        )
        
        return Response({
            'detection_id': logged_detection.id,
            'image_url': request.build_absolute_uri(logged_detection.image.url) if logged_detection.image else None,
            'items': aggregated_nutrition["items"],
            'totals': aggregated_nutrition["totals"],
            'health_score': {
                'score': score,
                'strengths': strengths,
                'concerns': concerns,
                'alternatives': alternatives
            },
            'disclaimer': DISCLAIMER
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error detecting food: {e}")
        return Response({'error': f"Failed to analyze image: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def food_log_api(request):
    """
    GET: Get all logged detections.
    POST: Log a specific custom food directly without image (for manual logs).
    """
    profile = request.user.userprofile
    
    if request.method == 'GET':
        logs = FoodDetectionLog.objects.filter(user_profile=profile).order_by('-detected_at')
        serializer = FoodDetectionLogSerializer(logs, many=True)
        # Add absolute urls for images
        data = []
        for log, serialized in zip(logs, serializer.data):
            s_data = serialized
            if log.image:
                s_data['image_url'] = request.build_absolute_uri(log.image.url)
            data.append(s_data)
        return Response(data)
        
    elif request.method == 'POST':
        # Manual Logging
        food_name = request.data.get('food_name')
        calories = request.data.get('calories', 0)
        protein = request.data.get('protein_g', 0)
        carbs = request.data.get('carbs_g', 0)
        fat = request.data.get('fat_g', 0)
        quantity = request.data.get('quantity', 1)
        
        if not food_name:
            return Response({'error': 'Food name is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        latest_report = MedicalReport.objects.filter(user_profile=profile).order_by('-uploaded_at').first()
        food_totals = {
            "calories": float(calories) * int(quantity),
            "protein_g": float(protein) * int(quantity),
            "carbs_g": float(carbs) * int(quantity),
            "fat_g": float(fat) * int(quantity)
        }
        
        score, strengths, concerns, alternatives = calculate_meal_health_score(
            food_totals, profile, latest_report
        )
        
        log = FoodDetectionLog.objects.create(
            user_profile=profile,
            food_name=food_name,
            quantity=int(quantity),
            calories=food_totals["calories"],
            protein_g=food_totals["protein_g"],
            carbs_g=food_totals["carbs_g"],
            fat_g=food_totals["fat_g"],
            health_score=score,
            health_analysis={
                "strengths": strengths,
                "concerns": concerns,
                "alternatives": alternatives
            }
        )
        
        # Also log to DailyIntakeLog to maintain backward compatibility
        from .models import DailyIntakeLog
        DailyIntakeLog.objects.create(
            user_profile=profile,
            food_name=f"{quantity}x {food_name.title()}",
            calories=food_totals["calories"],
            protein_g=food_totals["protein_g"],
            carbs_g=food_totals["carbs_g"],
            fat_g=food_totals["fat_g"]
        )
        
        serializer = FoodDetectionLogSerializer(log)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# -------------------------------------------------------------
# 4. CHATBOT WITH RAG CONTEXT API
# -------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_api(request):
    """
    POST API for the AI Chatbot.
    Queries the RAG index, adds medical report biomarkers, uses chat history, and calls Gemini.
    """
    query = request.data.get('message')
    if not query:
        return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    profile = request.user.userprofile
    latest_report = MedicalReport.objects.filter(user_profile=profile).order_by('-uploaded_at').first()
    
    # 1. Retrieve RAG Context
    rag_chunks = retrieve_relevant_chunks(query, top_k=3)
    rag_context = "\n\n".join(rag_chunks)
    
    # 2. Build Biomarker profile context
    biomarkers_text = "None uploaded yet"
    if latest_report:
        biomarkers_text = f"""
        Fasting Blood Sugar: {latest_report.blood_sugar or 'N/A'} mg/dL
        HbA1c: {latest_report.hba1c or 'N/A'}%
        Total Cholesterol: {latest_report.cholesterol or 'N/A'} mg/dL
        LDL Cholesterol: {latest_report.ldl or 'N/A'} mg/dL
        HDL Cholesterol: {latest_report.hdl or 'N/A'} mg/dL
        Vitamin D: {latest_report.vitamin_d or 'N/A'} ng/mL
        Vitamin B12: {latest_report.vitamin_b12 or 'N/A'} pg/mL
        Hemoglobin: {latest_report.hemoglobin or 'N/A'} g/dL
        Blood Pressure: {latest_report.blood_pressure or 'N/A'} mmHg
        BMI: {latest_report.bmi or 'N/A'}
        Summary of report: {latest_report.summary or 'N/A'}
        """
        
    # Build Profile Goals
    profile_text = f"""
    Age: {profile.age or 'N/A'}
    Weight: {profile.weight_kg or 'N/A'} kg
    Height: {profile.height_cm or 'N/A'} cm
    Goal: {profile.get_goal_display() if profile.goal else 'N/A'}
    Diet Type: {profile.get_diet_type_display() if profile.diet_type else 'N/A'}
    Allergies: {profile.allergies or 'None'}
    Low Carb: {'Yes' if profile.diet_low_carb else 'No'}
    High Protein: {'Yes' if profile.diet_high_protein else 'No'}
    Diabetic Diet: {'Yes' if profile.diet_diabetic else 'No'}
    """
    
    # Fetch recent chat logs
    recent_chats = ChatHistory.objects.filter(user_profile=profile).order_by('-timestamp')[:6]
    chat_history_list = []
    for chat in reversed(recent_chats):
        chat_history_list.append(f"{'User' if chat.role == 'user' else 'Assistant'}: {chat.message}")
    history_text = "\n".join(chat_history_list)
    
    # Save User message
    ChatHistory.objects.create(user_profile=profile, role='user', message=query)
    
    from food_analyzer.ml_utils import gemini_client
    
    # Check if Gemini Client is configured
    if gemini_client:
        prompt = f"""
        You are NutriVision AI, an educational Personalized Nutrition Assistant. 
        You must ground your answers in the provided context from nutrition guidelines and the user's health profile.
        
        IMPORTANT RULES:
        1. Keep responses supportive, clear, and focused on dietary/nutritional suggestions.
        2. DO NOT provide a medical diagnosis or prescribe medications.
        3. Ground all advice in the retrieved guidelines and medical report biomarkers.
        4. If a query is not answerable by the retrieved context, combine general nutritional knowledge but state that it is general advice.
        5. Grounding: Never answer only from your internal knowledge base if the context covers the topic.
        
        User Medical Biomarkers:
        {biomarkers_text}
        
        User Nutrition Profile & Goals:
        {profile_text}
        
        Retrieved Reference Guidelines (RAG Context):
        {rag_context}
        
        Recent Conversation History:
        {history_text}
        
        User Question: "{query}"
        
        Provide your grounded nutrition guidance response.
        """
        
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            answer = response.text.strip()
        except Exception as e:
            logger.error(f"Gemini chat generation failed: {e}")
            answer = "I apologize, I encountered an error while processing your request. Please try again."
    else:
        # Fallback Local Heuristic Rule-Engine for Chatbot
        normalized_query = query.lower()
        
        if "avoid" in normalized_query:
            if latest_report and (latest_report.cholesterol and latest_report.cholesterol > 200):
                answer = "Based on your medical report showing high cholesterol, you should avoid foods rich in saturated and trans-fats, such as deep-fried items, butter, fatty cuts of meat, and processed foods. Focus instead on soluble fiber (oats, beans) and unsaturated fats (olive oil, avocados)."
            elif latest_report and (latest_report.blood_sugar and latest_report.blood_sugar > 100):
                answer = "Since your blood sugar biomarkers are elevated, you should avoid high-glycemic index foods. This includes refined white sugar, soda, white bread, white rice, sweets, and processed snacks. Opt for complex carbs with high fiber."
            else:
                answer = "Generally, to maintain healthy nutrition, you should avoid processed foods, items with added high-fructose corn syrup, trans fats (found in commercial baked goods), and excessive sodium. Focus on whole foods."
                
        elif "breakfast" in normalized_query:
            if profile.diet_low_carb:
                answer = "For a Low Carb breakfast, I suggest a spinach and mushroom egg scramble cooked in olive oil, paired with sliced avocado."
            elif profile.diet_type == 'veg' or profile.diet_type == 'vegan':
                answer = "A healthy plant-based breakfast: Oatmeal cooked with almond milk, topped with ground flaxseeds, chia seeds, and a handful of blueberries."
            else:
                answer = "Suggested breakfast: A bowl of oatmeal with fresh berries, or 2 boiled eggs with whole-grain toast and a cup of green tea."
                
        elif "banana" in normalized_query:
            if latest_report and (latest_report.blood_sugar and latest_report.blood_sugar > 100):
                answer = "Bananas are rich in potassium and vitamins, but they do contain natural sugars that can impact blood glucose. Since your blood sugar is elevated, it is recommended to limit banana intake to half a medium banana at a time, preferably paired with a protein or healthy fat (like almonds) to slow digestion."
            else:
                answer = "Yes! Bananas are an excellent source of potassium, vitamin B6, and dietary fiber. They make a perfect pre-workout snack or addition to oatmeal."
                
        elif "protein" in normalized_query:
            if profile.weight_kg:
                target = profile.weight_kg * (1.2 if profile.diet_high_protein else 0.8)
                answer = f"Based on your weight of {profile.weight_kg} kg, your estimated daily protein target is approximately {target:.1f} grams. You can reach this with poultry, fish, eggs, Greek yogurt, tofu, and beans."
            else:
                answer = "Generally, sedentary adults should aim for 0.8g of protein per kg of body weight. For active individuals or those aiming for muscle gain, this target increases to 1.2 to 2.0g per kg daily."
                
        elif "weekly" in normalized_query or "meal plan" in normalized_query:
            answer = "I can generate a complete 7-day personalized meal plan for you! Please navigate to the 'Weekly Meal Planner' page on your dashboard to generate and view your detailed plan."
            
        else:
            # Ground answer using retrieved RAG chunks
            if rag_chunks:
                answer = f"Based on our reference guidelines: {rag_chunks[0]} For specific advice, try asking about breakfast ideas, foods to avoid, banana consumption, or protein targets."
            else:
                answer = "I am NutriVision AI, your nutrition assistant. I can help guide your food choices based on your goals and medical report. Ask me about breakfast suggestions, foods to avoid, or nutrient guidelines!"

    # Save Assistant response to history
    ChatHistory.objects.create(user_profile=profile, role='assistant', message=answer)
    
    return Response({
        'message': answer,
        'disclaimer': DISCLAIMER
    }, status=status.HTTP_200_OK)

# -------------------------------------------------------------
# 5. DIET RECOMMENDATIONS & WEEKLY PLANNER
# -------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_diet_recommendation_api(request):
    """
    POST API to generate a structured 7-day Weekly Meal Plan.
    Tailored to User Goals, Allergies, Diet Type, and Medical Biomarkers.
    """
    profile = request.user.userprofile
    latest_report = MedicalReport.objects.filter(user_profile=profile).order_by('-uploaded_at').first()
    
    # Calculate calorie targets (using planner_engine formulas)
    from .planner_engine import calculate_tdee
    tdee = calculate_tdee(profile)
    
    # Tweak macro targets based on profile goals
    protein_pct = 0.20
    carbs_pct = 0.50
    fat_pct = 0.30
    
    if profile.diet_high_protein:
        protein_pct = 0.30
        carbs_pct = 0.40
        fat_pct = 0.30
    elif profile.diet_low_carb:
        protein_pct = 0.25
        carbs_pct = 0.25
        fat_pct = 0.50
        
    protein_g = (tdee * protein_pct) / 4.0
    carbs_g = (tdee * carbs_pct) / 4.0
    fat_g = (tdee * fat_pct) / 9.0
    fiber_g = 38.0 if profile.gender == 'M' else 25.0
    water_l = 3.0 if profile.gender == 'M' else 2.2
    
    # Check medical report for adjustments
    medical_adjustments = []
    foods_to_eat = ["Leafy greens", "Whole grains", "Lean proteins", "Berries"]
    foods_to_avoid = ["Refined sugar", "Processed meats", "Trans-fats"]
    
    if latest_report:
        if latest_report.cholesterol and latest_report.cholesterol > 200:
            medical_adjustments.append("Reduced saturated fats due to elevated cholesterol.")
            foods_to_avoid.extend(["Butter", "Cheese", "Fried food", "Fatty red meat"])
            foods_to_eat.extend(["Oatmeal", "Beans", "Salmon", "Almonds"])
            fat_g = min(fat_g, (tdee * 0.25) / 9.0)  # Lower fat cap
            
        if latest_report.blood_sugar and latest_report.blood_sugar > 100:
            medical_adjustments.append("Low glycemic index carb constraints due to elevated blood sugar.")
            foods_to_avoid.extend(["White rice", "White bread", "Sweet beverages", "Fruit juice"])
            foods_to_eat.extend(["Quinoa", "Broccoli", "Lentils", "Avocados"])
            carbs_g = min(carbs_g, (tdee * 0.35) / 4.0)  # Lower carb cap
            
        if latest_report.blood_pressure:
            # Try to parse BP
            bp_match = re.match(r'(\d+)\/(\d+)', latest_report.blood_pressure)
            if bp_match and int(bp_match.group(1)) > 130:
                medical_adjustments.append("Low sodium DASH diet recommendation due to hypertension.")
                foods_to_avoid.extend(["Processed snacks", "Canned soups", "Soy sauce", "Table salt"])
                foods_to_eat.extend(["Bananas", "Yogurt", "Spinach", "Garlic"])

    # Retrieve RAG chunks
    rag_chunks = retrieve_relevant_chunks("healthy meal plan", top_k=2)
    rag_context = "\n".join(rag_chunks)
    
    # Generate 7-day meal schedule
    from food_analyzer.ml_utils import gemini_client
    
    if gemini_client:
        prompt = f"""
        Generate a 7-day weekly meal plan for a user with the following profile:
        Age: {profile.age or 'N/A'}
        Weight: {profile.weight_kg or 'N/A'} kg
        Height: {profile.height_cm or 'N/A'} cm
        Goal: {profile.get_goal_display() if profile.goal else 'N/A'}
        Diet Type: {profile.get_diet_type_display() if profile.diet_type else 'N/A'}
        Allergies: {profile.allergies or 'None'}
        Low Carb: {'Yes' if profile.diet_low_carb else 'No'}
        High Protein: {'Yes' if profile.diet_high_protein else 'No'}
        Diabetic Diet: {'Yes' if profile.diet_diabetic else 'No'}
        Medical Report Context: {medical_adjustments}
        Retrieved Guidelines: {rag_context}
        
        Target Daily Calories: {tdee:.0f}
        Protein Target: {protein_g:.0f}g, Carb Target: {carbs_g:.0f}g, Fat Target: {fat_g:.0f}g, Fiber Target: {fiber_g:.0f}g, Water Target: {water_l:.1f}L.

        You must format the plan as a clean JSON object containing:
        1. "weekly_plan": A list of 7 objects representing days. Each day must contain keys: "day" (e.g. "Monday"), "breakfast", "lunch", "dinner", "snack".
        2. "foods_to_eat": A list of recommended food items.
        3. "foods_to_avoid": A list of food items to avoid.
        4. "health_insights": A list of 2-3 specific health insights based on their biomarkers.

        Return ONLY the raw JSON object. Do not include markdown tags.
        """
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            
            clean_text = response.text.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
                clean_text = clean_text.strip()
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3].strip()
                    
            plan_json = json.loads(clean_text)
            
        except Exception as e:
            logger.error(f"Gemini diet planner failed: {e}")
            plan_json = None
    else:
        plan_json = None
        
    # Heuristic fallback if LLM is down/no key
    if not plan_json:
        # Predefined options based on diet type
        meals_pool = {
            "breakfast": [
                "Oats with almond milk, chia seeds, and sliced strawberries",
                "Egg white omelette with spinach, bell peppers, and avocado",
                "Greek yogurt topped with walnuts, honey, and flaxseeds",
                "Quinoa porridge cooked with coconut milk and mixed berries",
                "Whole-wheat toast with mashed avocado, cherry tomatoes, and poached eggs"
            ],
            "lunch": [
                "Grilled chicken breast salad with mixed greens, olive oil, and lemon vinaigrette",
                "Baked tofu bowl with brown rice, steamed broccoli, and sesame-ginger dressing",
                "Lentil soup served with a side of mixed green salad and cucumbers",
                "Quinoa salad mixed with chickpeas, cucumbers, parsley, and feta cheese",
                "Pan-seared salmon with roasted sweet potatoes and asparagus"
            ],
            "dinner": [
                "Baked cod filet with sautéed spinach and zucchini noodles",
                "Stir-fry mixed vegetables (bell peppers, mushrooms, snap peas) with tempeh",
                "Turkey breast meatballs served over spaghetti squash with marinara",
                "Vegetable curry with lentils, carrots, spinach, and brown rice",
                "Grilled chicken breast with roasted Brussels sprouts and quinoa"
            ],
            "snack": [
                "A handful of raw almonds and walnuts",
                "Carrot sticks with 2 tablespoons of hummus",
                "Apple slices with 1 tablespoon of almond butter",
                "A cup of low-fat cottage cheese",
                "Mixed berries (blueberries, raspberries)"
            ]
        }
        
        # Filter pool by vegetarian/vegan if needed
        is_veg = (profile.diet_type == 'veg' or profile.diet_type == 'vegan')
        if is_veg:
            meals_pool["breakfast"] = [m for m in meals_pool["breakfast"] if "egg" not in m.lower()] or [meals_pool["breakfast"][0]]
            meals_pool["lunch"] = [m for m in meals_pool["lunch"] if "chicken" not in m.lower() and "salmon" not in m.lower()]
            meals_pool["dinner"] = [m for m in meals_pool["dinner"] if "chicken" not in m.lower() and "cod" not in m.lower() and "turkey" not in m.lower()]
            
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekly_plan = []
        for idx, day in enumerate(days):
            weekly_plan.append({
                "day": day,
                "breakfast": meals_pool["breakfast"][idx % len(meals_pool["breakfast"])],
                "lunch": meals_pool["lunch"][idx % len(meals_pool["lunch"])],
                "dinner": meals_pool["dinner"][idx % len(meals_pool["dinner"])],
                "snack": meals_pool["snack"][idx % len(meals_pool["snack"])]
            })
            
        plan_json = {
            "weekly_plan": weekly_plan,
            "foods_to_eat": list(set(foods_to_eat)),
            "foods_to_avoid": list(set(foods_to_avoid)),
            "health_insights": [
                f"Calorie target set to {tdee:.0f} kcal based on your {profile.get_goal_display() or 'maintenance'} goals.",
                "High fiber intake is emphasized to aid digestion and metabolic balance.",
                "Consuming 2-3 liters of water daily helps maintain cellular hydration."
            ]
        }

    # Format the complete output structure
    complete_plan_data = {
        "targets": {
            "calories": round(tdee),
            "protein_g": round(protein_g),
            "carbs_g": round(carbs_g),
            "fat_g": round(fat_g),
            "fiber_g": round(fiber_g),
            "water_l": round(water_l, 1)
        },
        "weekly_plan": plan_json.get("weekly_plan"),
        "foods_to_eat": plan_json.get("foods_to_eat"),
        "foods_to_avoid": plan_json.get("foods_to_avoid"),
        "health_insights": plan_json.get("health_insights"),
        "medical_adjustments": medical_adjustments,
        "disclaimer": DISCLAIMER
    }
    
    # Save to recommendation database
    rec = DietRecommendation.objects.create(
        user_profile=profile,
        plan_data=complete_plan_data
    )
    
    serializer = DietRecommendationSerializer(rec)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def diet_recommendation_history_api(request):
    """Retrieves previous diet plans."""
    profile = request.user.userprofile
    recs = DietRecommendation.objects.filter(user_profile=profile).order_by('-generated_at')
    serializer = DietRecommendationSerializer(recs, many=True)
    return Response(serializer.data)
