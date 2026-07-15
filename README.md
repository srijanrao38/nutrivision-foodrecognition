# NutriVision AI: Personalized Nutrition Assistant

NutriVision AI is a full-stack, AI-powered Personalized Nutrition Assistant. It integrates a **Django REST Framework** backend and a modern **React + Vite + TypeScript** frontend. The platform combines deep learning models (**YOLOv8** + **EfficientNetB0**), **OCR / Regex-based medical biomarker extraction**, and **Retrieval-Augmented Generation (RAG)** grounded in global nutritional guidelines to deliver personalized nutritional insights and 7-day meal planners.

> [!IMPORTANT]
> **Educational & Informational Disclaimer**
> NutriVision AI is designed for educational and informational purposes only. It is **NOT** a medical diagnostic platform. All suggestions, scores, and food alternatives should be reviewed by a clinical healthcare professional before application.

---

## Key Features

1. **YOLOv8 Meal Image Scanner**: Scan images of food to identify items, compute calorie and macronutrient values (linked with the USDA database), and evaluate a **Meal Health Score (0-100)**.
2. **Hybrid Medical Biomarker Extraction**: Parse laboratory PDF/image reports using OCR (EasyOCR / Tesseract) and rule-based regex parsing, falling back to Gemini only for unstructured values and clinical summaries.
3. **Retrieval-Augmented Generation (RAG)**: Ingest public health guidelines (USDA, WHO, NIH) into a vector database (FAISS/TF-IDF) to ground chatbot responses and prevent model hallucinations.
4. **Interactive AI Chatbot**: Conversational agent grounded in both the loaded guideline guidelines and the user's active clinical biomarker profile.
5. **7-Day Diet Recommendation & Weekly Planner**: Generates target metrics (calories, protein, carbs, fat, fiber, water) and structured meal calendars customized to user weight goals, allergies, and lab results.

---

## Project Structure

```
├── food_analyzer/            # Django Application
│   ├── api_views.py          # REST API Controllers (Auth, Profile, OCR, RAG, Planner)
│   ├── ocr_engine.py         # Hybrid OCR & Regex Extraction Engine
│   ├── rag_engine.py         # Guideline chunker & FAISS / TF-IDF Vector Retriever
│   ├── ml_utils.py           # Deep Learning Model Loader (YOLOv8 fallback)
│   └── models.py             # Extended database models
├── knowledge_base/           # Guideline Reference documents (USDA, WHO, NIH)
├── frontend/                 # React + Vite + TypeScript Frontend
│   ├── src/
│   │   ├── pages/            # Dashboard, FoodDetection, MedicalUpload, WeeklyPlanner, AIChat, Profile
│   │   ├── components/       # Custom Navbar and UI components
│   │   └── api.ts            # Axios configuration
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

---

### Backend Setup (Django)

1. **Activate Virtual Environment**:
   ```bash
   # Windows
   .\venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create or edit the `.env` file in the root directory:
   ```env
   GEMINI_API_KEY="your-gemini-api-key-here"
   USDA_API_KEY="ObxxfuP7HyxcXjFJ3Vx2Ye83FzoduRXyycgFVBRx"
   ```

4. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Ingest Guidelines (Build RAG Vector Index)**:
   This indexes the guidelines text files located in `knowledge_base/` using FAISS (or falls back to TF-IDF if the Gemini key is not configured):
   ```bash
   python manage.py ingest_kb
   ```

6. **Start Backend Server**:
   ```bash
   python manage.py runserver
   ```
   The backend will be running at `http://localhost:8000`.

---

### Frontend Setup (Vite + React)

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install node modules**:
   ```bash
   npm install
   ```

3. **Start Development Server**:
   ```bash
   npm run dev
   ```
   The frontend will be running at `http://localhost:5173`.

---

## Verification & Testing
To run Django system configuration and model verification checks:
```bash
python manage.py check
```
