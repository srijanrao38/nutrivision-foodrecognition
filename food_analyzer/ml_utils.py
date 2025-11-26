import os
from collections import Counter
from PIL import Image
import requests
import json 

# Django Imports
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# AI/ML Imports
from ultralytics import YOLO
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np

# --- Gemini Imports and Configuration ---
from google import genai
from google.genai import types

# NOTE: Using the provided key directly for testing
GEMINI_API_KEY = "AIzaSyDfOGu27WRMfUCWnI2nHMoXgGQ-kXG06u0"

# --- FIX: Initialize the Client object using the API key ---
try:
    # Initialize a global client object
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Gemini Client initialized successfully.")
except Exception as e:
    gemini_client = None
    print(f"❌ Error initializing Gemini Client: {e}. Gemini analysis will be disabled.")

# Define the structured output format (JSON Schema) for Gemini
FOOD_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    description="A list of all food items detected in the image.",
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "food_name": types.Schema(type=types.Type.STRING, description="The specific name of the food item."),
            "quantity": types.Schema(type=types.Type.INTEGER, description="The count or quantity of the food item.")
        },
        required=["food_name", "quantity"]
    )
)
# ----------------------------------------

print("--- LOADING ML_UTILS.PY (Gemini -> YOLO -> B0 Version) ---")

# --- Nutrition API Configuration ---
USDA_API_KEY = os.environ.get("USDA_API_KEY", "YOUR_FALLBACK_API_KEY_HERE")
USDA_API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# --- Model Loading Section ---
yolo_model = None
b0_model = None
imagenet_labels = []

# 1. Load Custom YOLOv8 Model (The Specialist)
try:
    YOLO_MODEL_PATH = os.path.join(settings.BASE_DIR, 'ml_models', 'best.pt')
    if os.path.exists(YOLO_MODEL_PATH):
        yolo_model = YOLO(YOLO_MODEL_PATH)
        print("✅ YOLOv8 model loaded successfully.")
    else:
        print(f"⚠️ WARNING: YOLOv8 model file not found at {YOLO_MODEL_PATH}")
except Exception as e:
    print(f"❌ Error loading YOLOv8 model: {e}")

# 2. Load EfficientNetB0 Model (The Generalist Fallback)
try:
    B0_MODEL_URL = "https://tfhub.dev/google/imagenet/efficientnet_v2_imagenet1k_b0/classification/2"
    IMAGE_NET_LABELS_URL = "https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt"
    b0_model = hub.load(B0_MODEL_URL)
    response = requests.get(IMAGE_NET_LABELS_URL)
    response.raise_for_status()
    labels_raw = response.text.split("\n")
    imagenet_labels = [label.strip() for label in labels_raw if label.strip()]
    print("✅ EfficientNetB0 fallback model loaded successfully.")
except Exception as e:
    print(f"⚠️ WARNING: Could not load fallback B0 model: {e}")


# --- Helper & Prediction Functions ---

def preprocess_image_for_b0(image_path, target_size=(224, 224)):
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def detect_and_count_foods(image_path):
    if not yolo_model: return None, "Error: YOLO Model not loaded."
    try:
        results = yolo_model(image_path)
        detected_items = [yolo_model.names[int(box.cls)].title() for box in results[0].boxes]
        return Counter(detected_items), None
    except Exception as e:
        return None, f"Error during YOLO prediction: {e}"

def predict_single_food(image_path):
    if not b0_model: return "Error: B0 Model not loaded.", None
    try:
        processed_image = preprocess_image_for_b0(image_path)
        tensor_image = tf.convert_to_tensor(processed_image, dtype=tf.float32)
        predictions = b0_model(tensor_image)
        predicted_index = np.argmax(predictions[0])
        return imagenet_labels[predicted_index].replace("_", " ").title(), None
    except Exception as e:
        return "Prediction Error", f"Error during B0 prediction: {e}"

def analyze_with_gemini(image_path):
    # Check if the client failed to initialize at startup
    if not gemini_client:
        return None, "Error: Gemini Client failed to initialize."
    
    try:
        # 1. Load the image and create the prompt
        img = Image.open(image_path)
        prompt = (
            "You are an expert food detection system. Analyze the uploaded image and identify ALL distinct food items present in the meal. "
            "Ignore plates, cutlery, or backgrounds. For mixed dishes (like 'Lemon Rice'), treat them as a single item."
        )

        # 2. Call the Gemini API using the client object
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=[prompt, img],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FOOD_SCHEMA,
            )
        )
        
        # 3. Parse the JSON response
        food_list = json.loads(response.text)
        
        # 4. Convert the list into the Counter format expected by the main function
        gemini_counts = Counter({item['food_name'].title(): item['quantity'] for item in food_list})
        return gemini_counts, None

    except Exception as e:
        return None, f"Error during Gemini analysis: {e}"

def get_nutrition_data(food_name, quantity=1):
    query = f"{quantity} {food_name}"
    params = {'api_key': USDA_API_KEY, 'query': query, 'pageSize': 1}
    try:
        response = requests.get(USDA_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data and "foods" in data and data["foods"]:
            food_data = data["foods"][0]
            nutrients = {n['nutrientName']: n.get('value', 0) for n in food_data.get('foodNutrients', [])}
            return {"name": food_data.get("description", food_name).title(), "calories": nutrients.get("Energy", 0), "protein_g": nutrients.get("Protein", 0), "carbs_g": nutrients.get("Carbohydrate, by difference", 0), "fat_g": nutrients.get("Total lipid (fat)", 0)}
    except Exception as e:
        print(f"USDA API error for query '{query}': {e}")
    return None

# --- Main Orchestrator Function (UPDATED WITH FIX) ---
def handle_uploaded_image(image_file):
    path = default_storage.save(f"tmp/{image_file.name}", ContentFile(image_file.read()))
    full_path = default_storage.path(path)
    
    aggregated_nutrition = {"items": [],"totals": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}}
    error_message = None
    
    # FIX: Initialize variables outside of conditional blocks
    food_counts = None
    
    try:
        # 🟢 Tier 1: Try the Generalist/Multimodal (Gemini)
        if gemini_client:
            print("🟢 Tier 1: Attempting analysis with Gemini...")
            gemini_counts, gemini_error = analyze_with_gemini(full_path)
            
            if gemini_counts:
                food_counts = gemini_counts
                print(f"✅ Gemini detected: {food_counts}")
            elif gemini_error:
                error_message = gemini_error 
                print(f"❌ Gemini Error: {gemini_error}")

        # 🟡 Tier 2: If Gemini failed, FALLBACK to Specialist (YOLOv8)
        if not food_counts:
            print("🟡 Tier 2: Gemini failed or was disabled. Falling back to YOLOv8...")
            yolo_counts, yolo_error = detect_and_count_foods(full_path)
            
            if yolo_counts:
                food_counts = yolo_counts
                print(f"✅ YOLOv8 detected: {food_counts}")
            elif yolo_error:
                # Use the YOLO error message if no other error exists
                error_message = yolo_error
                print(f"❌ YOLOv8 Error: {yolo_error}")

        # 🔴 Tier 3: If both failed, use the last resort Generalist (B0)
        if not food_counts and b0_model:
            print("🔴 Tier 3: Both Gemini and YOLO failed. Attempting EfficientNetB0...")
            predicted_name, b0_error = predict_single_food(full_path)
            
            if predicted_name and predicted_name != "Prediction Error":
                food_counts = Counter({predicted_name: 1})
                print(f"✅ B0 detected: {food_counts}")
            elif b0_error:
                error_message = b0_error 
                print(f"❌ B0 Error: {b0_error}")

        # --- Aggregation Logic ---
        if food_counts:
            for food_name, quantity in food_counts.items():
                base_nutrition = get_nutrition_data(food_name, 1)
                if base_nutrition:
                    item_total_nutrition = {k: v * quantity for k, v in base_nutrition.items() if isinstance(v, (int, float))}
                    item_details = {"name": food_name, "quantity": quantity, "nutrition": item_total_nutrition}
                    aggregated_nutrition["items"].append(item_details)
                    for key in aggregated_nutrition["totals"]:
                        aggregated_nutrition["totals"][key] += item_total_nutrition.get(key, 0)
        
        if not aggregated_nutrition["items"]:
            error_message = error_message or "Could not identify food with any available AI model."

    finally:
        if default_storage.exists(path):
            default_storage.delete(path)
        
    return aggregated_nutrition, error_message