# food_analyzer/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    
    ACTIVITY_LEVEL_CHOICES = [
        (1.2, 'Sedentary (little or no exercise)'),
        (1.375, 'Lightly active (light exercise/sports 1-3 days/week)'),
        (1.55, 'Moderately active (moderate exercise/sports 3-5 days/week)'),
        (1.725, 'Very active (hard exercise/sports 6-7 days a week)'),
        (1.9, 'Super active (very hard exercise/physical job)'),
    ]
    activity_level = models.FloatField(choices=ACTIVITY_LEVEL_CHOICES, null=True, blank=True)
    
    GOAL_CHOICES = [
        ('lose', 'Weight Loss'),
        ('maintain', 'Weight Maintenance'),
        ('gain', 'Weight Gain'),
        ('muscle', 'Muscle Gain')
    ]
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES, null=True, blank=True)
    
    DIET_CHOICES = [
        ('any', 'Any'),
        ('veg', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('nonveg', 'Non-Vegetarian')
    ]
    diet_type = models.CharField(max_length=10, choices=DIET_CHOICES, default='any')
    
    # Extended diet goals and restrictions
    diet_high_protein = models.BooleanField(default=False)
    diet_low_carb = models.BooleanField(default=False)
    diet_diabetic = models.BooleanField(default=False)
    
    allergies = models.TextField(blank=True, help_text="Comma-separated list, e.g., peanuts, shellfish, dairy")

    def __str__(self):
        return self.user.username

class Meal(models.Model):
    name = models.CharField(max_length=100)
    meal_type = models.CharField(max_length=20, choices=[('breakfast', 'Breakfast'), ('lunch', 'Lunch'), ('dinner', 'Dinner'), ('snack', 'Snack')], default='lunch')
    calories = models.FloatField()
    protein_g = models.FloatField()
    carbs_g = models.FloatField()
    fat_g = models.FloatField()
    tags = models.CharField(max_length=200, blank=True, help_text="e.g., vegetarian, gluten-free")
    recipe = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.meal_type})"

class DailyIntakeLog(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    food_name = models.CharField(max_length=100)
    calories = models.FloatField()
    protein_g = models.FloatField()
    carbs_g = models.FloatField()
    fat_g = models.FloatField()

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.food_name} on {self.date}"

class MedicalReport(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='medical_reports')
    report_file = models.FileField(upload_to='medical_reports/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    
    # Extracted Biomarkers
    blood_sugar = models.FloatField(null=True, blank=True)
    hba1c = models.FloatField(null=True, blank=True)
    cholesterol = models.FloatField(null=True, blank=True)
    ldl = models.FloatField(null=True, blank=True)
    hdl = models.FloatField(null=True, blank=True)
    vitamin_d = models.FloatField(null=True, blank=True)
    vitamin_b12 = models.FloatField(null=True, blank=True)
    iron = models.FloatField(null=True, blank=True)
    hemoglobin = models.FloatField(null=True, blank=True)
    blood_pressure = models.CharField(max_length=20, null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    bmi = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Report {self.id} for {self.user_profile.user.username} ({self.uploaded_at.date()})"

class FoodDetectionLog(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='food_detections')
    image = models.ImageField(upload_to='food_images/', null=True, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    food_name = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    confidence = models.FloatField(null=True, blank=True)
    calories = models.FloatField()
    protein_g = models.FloatField()
    carbs_g = models.FloatField()
    fat_g = models.FloatField()
    health_score = models.IntegerField(null=True, blank=True)
    health_analysis = models.JSONField(null=True, blank=True) # stores strengths, concerns, alternatives

    def __str__(self):
        return f"{self.food_name} detected for {self.user_profile.user.username} on {self.detected_at.date()}"

class DietRecommendation(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='diet_recommendations')
    generated_at = models.DateTimeField(auto_now_add=True)
    plan_data = models.JSONField() # Holds the 7-day meal plan JSON representation

    def __str__(self):
        return f"Plan for {self.user_profile.user.username} generated on {self.generated_at.date()}"

class ChatHistory(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='chats')
    role = models.CharField(max_length=20, choices=[('user', 'User'), ('assistant', 'Assistant')])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat by {self.user_profile.user.username} as {self.role} at {self.timestamp}"