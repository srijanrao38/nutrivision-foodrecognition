# food_analyzer/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, MedicalReport, FoodDetectionLog, DietRecommendation, ChatHistory

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'age', 'weight_kg', 'height_cm', 'gender', 
            'activity_level', 'goal', 'diet_type', 
            'diet_high_protein', 'diet_low_carb', 'diet_diabetic', 
            'allergies'
        ]

class MedicalReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalReport
        fields = '__all__'

class FoodDetectionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodDetectionLog
        fields = '__all__'

class DietRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietRecommendation
        fields = '__all__'

class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = '__all__'
