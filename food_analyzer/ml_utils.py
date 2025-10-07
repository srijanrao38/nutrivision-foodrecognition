# food_analyzer/ml_utils.py
# --- CORRECTED HYBRID VERSION (YOLOv8 + B0 Fallback) ---

from ultralytics import YOLO
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from PIL import Image
import requests
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from collections import Counter

print("--- LOADING ML_UTILS.PY (Hybrid YOLOv8 + B0 Version) ---")

# --- Nutrition API Configuration ---
USDA_API_KEY = os.environ.get("USDA_API_KEY", "YOUR_FALLBACK_API_KEY_HERE")
USDA_API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# --- Model Loading Section ---
yolo_model = None
b0_model = None
imagenet_labels = []

# 1. Load Custom YOLOv8 Model (The Specialist)
YOLO_MODEL_PATH = os.path.join(settings.BASE_DIR, 'ml_models', 'best.pt')
try:
    if os.path.exists(YOLO_MODEL_PATH):
        yolo_model = YOLO(YOLO_MODEL_PATH)
        print("✅ Custom YOLOv8 model loaded successfully.")
    else:
        print(f"❌ WARNING: YOLOv8 model file not found at {YOLO_MODEL_PATH}")
except Exception as e:
    print(f"❌ Error loading custom YOLOv8 model: {e}")

# 2. Load EfficientNetB0 Model (The Generalist Fallback)
B0_MODEL_URL = "https://tfhub.dev/google/imagenet/efficientnet_v2_imagenet1k_b0/classification/2"
IMAGE_NET_LABELS_URL = "https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt"
try:
    b0_model = hub.load(B0_MODEL_URL)
    response = requests.get(IMAGE_NET_LABELS_URL)
    response.raise_for_status()
    labels_raw = response.text.split("\n")
    imagenet_labels = [label.strip() for label in labels_raw if label.strip()]
    if imagenet_labels and imagenet_labels[0].lower() == 'background':
        imagenet_labels = imagenet_labels[1:]
    print("✅ EfficientNetB0 fallback model loaded successfully.")
except Exception as e:
    print(f"❌ WARNING: Could not load fallback B0 model: {e}")


# --- Helper & Prediction Functions ---
def preprocess_image_for_b0(image_path, target_size=(224, 224)):
    img = Image.open(image_path).convert("RGB")
    img = img.resize(target_size)
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def detect_and_count_foods(image_path):
    if yolo_model is None: return None, "Error: YOLO Model not loaded."
    try:
        results = yolo_model(image_path)
        detected_items = [yolo_model.names[int(box.cls)].replace("_", " ").title() for box in results[0].boxes]
        food_counts = Counter(detected_items)
        return dict(food_counts), None
    except Exception as e:
        return None, f"Error during YOLO prediction: {e}"

def predict_single_food(image_path):
    if b0_model is None or not imagenet_labels: return "Error: B0 Model not loaded.", 0.0
    try:
        processed_image = preprocess_image_for_b0(image_path)
        tensor_image = tf.convert_to_tensor(processed_image, dtype=tf.float32)
        predictions = b0_model(tensor_image)
        logits = predictions[0]
        predicted_index = np.argmax(logits)
        predicted_name = imagenet_labels[predicted_index].replace("_", " ").title()
        return predicted_name, None
    except Exception as e:
        return "Prediction Error", f"Error during B0 prediction: {e}"

def get_nutrition_data(food_name, quantity=None):
    if quantity is not None:
        query = f"{quantity} {food_name}"
    else:
        query = food_name
    
    params = {'api_key': USDA_API_KEY, 'query': query, 'pageSize': 1}
    try:
        response = requests.get(USDA_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data and "foods" in data and data["foods"]:
            food_data = data["foods"][0]
            nutrients = {nutrient['nutrientName']: nutrient.get('value', 0) for nutrient in food_data.get('foodNutrients', [])}
            return { "name": food_data.get("description", food_name).title(), "calories": nutrients.get("Energy", 0), "protein_g": nutrients.get("Protein", 0), "carbs_g": nutrients.get("Carbohydrate, by difference", 0), "fat_g": nutrients.get("Total lipid (fat)", 0), "serving_qty": 1, "serving_unit": "serving" }
    except requests.exceptions.RequestException as e:
        print(f"USDA API error for query '{query}': {e}")
    return None

# --- THIS IS THE FULLY RESTORED MAIN FUNCTION ---
def handle_uploaded_image(image_file):
    path = default_storage.save(f"tmp/{image_file.name}", ContentFile(image_file.read()))
    full_path = default_storage.path(path)
    
    aggregated_nutrition = {
        "items": [],
        "totals": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    }
    error_message = None

    try:
        # Step 1: Try the Specialist (YOLOv8) first
        food_counts, error = detect_and_count_foods(full_path)
        if error:
            error_message = error
        
        # If YOLOv8 found items, process them
        if food_counts:
            print(f"✅ YOLOv8 detected: {food_counts}")
            for food_name, quantity in food_counts.items():
                nutrition_info = get_nutrition_data(food_name, quantity)
                if nutrition_info:
                    item_details = {"name": food_name, "quantity": quantity, "nutrition": nutrition_info}
                    aggregated_nutrition["items"].append(item_details)
                    for key in aggregated_nutrition["totals"]:
                        aggregated_nutrition["totals"][key] += nutrition_info.get(key, 0)
        
        # Step 2: If YOLO found nothing, use the Generalist (B0) as a fallback
        elif b0_model:
            print("⚠️ YOLOv8 found no detections. Falling back to EfficientNetB0...")
            predicted_name, error = predict_single_food(full_path)
            if error:
                error_message = error
            
            if predicted_name and predicted_name != "Prediction Error":
                nutrition_info = get_nutrition_data(predicted_name, 1)
                if nutrition_info:
                    item_details = {"name": predicted_name, "quantity": 1, "nutrition": nutrition_info}
                    aggregated_nutrition["items"].append(item_details)
                    aggregated_nutrition["totals"] = nutrition_info
            else:
                error_message = "Fallback model could not identify the food item."
        
        # Step 3: If both models fail
        else:
            error_message = "No food detected and fallback model is not available."

    finally:
        default_storage.delete(path)
    
    return aggregated_nutrition, error_message