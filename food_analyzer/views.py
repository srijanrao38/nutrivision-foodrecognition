# food_analyzer/views.py (Corrected Version)
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import UserProfile, DailyIntakeLog
from .forms import UserProfileForm, ImageUploadForm, CustomUserCreationForm
from . import planner_engine
from . import ml_utils
import datetime

def home_view(request):
    return render(request, 'food_analyzer/home.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'food_analyzer/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'food_analyzer/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=profile)
    # Corrected path below
    return render(request, 'food_analyzer/profile.html', {'form': form})

@login_required
def dashboard_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if not all([profile.age, profile.weight_kg, profile.height_cm, profile.gender, profile.activity_level, profile.goal]):
        return redirect('profile')

    meal_plan_data = planner_engine.generate_meal_plan(profile)
    today = datetime.date.today()
    todays_logs = DailyIntakeLog.objects.filter(user_profile=profile, date=today)
    
    total_calories_today = sum(log.calories for log in todays_logs)
    total_protein_today = sum(log.protein_g for log in todays_logs)
    total_carbs_today = sum(log.carbs_g for log in todays_logs)
    total_fat_today = sum(log.fat_g for log in todays_logs)
    
    target_calories = meal_plan_data.get('target_calories', 2000)
    calories_percentage = (total_calories_today / target_calories * 100) if target_calories > 0 else 0
    calories_percentage_capped = min(calories_percentage, 100)

    context = {
        'meal_plan': meal_plan_data.get('plan'),
        'target_calories': target_calories,
        'plan_calories': meal_plan_data.get('plan_calories', 0),
        'todays_logs': todays_logs,
        'total_calories_today': total_calories_today,
        'total_protein_today': total_protein_today,
        'total_carbs_today': total_carbs_today,
        'total_fat_today': total_fat_today,
        'calories_percentage': calories_percentage_capped,
    }
    # Corrected path below
    return render(request, 'food_analyzer/dashboard.html', context)

@login_required
def log_meal_view(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            aggregated_nutrition, error = ml_utils.handle_uploaded_image(image)
            
            if error or not aggregated_nutrition or not aggregated_nutrition.get("items"):
                # Corrected path below
                return render(request, 'food_analyzer/log_meal.html', {'form': form, 'error': "Could not analyze image or find any food items."})

            request.session['aggregated_nutrition'] = aggregated_nutrition
            return redirect('log_meal_confirm')
    else:
        form = ImageUploadForm()
    # Corrected path below
    return render(request, 'food_analyzer/log_meal.html', {'form': form})

@login_required
def log_meal_confirm_view(request):
    aggregated_nutrition = request.session.get('aggregated_nutrition')
    if not aggregated_nutrition:
        return redirect('log_meal')

    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, user=request.user)
        item_count = int(request.POST.get('item_count', 0))
        
        for i in range(item_count):
            corrected_name = request.POST.get(f'food_name_{i}')
            corrected_quantity = request.POST.get(f'quantity_{i}')

            if corrected_name and corrected_quantity:
                try:
                    quantity = int(corrected_quantity)
                    if quantity <= 0:
                        continue
                    
                    # **THE FIX**: Get base nutrition for the corrected name
                    base_nutrition = ml_utils.get_nutrition_data(corrected_name, 1)
                    
                    if base_nutrition:
                        # **THE FIX**: Do the multiplication before saving to the database
                        DailyIntakeLog.objects.create(
                            user_profile=profile,
                            food_name=f"{quantity}x {corrected_name.title()}",
                            calories=base_nutrition.get('calories', 0) * quantity,
                            protein_g=base_nutrition.get('protein_g', 0) * quantity,
                            carbs_g=base_nutrition.get('carbs_g', 0) * quantity,
                            fat_g=base_nutrition.get('fat_g', 0) * quantity,
                        )
                except (ValueError, TypeError):
                    continue

        del request.session['aggregated_nutrition']
        return redirect('dashboard')
    
    return render(request, 'food_analyzer/log_meal_confirm.html', {'aggregated_nutrition': aggregated_nutrition})
@login_required
def get_nutrition_data_view(request):
    food_name = request.GET.get('food')
    if not food_name:
        return JsonResponse({'error': 'Food name not provided'}, status=400)
    
    nutrition_data = ml_utils.get_nutrition_data(food_name) 
    
    if nutrition_data:
        return JsonResponse(nutrition_data)
    else:
        return JsonResponse({'error': 'Nutrition data not found for this item'}, status=404)