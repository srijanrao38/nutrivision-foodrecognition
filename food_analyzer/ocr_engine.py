# food_analyzer/ocr_engine.py
import re
import os
import logging
from pypdf import PdfReader
from PIL import Image

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize EasyOCR reader lazily to save startup time
_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            # Initialize reader for English
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
            logger.info("✅ EasyOCR Reader initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize EasyOCR: {e}")
    return _easyocr_reader

def extract_text_from_pdf(pdf_path):
    """Extracts text from a digital PDF using pypdf."""
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
    return text.strip()

def extract_text_from_image(image_path):
    """Extracts text from an image using EasyOCR, falling back to pytesseract."""
    text = ""
    
    # 1. Try EasyOCR
    reader = get_easyocr_reader()
    if reader:
        try:
            results = reader.readtext(image_path, detail=0)
            text = " ".join(results)
            if text.strip():
                logger.info("EasyOCR successfully extracted text.")
                return text.strip()
        except Exception as e:
            logger.warning(f"EasyOCR failed: {e}. Trying pytesseract fallback.")

    # 2. Try pytesseract as fallback
    try:
        import pytesseract
        # Pytesseract requires the PIL Image
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        if text.strip():
            logger.info("Pytesseract successfully extracted text.")
            return text.strip()
    except Exception as e:
        logger.warning(f"Pytesseract fallback failed or not installed: {e}")

    return text.strip()

def extract_text_from_file(file_path):
    """Dispatches to the correct text extractor based on file extension."""
    _, ext = os.path.splitext(file_path.lower())
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
        # If PDF was scanned and has no embedded text, try OCR
        if not text.strip():
            logger.info("PDF has no selectable text. Attempting OCR on PDF pages (not supported without additional libraries, fallback).")
            # We can log this, in a real system we would convert pages to images.
        return text
    elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
        return extract_text_from_image(file_path)
    else:
        logger.warning(f"Unsupported file format for OCR: {ext}")
        return ""

def rule_based_biomarker_extraction(text):
    """
    Extracts biomarkers using predefined regular expression rules.
    Returns a dictionary of found values, mapped to standard float/string types.
    """
    biomarkers = {
        "blood_sugar": None,
        "hba1c": None,
        "cholesterol": None,
        "ldl": None,
        "hdl": None,
        "vitamin_d": None,
        "vitamin_b12": None,
        "iron": None,
        "hemoglobin": None,
        "blood_pressure": None,
        "weight": None,
        "height": None,
        "bmi": None
    }
    
    # Regex patterns
    patterns = {
        "hba1c": r"(?i)(?:hba1c|hb\s*a1c|glycated\s*hemoglobin|a1c)[\s\:\-]*(\d+(?:\.\d+)?)\s*%",
        # Blood sugar (glucose) - look for fasting/random glucose or blood sugar
        "blood_sugar": r"(?i)(?:fasting\s*blood\s*sugar|fbs|fasting\s*glucose|glucose\s*fasting|blood\s*sugar|glucose|rbs)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:mg/dl|mmol/l)?",
        "cholesterol": r"(?i)(?:total\s*cholesterol|cholesterol)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:mg/dl)?",
        "ldl": r"(?i)(?:ldl(?:\s*cholesterol)?|low\s*density\s*lipoprotein)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:mg/dl)?",
        "hdl": r"(?i)(?:hdl(?:\s*cholesterol)?|high\s*density\s*lipoprotein)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:mg/dl)?",
        "vitamin_d": r"(?i)(?:vitamin\s*d|vit\s*d|25-hydroxy\s*vitamin\s*d|25-oh\s*d)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:ng/ml|nmol/l)?",
        "vitamin_b12": r"(?i)(?:vitamin\s*b12|vit\s*b12|b12|cobalamin)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:pg/ml|pmol/l)?",
        "iron": r"(?i)(?:serum\s*iron|iron|fe)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:mcg/dl|ug/dl)?",
        "hemoglobin": r"(?i)(?:hemoglobin|hb|hgb)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:g/dl|g/l)?",
        "blood_pressure": r"(?i)(?:blood\s*pressure|bp)[\s\:\-]*(\d{2,3}\/\d{2,3})",
        "weight": r"(?i)(?:weight|wt)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:kg|kilogram|lbs)?",
        "height": r"(?i)(?:height|ht)[\s\:\-]*(\d+(?:\.\d+)?)\s*(?:cm|centimeter|inches|inch)?",
        "bmi": r"(?i)(?:bmi|body\s*mass\s*index)[\s\:\-]*(\d+(?:\.\d+)?)"
    }

    # Search for each biomarker in the text
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            val = match.group(1)
            if key == "blood_pressure":
                biomarkers[key] = val
            else:
                try:
                    biomarkers[key] = float(val)
                except ValueError:
                    biomarkers[key] = None

    return biomarkers

def gemini_biomarker_fallback(text, extracted_so_far):
    """
    Uses Gemini LLM to extract remaining missing biomarkers and summarize the report.
    """
    from food_analyzer.ml_utils import gemini_client
    if not gemini_client:
        return extracted_so_far, "Gemini client not available. Could not generate summary."

    missing_keys = [k for k, v in extracted_so_far.items() if v is None]
    if not missing_keys and extracted_so_far.get("summary"):
        # Everything extracted and summary present
        return extracted_so_far, ""

    prompt = f"""
    Analyze the following medical report text and extract the values for these specific parameters:
    {', '.join(missing_keys)}

    Report Text:
    ---
    {text}
    ---

    Instructions:
    1. Extract the numerical values (or string for blood_pressure like '120/80') for each requested parameter.
    2. If a parameter is NOT mentioned in the text, return null for it.
    3. Keep values strictly as they appear (or converted to standard units: blood sugar in mg/dL, cholesterol in mg/dL, height in cm, weight in kg).
    4. Provide a brief 2-3 sentence educational summary of the health findings in the report (highlighting any values out of range).
    5. Return the result STRICTLY as a JSON object with keys:
       "extracted_values": {{ "parameter_name": value or null }},
       "summary": "Educational summary of findings"

    Do not include any Markdown styling (like ```json) or explanation, return ONLY the raw JSON.
    """

    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # Parse output
        import json
        clean_text = response.text.strip()
        # Remove markdown code blocks if any
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:]
            clean_text = clean_text.strip()
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3].strip()

        data = json.loads(clean_text)
        
        # Fill in the missing values
        gemini_vals = data.get("extracted_values", {})
        for key in missing_keys:
            if key in gemini_vals and gemini_vals[key] is not None:
                extracted_so_far[key] = gemini_vals[key]
                
        summary = data.get("summary", "Medical report successfully parsed.")
        return extracted_so_far, summary
    except Exception as e:
        logger.error(f"Gemini biomarker extraction fallback failed: {e}")
        return extracted_so_far, "Failed to analyze report with AI."

def run_hybrid_biomarker_pipeline(file_path):
    """
    Runs the full hybrid extraction pipeline:
    1. Extract text from PDF/Image.
    2. Run Regex/Rule-based biomarker extraction.
    3. Run Gemini fallback for missing values and summary.
    """
    text = extract_text_from_file(file_path)
    if not text.strip():
        return None, "Failed to extract text from file."

    # Run rule-based regex
    biomarkers = rule_based_biomarker_extraction(text)
    
    # Run Gemini fallback
    final_biomarkers, summary = gemini_biomarker_fallback(text, biomarkers)
    
    return {
        "text": text,
        "biomarkers": final_biomarkers,
        "summary": summary
    }, None
