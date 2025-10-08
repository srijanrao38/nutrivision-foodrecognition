# food_analyzer/models.py
from django.db import models
from django.contrib.auth.models import User

# In food_analyzer/models.py

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
    
    GOAL_CHOICES = [('lose', 'Weight Loss'), ('maintain', 'Weight Maintenance'), ('gain', 'Muscle Gain')]
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES, null=True, blank=True)
    
    # --- ADD THIS NEW FIELD ---
    DIET_CHOICES = [('any', 'Any'), ('veg', 'Vegetarian'), ('nonveg', 'Non-Vegetarian')]
    diet_type = models.CharField(max_length=10, choices=DIET_CHOICES, default='any')
    
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