from django.urls import path
from rest_framework.routers import DefaultRouter
from test_app.views import check_city, get_weekly_forecast

router = DefaultRouter()

urlpatterns = [
    path("check-city", check_city, name="search-for-city"),
    path("forecast", get_weekly_forecast, name="weekly-forecast"),
]

urlpatterns += router.urls
