import os
from collections import Counter
from PIL import Image
import requests
import io 
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

# NOTE: For security, fetch the key from the environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

try:
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ model  initialized successfully.")
    else:
        gemini_client = None
        print("⚠️ WARNING: GEMINI_API_KEY not set. Gemini analysis is disabled.")
except Exception as e:
    gemini_client = None
    print(f"❌ Error initializing Gemini Client: {e}. Gemini analysis will be disabled.")

# Define the structured output format for Gemini
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

# --- Configuration ---
# Define the minimum confidence threshold for YOLOv8 detection
YOLO_CONFIDENCE_THRESHOLD = 0.50 

print("--- LOADING ML_UTILS.PY (YOLOv8 -> Gemini -> Hub B0 Version) ---")

# --- Nutrition API Configuration ---
USDA_API_KEY = os.environ.get("USDA_API_KEY", "YOUR_FALLBACK_API_KEY_HERE") 
USDA_API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# --- Model Loading Section (REVERTED TO ORIGINAL B0) ---
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

# 2. Load ORIGINAL EfficientNetB0 Model (Generalist Fallback) - REVERTED
try:
    B0_MODEL_URL = "https://tfhub.dev/google/imagenet/efficientnet_v2_imagenet1k_b0/classification/2"
    IMAGE_NET_LABELS_URL = "https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt"
    b0_model = hub.load(B0_MODEL_URL)
    response = requests.get(IMAGE_NET_LABELS_URL)
    response.raise_for_status()
    labels_raw = response.text.split("\n")
    imagenet_labels = [label.strip() for label in labels_raw if label.strip()]
    print("✅ ORIGINAL EfficientNetB0 fallback model loaded successfully.")
except Exception as e:
    b0_model = None
    print(f"❌ Error loading ORIGINAL B0 model (online download): {e}")


# --- Helper & Prediction Functions ---

def preprocess_image_for_b0(image_path, target_size=(224, 224)):
    # Standard preprocessing for Hub models (Resize and scale)
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    img_array = np.array(img) / 255.0 # Must scale back to [0, 1] for original Hub model
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def detect_and_count_foods(image_path):
    # Tier 1 Logic
    if not yolo_model: return None, "Error: YOLO Model not loaded."
    try:
        results = yolo_model(image_path)
        detected_items = []
        
        # 1. Filter detections by confidence
        for box in results[0].boxes:
            confidence = box.conf.item() 
            
            if confidence >= YOLO_CONFIDENCE_THRESHOLD:
                item_name = yolo_model.names[int(box.cls)].title()
                detected_items.append(item_name)
                
        # 2. CRUCIAL FIX: Implement single-item fallback logic
        num_reliable_detections = len(detected_items)
        
        if num_reliable_detections > 1:
            # Success: YOLO found multiple reliable items, use YOLO results.
            print(f"DEBUG: YOLO found {num_reliable_detections} reliable items. Using YOLO results.")
            return Counter(detected_items), None
        
        else: 
            # If 0 or 1 item is found, force the system to Tier 2 (Gemini) 
            print(f"DEBUG: YOLO found {num_reliable_detections} items. Forcing fallback to Tier 2 .")
            return None, None 

    except Exception as e:
        return None, f"Error during YOLO prediction: {e}"

def analyze_with_gemini(image_path):
    if not gemini_client:
        return None, "Error: Gemini Client failed or API key not set."
    
    try:
        img = Image.open(image_path)
        prompt = (
            "Task: Analyze the image and identify ALL distinct food items present. "
            "Constraint: **DO NOT provide any prose, descriptions, greetings, or commentary.** "
            "Output must STRICTLY adhere to the JSON schema provided. "
            "For mixed dishes (like 'Lemon Rice'), treat them as a single item. Ignore non-food items."
        )

        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=[prompt, img],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FOOD_SCHEMA,
            )
        )
        
        food_list = json.loads(response.text)
        
        if food_list:
            gemini_counts = Counter({item['food_name'].title(): item['quantity'] for item in food_list})
            return gemini_counts, None
        
        return None, "Gemini analysis returned no food items."

    except Exception as e:
        return None, f"Error during Gemini analysis: {e}"

def predict_single_food(image_path):
    # Tier 3 Logic
    if not b0_model: return "Error: B0 Model not loaded.", None
    try:
        processed_image = preprocess_image_for_b0(image_path)
        tensor_image = tf.convert_to_tensor(processed_image, dtype=tf.float32)
        predictions = b0_model(tensor_image)
        predicted_index = np.argmax(predictions[0])
        # Output uses ImageNet labels (broad, non-food specific)
        return imagenet_labels[predicted_index].replace("_", " ").title(), None 
    except Exception as e:
        return "Prediction Error", f"Error during B0 prediction: {e}"

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

# --- Main Orchestrator Function ---
def handle_uploaded_image(image_file):
    
    # 1. Save the initial uploaded file
    path = default_storage.save(f"tmp/{image_file.name}", ContentFile(image_file.read()))
    original_path = default_storage.path(path)
    full_path = original_path
    
    # Convert image to RGB JPEG to guarantee YOLOv8/OpenCV compatibility (handles AVIF, WebP, PNG, HEIC)
    try:
        with Image.open(original_path) as img:
            converted_path = os.path.splitext(original_path)[0] + '_converted.jpg'
            img.convert('RGB').save(converted_path, 'JPEG') 
            full_path = converted_path
            print(f"DEBUG: Successfully converted image of format {img.format} to JPEG: {full_path}")
    except Exception as e:
        print(f"WARNING: Could not convert file to JPEG: {e}. Attempting analysis with original file.")
    
    aggregated_nutrition = {"items": [],"totals": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}}
    error_message = None
    food_counts = None

    try:
        # 🟢 Tier 1: YOLOv8 (Fast Check with Confidence Filter)
        print("🟢 Tier 1: Attempting analysis with YOLOv8...")
        food_counts, yolo_error = detect_and_count_foods(full_path)
        
        if food_counts:
            print(f"✅ YOLOv8 detected: {food_counts}")
        elif yolo_error:
            error_message = yolo_error 
            print(f"❌ YOLOv8 Error: {yolo_error}")

        # 🟡 Tier 2: GEMINI (Multimodal Fallback, if YOLO was uncertain/missed)
        if not food_counts and gemini_client:
            print("🟡 Tier 2: YOLO uncertain/missed. Falling back to GEMINI...")
            food_counts, gemini_error = analyze_with_gemini(full_path)
            
            if food_counts:
                print(f"✅ Gemini detected: {food_counts}")
                error_message = None  # Clear previous errors if fallback succeeds
            elif gemini_error:
                error_message = gemini_error
                print(f"❌ Gemini Error: {gemini_error}")

        # 🔴 Tier 3: ORIGINAL B0 (Local Last Resort, if both failed)
        if not food_counts and b0_model:
            print("🔴 Tier 3: Gemini/YOLO failed. Falling back to ORIGINAL EfficientNetB0...")
            predicted_name, b0_error = predict_single_food(full_path)
            
            if predicted_name and predicted_name != "Prediction Error":
                food_counts = Counter({predicted_name: 1})
                print(f"✅ B0 detected: {food_counts}")
                error_message = None  # Clear previous errors if fallback succeeds
            elif b0_error:
                error_message = b0_error
                print(f"❌ B0 Error: {b0_error}")

        # --- Aggregation Logic ---
        if food_counts:
            for food_name, quantity in food_counts.items():
                
                base_nutrition = get_nutrition_data(food_name, 1)
                
                # FIX: Retry lookup with a simplified name if the specific prediction fails 
                if not base_nutrition:
                    print(f"DEBUG: Initial lookup failed for: {food_name}. Retrying with generic term.")
                    simple_name = food_name.split()[-1] 
                    
                    if simple_name != food_name: 
                        base_nutrition = get_nutrition_data(simple_name, 1)

                if base_nutrition:
                    item_total_nutrition = {k: v * quantity for k, v in base_nutrition.items() if isinstance(v, (int, float))}
                    item_details = {"name": food_name, "quantity": quantity, "nutrition": item_total_nutrition}
                    aggregated_nutrition["items"].append(item_details)
                    for key in aggregated_nutrition["totals"]:
                        aggregated_nutrition["totals"][key] += item_total_nutrition.get(key, 0)
                else:
                    print(f"WARNING: Could not find nutrition data for: {food_name}")

        
        if not aggregated_nutrition["items"]:
            error_message = error_message or "Could not analyze image or find any food items."

    finally:
        # Clean up the original uploaded file and the converted file (if it exists)
        if default_storage.exists(original_path):
            default_storage.delete(original_path)
        if full_path != original_path and default_storage.exists(full_path):
             default_storage.delete(full_path)
        
    return aggregated_nutrition, error_message