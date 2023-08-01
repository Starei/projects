"""
SimpleTestCase disallows database queries by default.

A TransactionTestCase resets the database after the test runs by truncating all tables.

A TestCase, on the other hand, does not truncate tables after a test. Instead, it encloses the test code in a database transaction that is rolled back at the end of the test. This guarantees that the rollback at the end of the test restores the database to its initial state.

So we will use a TestCase because one needs to get data from a database and
not delete them after running tests.
"""

from datetime import datetime, timedelta
from unittest import skip

from django.test import TestCase

from ...ml_part.data_workflow import (
    DataCollection,
    ERA5Service,
    NOAACleaning,
    NOAAService,
)

TIME_FORMAT = None
start_date = None
end_date = None
diff_in_days = None


def setUpModule():
    global start_date, end_date, diff_in_days, TIME_FORMAT
    TIME_FORMAT = r"%Y-%m-%d"
    start_date = "2010-01-01"
    end_date = "2023-07-20"
    diff_in_days = abs(
        (
            datetime.strptime(start_date, TIME_FORMAT)
            - datetime.strptime(end_date, TIME_FORMAT)
        ).days
    )


def tearDownModule():
    global start_date, end_date, diff_in_days, TIME_FORMAT
    del start_date, end_date, diff_in_days, TIME_FORMAT


class DataCollectionTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # Specifying the correct values.
        cls.loc_coords = (53.9, 27.56)
        cls.data_types = ["PRCP", "TMAX"]
        cls.start_date = start_date
        cls.end_date = end_date

    @classmethod
    def tearDownClass(cls):
        del cls.loc_coords, cls.data_types, cls.start_date, cls.end_date

    def test_check_length(self):
        # If the number of coordinates is not equal to 2
        with self.assertRaises(ValueError):
            loc_coords = (1, 2, 3)
            DataCollection.check_length(loc_coords, self.data_types)

        # If data types were not specified (an empty collection)
        with self.assertRaises(ValueError):
            data_types = []
            DataCollection.check_length(self.loc_coords, data_types)

    def test_check_types(self):
        # If the type of parameter 'loc_coords' was not tuple
        with self.assertRaises(TypeError):
            loc_coords = [1, 1]
            DataCollection.check_types(
                loc_coords, self.data_types, self.start_date, self.end_date
            )

        # If the type of the coordinate was not float or int
        with self.assertRaises(TypeError):
            loc_coords = ("1", 1)
            DataCollection.check_types(
                loc_coords, self.data_types, self.start_date, self.end_date
            )

        # If the type of parameter 'data_types' was not list, tuple, or set
        with self.assertRaises(TypeError):
            data_types = {"PRCP": "TMAX"}
            DataCollection.check_types(
                self.loc_coords, data_types, self.start_date, self.end_date
            )

        # If the type of the data type was not str
        with self.assertRaises(TypeError):
            data_types = ["PRCP", ["TMAX"]]
            DataCollection.check_types(
                self.loc_coords, data_types, self.start_date, self.end_date
            )

        # If the type of parameter 'start_date' was not str
        with self.assertRaises(TypeError):
            start_date = 1940_01_01
            DataCollection.check_types(
                self.loc_coords, self.data_types, start_date, self.end_date
            )

        # If the type of parameter 'end_date' was not str
        with self.assertRaises(TypeError):
            end_date = 1960_01_01
            DataCollection.check_types(
                self.loc_coords, self.data_types, self.start_date, end_date
            )

    def test_check_values(self):
        # If latitude was not in the range of [-90, 90]
        with self.assertRaises(ValueError):
            loc_coords = (-100, self.loc_coords[1])
            DataCollection.check_values(
                loc_coords, self.start_date, self.end_date
            )

        # If longitude was not in the range of [-180, 180]
        with self.assertRaises(ValueError):
            loc_coords = (self.loc_coords[0], -190)
            DataCollection.check_values(
                loc_coords, self.start_date, self.end_date
            )

        # If 'end_date' was greater than today
        with self.assertRaises(ValueError):
            end_date = datetime.today() + timedelta(days=1)
            DataCollection.check_values(
                self.loc_coords, self.start_date, end_date.strftime(TIME_FORMAT)
            )

        # If 'start_date' was greater than 'end_date'
        with self.assertRaises(ValueError):
            start_date = datetime.strptime(
                self.end_date, TIME_FORMAT
            ) + timedelta(days=1)
            DataCollection.check_values(
                self.loc_coords, start_date.strftime(TIME_FORMAT), self.end_date
            )

    def check_constant_data(self):
        # If stations and cities were retrieved from the database
        self.assertGreater(len(DataCollection.get_stations()), 0)
        self.assertGreater(len(DataCollection.get_cities()), 0)


skip("")


class NOAAServiceTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.noaa_service = NOAAService(
            loc_coords=(50, 30), start_date=start_date, end_date=end_date
        )

    @classmethod
    def tearDownClass(cls):
        del cls.noaa_service

    def test_check_num_stations(self):
        # If the type of parameter 'num_nearby_stations' was not int
        with self.assertRaises(TypeError):
            num_nearby_stations = "1"
            NOAAService.check_types(
                num_nearby_stations,
                self.noaa_service.data_types,
                start_date,
                end_date,
            )

        # If the number of stations was less than 1
        with self.assertRaises(ValueError):
            num_nearby_stations = 0
            NOAAService.check_num_stations(num_nearby_stations)

    def test_get_nearest_stations(self):
        # If the number of found stations is not greater than
        # 'num_nearby_stations' or equal to it
        self.assertGreaterEqual(
            self.noaa_service.num_nearby_stations,
            len(self.noaa_service.get_nearest_stations()),
        )

    def test_get_noaa_data(self):
        # If the number of rows in NOAA data is greater than or equal to the
        # number of days between the first and last requested days
        self.assertGreaterEqual(
            len(self.noaa_service.get_noaa_data()), diff_in_days + 1
        )


skip("")


class NOAACleaningTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.noaa_service = NOAAService(
            loc_coords=(50, 30), start_date=start_date, end_date=end_date
        )
        cls.noaa_cleaning = NOAACleaning(cls.noaa_service.get_noaa_data())

    @classmethod
    def tearDownClass(cls):
        del cls.noaa_service, cls.noaa_cleaning

    def test_get_station_coords(self):
        # The nearest station will be found, guaranteed
        station_coords = self.noaa_cleaning.get_station_coords(
            self.noaa_service.get_nearest_stations()[0]
        )
        # If the coordinates of a station are tuple
        self.assertIsInstance(station_coords, tuple)
        # If the number of coordinates is equal to 2
        self.assertEqual(len(station_coords), 2)

    def test_get_combined_dataset(self):
        # If the number of rows in a combined dataset is less or equal to
        # the number of rows in NOAA data, which consists of one and more
        # datasets
        self.assertLessEqual(
            len(self.noaa_cleaning.get_combined_dataset()),
            len(self.noaa_service.get_noaa_data()),
        )

    def test_get_cleaned_data(self):
        # If the number of rows in a cleaned dataset is less or equal to
        # the number of rows in a combined dataset, which could have missing
        # rows (dates) and values
        self.assertLessEqual(
            len(self.noaa_cleaning.get_combined_dataset()),
            len(self.noaa_cleaning.get_cleaned_data()),
        )


@skip("f")
class ERA5ServiceTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.era5_service = ERA5Service(
            loc_coords=(50, 30),
            start_date=start_date,
            end_date=end_date,
            intermidiate_dists=[200, 500],
        )

    @classmethod
    def tearDownClass(cls):
        del cls.era5_service

    def test_check_intermidiate_dists(self):
        # If 'intermidiate_dists' was not list or tuple
        with self.assertRaises(TypeError):
            intermidiate_dists = {150, 200}
            ERA5Service.check_intermidiate_dists(intermidiate_dists)

        # If all values of 'intermidiate_dists' were not int
        with self.assertRaises(TypeError):
            intermidiate_dists = [150.5, 200.0]
            ERA5Service.check_intermidiate_dists(intermidiate_dists)

        # If the distance between the boundary distances is less than 50 km
        with self.assertRaises(ValueError):
            intermidiate_dists = [150, 190]
            ERA5Service.check_intermidiate_dists(intermidiate_dists)

    def test_get_station_ids_bw_dists_of_card_points(self):
        station_ids = (
            self.era5_service.get_station_ids_bw_dists_of_card_points()
        )
        # If the number of sectors m is equal to the number of the boundary
        # distances n - 1: m = n - 1
        self.assertEqual(
            len(station_ids) + 1, len(self.era5_service.intermidiate_dists)
        )

        # If a sector contains all four cardinal points
        first_sector = station_ids[list(station_ids.keys())[0]]
        self.assertEqual(len(first_sector), 4)

    def test_get_era_data(self):
        # If the number of rows in ERA5 data is equal to the difference
        # in days between the first and last requested days
        self.assertEqual(
            len(self.era5_service.get_era_data()), diff_in_days + 1
        )
