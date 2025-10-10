# food_analyzer/planner_engine.py
from .models import UserProfile, Meal
import random
from django.db.models import Q

# No changes needed for calculate_tdee
def calculate_tdee(profile: UserProfile):
    if not all([profile.gender, profile.weight_kg, profile.height_cm, profile.age, profile.activity_level]):
        return 2000 # Return a default value if profile is incomplete

    if profile.gender == 'M':
        bmr = 88.362 + (13.397 * profile.weight_kg) + (4.799 * profile.height_cm) - (5.677 * profile.age)
    else: # 'F'
        bmr = 447.593 + (9.247 * profile.weight_kg) + (3.098 * profile.height_cm) - (4.330 * profile.age)
    
    tdee = bmr * profile.activity_level
    
    if profile.goal == 'lose':
        return tdee - 500
    elif profile.goal == 'gain':
        return tdee + 500
    else:
        return tdee

# In food_analyzer/planner_engine.py

def generate_meal_plan(profile: UserProfile):
    target_calories = calculate_tdee(profile)
    
    # 1. Start with all meals
    all_meals = Meal.objects.all()
    
    # 2. **CRITICAL FIX**: Use a more specific filter for diet type
    if profile.diet_type == 'veg':
        # Find meals that contain 'veg' BUT EXCLUDE those that also contain 'non-veg'
        all_meals = all_meals.filter(Q(tags__icontains='veg') & ~Q(tags__icontains='non-veg'))
    elif profile.diet_type == 'nonveg':
        # This filter remains the same and is correct
        all_meals = all_meals.filter(tags__icontains='non-veg')
    # If diet_type is 'any', we don't filter by diet.

    # 3. Filter the remaining meals by the user's goal
    if profile.goal == 'lose':
        goal_tag = 'weight-loss'
    elif profile.goal == 'gain':
        goal_tag = 'weight-gain'
    else: # maintain
        goal_tag = 'maintenance'
        
    goal_specific_meals = all_meals.filter(tags__icontains=goal_tag)
    
    # 4. Filter out any allergens
    user_allergies = [allergy.strip().lower() for allergy in profile.allergies.split(',') if allergy.strip()]
    
    safe_meals = []
    for meal in goal_specific_meals:
        is_safe = True
        for allergy in user_allergies:
            if allergy in meal.name.lower() or allergy in meal.tags.lower():
                is_safe = False
                break
        if is_safe:
            safe_meals.append(meal)

    # 5. Select random meals from the final, safe list
    plan = {
        'breakfast': random.choice([m for m in safe_meals if m.meal_type == 'breakfast']) if any(m.meal_type == 'breakfast' for m in safe_meals) else None,
        'lunch': random.choice([m for m in safe_meals if m.meal_type == 'lunch']) if any(m.meal_type == 'lunch' for m in safe_meals) else None,
        'dinner': random.choice([m for m in safe_meals if m.meal_type == 'dinner']) if any(m.meal_type == 'dinner' for m in safe_meals) else None,
    }
    
    total_calories = sum(meal.calories for meal in plan.values() if meal)
            
    return {'plan': plan, 'target_calories': target_calories, 'plan_calories': total_calories}

