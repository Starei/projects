from django.urls import path
from rest_framework.routers import DefaultRouter
from test_app.views import *


router = DefaultRouter()
router.register('city', CityViewSet)
router.register('current-weather', CurrentWeatherViewSet)
 
urlpatterns = [
    path('check-city', check_city),
    path('forecast', get_weekly_forecast),
]

urlpatterns += router.urls