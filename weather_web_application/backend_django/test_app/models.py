from django.db import models


class Location(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()

    class Meta:
        # It will cause a single table to be generated from a subclass
        # with added columns from this base class
        abstract = True


class Station(Location):
    name = models.CharField(max_length=20)

    class Meta:
        db_table = 'world_stations'
        managed = False


class City(Location):
    name = models.CharField(max_length=50)
    country = models.CharField(max_length=50)

    class Meta:
        db_table = 'world_cities'
        managed = False


class Datetime(models.Model):
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        abstract = True


class CurrentWeather(Datetime):
    city = models.OneToOneField(
        City, primary_key=True, on_delete=models.CASCADE
    )
    calendar_date = models.DateField()
    temperature = models.IntegerField()
    feels_like = models.IntegerField()
    weather_condition = models.CharField(max_length=30)
    pressure = models.IntegerField()
    humidity = models.IntegerField()
    wind_speed = models.IntegerField()
    wind_direction = models.IntegerField()
    sunrise = models.TimeField()
    sunset = models.TimeField()

    class Meta:
        db_table = 'current_weather'



