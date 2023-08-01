from django.test import TestCase

from ...models import City, CurrentWeather, Station


class StationModelTest(TestCase):
    STATION_NAME = "test station"
    LAT, LNG = (1, 1)

    station = Station.objects.create(name=STATION_NAME, lat=LAT, lng=LNG)

    def test_field_values(self):
        self.assertEqual(self.station.name, self.STATION_NAME)
        self.assertEqual(self.station.lat, self.LAT)
        self.assertEqual(self.station.lng, self.LNG)


class CityModelTest(TestCase):
    CITY_NAME = "test city"
    COUNTRY = "test country"
    LAT, LNG = (1, 1)
    NEAREST_STATION = StationModelTest.station

    city = City.objects.create(
        name=CITY_NAME,
        country=COUNTRY,
        lat=LAT,
        lng=LNG,
        nearest_station=NEAREST_STATION,
    )

    def test_field_values(self):
        self.assertEqual(self.city.name, self.CITY_NAME)
        self.assertEqual(self.city.country, self.COUNTRY)
        self.assertEqual(self.city.lat, self.LAT)
        self.assertEqual(self.city.lng, self.LNG)
        self.assertEqual(self.city.nearest_station, self.NEAREST_STATION)


class CurrentWeatherModelTest(TestCase):
    CITY = CityModelTest.city
    CALENDAR_DATE = "2023-01-01"
    TEMPERATURE = -5
    FEELS_LIKE = -8
    WEATHER_CONDITION = "SNOWING"
    PRESSURE = 760
    HUMIDITY = 95
    WIND_SPEED = 5
    WIND_DIRECTION = 120
    SUNRISE = "09:13:40"
    SUNSET = "17:28:12"

    @classmethod
    def setUpTestData(cls):
        cls.current_weather = CurrentWeather(
            city=cls.CITY,
            calendar_date=cls.CALENDAR_DATE,
            temperature=cls.TEMPERATURE,
            feels_like=cls.FEELS_LIKE,
            weather_condition=cls.WEATHER_CONDITION,
            pressure=cls.PRESSURE,
            humidity=cls.HUMIDITY,
            wind_speed=cls.WIND_SPEED,
            wind_direction=cls.WIND_DIRECTION,
            sunrise=cls.SUNRISE,
            sunset=cls.SUNSET,
        )

    def test_field_values(self):
        self.assertEqual(self.current_weather.city, self.CITY)
        self.assertEqual(self.current_weather.calendar_date, self.CALENDAR_DATE)
        self.assertEqual(self.current_weather.temperature, self.TEMPERATURE)
        self.assertEqual(self.current_weather.feels_like, self.FEELS_LIKE)
        self.assertEqual(self.current_weather.pressure, self.PRESSURE)
        self.assertEqual(self.current_weather.humidity, self.HUMIDITY)
        self.assertEqual(self.current_weather.wind_speed, self.WIND_SPEED)
        self.assertEqual(
            self.current_weather.wind_direction, self.WIND_DIRECTION
        )
        self.assertEqual(self.current_weather.sunrise, self.SUNRISE)
        self.assertEqual(self.current_weather.sunset, self.SUNSET)
