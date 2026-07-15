# NutriVision AI – Personalized Nutrition Assistant

NutriVision AI is a full-stack AI-powered nutrition assistant built with **React, Django REST Framework, and Machine Learning**. It analyzes food images, extracts health information from medical reports, and generates personalized diet recommendations using Retrieval-Augmented Generation (RAG).

> **Disclaimer:** This project is for educational purposes only and should not be used for medical diagnosis.

## Features

- 🍽️ Food recognition using **YOLOv8** and nutritional analysis.
- 📄 Medical report analysis using **OCR** and biomarker extraction.
- 🤖 AI nutrition chatbot powered by **RAG** with USDA/WHO nutrition guidelines.
- 🥗 Personalized 7-day diet and meal planning.
- 📊 Interactive dashboard for nutrition tracking and health insights.

## Tech Stack

**Frontend**
- React
- Vite
- TypeScript
- Tailwind CSS

**Backend**
- Django
- Django REST Framework
- MySQL

**AI / ML**
- YOLOv8
- EfficientNet-B0
- OCR (EasyOCR / Tesseract)
- RAG
- Gemini API

## Project Structure

```text
food_analyzer/     Django Backend
frontend/          React Frontend
knowledge_base/    Nutrition Guidelines
README.md
```

## Getting Started

### Backend

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000

Frontend: http://localhost:5173

## Screenshots

(Add screenshots here)

## Future Improvements

- Nutrition progress tracking
- Wearable device integration
- Multi-language chatbot
- Cloud deployment

## License

This project is intended for educational and academic use.
