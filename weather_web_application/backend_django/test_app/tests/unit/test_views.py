from datetime import datetime, timedelta
from unittest import skip

import pandas as pd
from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from ...models import City, Station

'''
def change_managed_settings_just_for_tests():
    """ Making models """

    model_names = {'city', 'station'}
    unmanaged_models = [
        m for m in apps.get_models() if m._meta.model_name in model_names
    ]
    print(unmanaged_models)
    for m in unmanaged_models:
        m._meta.managed = True

change_managed_settings_just_for_tests()
'''


class CityViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("search-for-city")

    def test_city_name(self):
        request_data = [
            # If a city was not found with such a name
            ({"city": "A"}, 404),
            # If several cities were found with the same name
            ({"city": "Brest"}, 202),
            # If one city was found with such a name
            ({"city": "Minsk"}, 200),
        ]
        for data, expected_status_code in request_data:
            resp = self.client.get(self.url, data=data)
            self.assertEqual(resp.json()["status"], expected_status_code)

    def test_loc_coords(self):
        # The coordinates of Brest city
        request_data = {"lat": 52.10, "lng": 23.72}
        resp = self.client.get(self.url, request_data)
        data = resp.json()

        # If status codes were correct
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["status"], 200)

        # If the city data was correct
        city_data = data["cityData"]
        self.assertEqual(city_data["name"], "Brest")
        self.assertEqual(city_data["country"], "Belarus")


@skip("It lasts too long")
class WeeklyForecastViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("weekly-forecast")

    def test_get_weekly_forecast(self):
        request_data = {"lat": 52.10, "lng": 23.72}
        resp = self.client.get(self.url, request_data)
        forecast = dict(resp.json())

        # Test if all parameters are in the data
        dict_keys = [
            "max_temperature",
            "min_temperature",
            "calendar_date",
            "precipitation",
        ]
        self.assertListEqual(list(forecast.keys()), dict_keys)

        # Test if each parameter has weekly data
        num_predicted_days = 7  # A week = 7 days
        self.assertTrue(
            all(
                key
                for key in forecast.keys()
                if len(forecast[key]) == num_predicted_days
            )
        )

        # Test if a temperature is within its known boundaries
        lowest_temp, highest_temp = -89.2, 56.7
        for temp in ["max_temperature", "min_temperature"]:
            self.assertTrue(
                all(
                    val
                    for val in forecast[temp]
                    if lowest_temp <= val <= highest_temp
                )
            )

        # Test if precipitation is within its known boundaries
        max_precip = 1870
        self.assertTrue(
            all(
                val
                for val in forecast["precipitation"]
                if 0 <= val <= max_precip
            )
        )

        # Test if calendar dates are correct
        calendar_dates = (
            pd.date_range(
                start=datetime.today().strftime("%Y-%m-%d"),
                end=(datetime.today() + timedelta(days=7)).strftime("%Y-%m-%d"),
                freq="D",
            )
            .strftime("%a %d")
            .to_list()
        )
        self.assertListEqual(forecast["calendar_date"], calendar_dates)
