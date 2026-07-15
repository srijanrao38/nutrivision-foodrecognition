# food_analyzer/urls.py
from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # Existing Web Views
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('log_meal/', views.log_meal_view, name='log_meal'),
    path('log_meal/confirm/', views.log_meal_confirm_view, name='log_meal_confirm'),
    path('api/get-nutrition/', views.get_nutrition_data_view, name='api_get_nutrition'),

    # New REST API Endpoints
    path('api/auth/register/', api_views.register_api, name='api_register'),
    path('api/auth/login/', api_views.login_api, name='api_login'),
    path('api/auth/logout/', api_views.logout_api, name='api_logout'),
    path('api/profile/', api_views.profile_api, name='api_profile'),
    path('api/medical/upload/', api_views.upload_medical_report_api, name='api_medical_upload'),
    path('api/medical/history/', api_views.medical_report_history_api, name='api_medical_history'),
    path('api/food/detect/', api_views.detect_food_api, name='api_food_detect'),
    path('api/food/log/', api_views.food_log_api, name='api_food_log'),
    path('api/chat/', api_views.chat_api, name='api_chat'),
    path('api/recommendations/generate/', api_views.generate_diet_recommendation_api, name='api_recommendation_generate'),
    path('api/recommendations/history/', api_views.diet_recommendation_history_api, name='api_recommendation_history'),
]