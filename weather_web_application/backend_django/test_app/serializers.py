from rest_framework import serializers
from .models import *


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__' 


class CurrentWeatherSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentWeather
        fields = '__all__'


