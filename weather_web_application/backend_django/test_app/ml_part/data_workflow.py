import io
import time
import warnings
from datetime import date, datetime, timedelta
from typing import Union

import numpy as np
import pandas as pd
import requests
from haversine import haversine

from ..models import City, Station


class DataCollection:
    """
    A base class for verification of parameters and storage of shared data

    """

    TIME_FORMAT = "%Y-%m-%d"

    # Constraints for coordinates
    NUM_COORDS = 2
    MIN_LAT, MAX_LAT = (-90, 90)
    MIN_LNG, MAX_LNG = (-180, 180)

    def __init__(self, loc_coords, data_types, start_date, end_date) -> None:
        self.check_length(loc_coords, data_types)
        self.check_types(loc_coords, data_types, start_date, end_date)
        self.check_values(loc_coords, start_date, end_date)

        self.loc_coords = loc_coords
        # We delete duplicates and convert the collection back to its
        # initial type.
        self.data_types = type(data_types)(s for s in set(data_types))
        self.start_date = start_date
        self.end_date = end_date

    @classmethod
    def check_length(cls, loc_coords, data_types):
        if len(loc_coords) != cls.NUM_COORDS:
            raise ValueError(
                "Location coordinates consist of two parameters: "
                "(latitude, longitude)"
            )
        if not len(data_types):
            raise ValueError("'data_types' argument cannot be empty.")

    @classmethod
    def check_types(cls, loc_coords, data_types, start_date, end_date):
        if not type(loc_coords) is tuple:
            raise TypeError(
                "'loc_coords' type must be tuple"
                f"but got type {type(loc_coords).__name__}"
            )
        if not all(isinstance(i, (float, int)) for i in loc_coords):
            raise TypeError("The type of the coordinate must be float or int")

        if not isinstance(data_types, (list, tuple, set)):
            raise TypeError(
                "'data_types' type must be list, tuple, or set "
                f"but got type {type(data_types).__name__}."
            )
        if not all(type(s) is str for s in data_types):
            raise TypeError("The type of the data type must be str")

        if not type(start_date) is str:
            raise TypeError(
                "'start_date' type must be str"
                f"but got type {type(start_date).__name__}."
            )
        if not type(end_date) is str:
            raise TypeError(
                "'end_date' type must be str"
                f"but got type {type(end_date).__name__}."
            )

    @classmethod
    def check_values(cls, loc_coords, start_date, end_date):
        lat, lng = loc_coords
        if not cls.MIN_LAT <= lat <= cls.MAX_LAT:
            raise ValueError(
                "Latitude (the first value in 'loc_coords') must be"
                f"in the range of [{cls.MIN_LAT}, {cls.MAX_LAT}]"
            )
        if not cls.MIN_LNG <= lng <= cls.MAX_LNG:
            raise ValueError(
                "Longitude (the second value in 'loc_coords') must be"
                f"in the range of [{cls.MIN_LNG}, {cls.MAX_LNG}]"
            )

        start_date = datetime.strptime(start_date, cls.TIME_FORMAT)
        end_date = datetime.strptime(end_date, cls.TIME_FORMAT)
        today = datetime.today()
        if end_date > today:
            raise ValueError("'end_date' must be less or equal to 'today'.")
        if start_date > end_date:
            raise ValueError(
                "'start_date' must be less or equal to 'end_date'."
            )

    @staticmethod
    def show_available_data_types():
        raise NotImplementedError(
            "This method must be overridden in child classes"
        )

    @staticmethod
    def get_stations():
        return pd.DataFrame(
            Station.objects.values(),
            columns=[field.name for field in Station._meta.get_fields()],
        )

    @staticmethod
    def get_cities():
        return pd.DataFrame(
            City.objects.values(),
            columns=[field.name for field in City._meta.get_fields()],
        )


class NOAAService(DataCollection):
    """
    Obtaning daily weather data from NOAA NCEI.

    ...

    Parameters
    ----------
    loc_coords : tuple[float | int, float | int]
        Coordinates of location: [latitude, longitude].
    data_types : list[str] | tuple[str] | set[str], \
        default=['PRCP', 'TMAX','TMIN']
        The fields to return from the dataset. It consists of a comma-delimited
        list of field names. Read to [1] know more.
    start_date : str, default='01-01-01'
        The first date of the data to retrieve in format 'year-month-day'.
    end_date : str, default='today'
        The last date of the data to retrieve.
    num_nearby_stations : int, default=3
        The number of stations that are located within 150 km of the specified location is used to fill in missing values in data of the nearest station.

    Attributes
    ----------
    station_ids_ : list
        Identifiers of the nearest stations.

    References
    ----------
        [1]  https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt - README
    FILE FOR DAILY GLOBAL HISTORICAL CLIMATOLOGY NETWORK.

    Methods
    -------
    show_available_data_types -> None:
        Showing the data types that the class accepts. Wrong data types will
        be ignored.
    get_nearest_stations -> list[str]:
        Getting the nearest stations to the coordinates.
    get_noaa_data -> DataFrame | str:
        Getting the dataset that consists of data from the nearest
        stations.
    """

    BASE_API_URL = "https://www.ncei.noaa.gov/access/services/data/v1/?"

    MIN_NUM_STATIONS = 1
    DATA_TYPES = {"pandas", "text"}

    stations = DataCollection.get_stations()
    cities = DataCollection.get_cities()

    def __init__(
        self,
        loc_coords: Union[tuple[float, float], tuple[int, int]],
        data_types: Union[list[str], tuple[str], set[str]] = [
            "PRCP",
            "TMAX",
            "TMIN",
        ],
        start_date: str = date.min.strftime("%Y-%m-%d"),
        end_date: str = datetime.today().strftime("%Y-%m-%d"),
        num_nearby_stations: int = 3,
    ):
        super(NOAAService, self).__init__(
            loc_coords, data_types, start_date, end_date
        )

        self.check_num_stations(num_nearby_stations)
        self.num_nearby_stations = num_nearby_stations

    @classmethod
    def check_num_stations(cls, num_nearby_stations):
        if not type(num_nearby_stations) is int:
            raise TypeError(
                "'num_nearby_stations' type must be int "
                f"but got type {type(num_nearby_stations).__name__}"
            )
        if not num_nearby_stations >= cls.MIN_NUM_STATIONS:
            raise ValueError("The number of stations must be greater than zero")

    @staticmethod
    def show_available_data_types():
        data_types = {
            "TMAX": "Maximum temperature",
            "TMIN": "Minimum temperature",
            "PRCP": "Precipitation",
            "RHAV": "Average relative humidity",
            "ASTP": "Average Station Level Pressure",
            "ACSC": (
                "Average cloudiness sunrise to sunset from 30-second"
                "ceilometer data (percent)"
            ),
            "AWDR": "Average daily wind direction (degrees)",
            "AWND": "Average daily wind speed (tenths of meters per second)",
        }
        print(data_types)

    def _call_api(self, station_ids: list) -> Union[str, pd.DataFrame]:
        """Obtaining NOAA data"""
        stations = ",".join(station_ids)
        full_url = (
            f"{self.BASE_API_URL}dataset=daily-summaries&dataTypes="
            f"{','.join(self.data_types)}&stations={stations}"
            f"&startDate={self.start_date}&endDate={self.end_date}"
            "&boundingBox=90,-180,-90,180&units=metric"
        )
        response = requests.get(full_url)
        if response.status_code != 200:
            response.raise_for_status()
        return response.text

    def get_nearest_stations(self) -> list[str]:
        stations_locs = pd.DataFrame(
            {
                "Id": self.stations["name"],
                "Coords": tuple(
                    zip(self.stations["lat"], self.stations["lng"])
                ),
            }
        )
        cities_locs = pd.DataFrame(
            {
                "City": self.cities["name"],
                "Coords": tuple(zip(self.cities["lat"], self.cities["lng"])),
            }
        )

        station_ids = []
        for i in range(self.num_nearby_stations):
            stations_locs["Dist"] = stations_locs["Coords"].map(
                lambda x: haversine(self.loc_coords, x)
            )
            cities_locs["Dist"] = cities_locs["Coords"].map(
                lambda x: haversine(self.loc_coords, x)
            )

            station_ind = stations_locs["Dist"].idxmin()
            station = stations_locs.loc[station_ind]
            city = cities_locs.loc[cities_locs["Dist"].idxmin()]

            if i > 0 and station["Dist"] >= 150:
                print(
                    f"{i} stations were only used. The rest are located > 150km"
                )
                break

            if i == 0:
                print(
                    "The nearest city is {city} -> {dist} km".format_map(
                        {
                            "city": city["City"],
                            "dist": round(city["Dist"], 3),
                        }
                    )
                )
                print("*" * 10 + " Stations " + "*" * 10)

            print(
                "{counter}. {id} -> {dist} km".format_map(
                    {
                        "counter": i + 1,
                        "id": station["Id"],
                        "dist": round(station["Dist"], 3),
                    }
                )
            )

            station_ids.append(station["Id"])
            stations_locs.drop(station_ind, inplace=True)

        self.station_ids_ = station_ids
        return station_ids

    def get_noaa_data(
        self, transform: str = "pandas"
    ) -> Union[pd.DataFrame, str]:
        if not isinstance(transform, str):
            raise ValueError(
                "'transform' type must be str"
                f"but got type {type(transform).__name__}."
            )
        if transform not in self.DATA_TYPES:
            raise ValueError(
                "Parameter 'transform' may accept the following values: "
                f"{self.DATA_TYPES}"
            )

        self.station_ids_ = self.get_nearest_stations()
        station_datasets = self._call_api(self.station_ids_)

        station_datasets_ = pd.read_csv(io.StringIO(station_datasets))
        stations_without_data = set(self.station_ids_) - set(
            station_datasets_["STATION"].unique()
        )
        if len(stations_without_data) > 0:
            print(
                f"\nStation(-s) {stations_without_data}\n",
                "do(-es) not have the data for this date range."
            )
            """
            if (len(stations_without_data) ==
                station_datasets_['STATION'].nunique()):
                print(
                    "As the dataset will be empty because all stations",
                    "found do not have data for this date range, we will",
                    "continue the search for the other nearest stations"
                )
                station_idx = [
                    self.stations[self.stations['name'] == station_id]
                    for station_id in nearest_stations
                ]
                self.stations = self.stations.drop(station_idx)
                return self.get_noaa_data()
            """

        return station_datasets if transform == "text" else station_datasets_


class NOAACleaning:
    """
    Filling missing values in NOAA weather data with ERA5 data since 1940

    ...

    Parameters
    ----------
    station_datasets : DataFrame
        Datasets from the nearest stations.

    Attributes
    ----------
    first_station_coords_ : tuple[float, float]
        Coordinates of the nearest station.
    combined_dataset_ : DataFrame
        One combined dataset is based on data from the nearest station, whose missing values are filled by data from the others.
    era_data_ : DataFrame
        The ERA5 data that was loaded to fill the last gaps in the data.

    Methods
    -------
    get_station_coords -> tuple[float, float]:
        Getting station coordinates using a station identifier.
    get_combined_dataset -> DataFrame:
        Filling missing values in the data of the nearest station with the data
        from other nearby stations in order depending on distance.
    get_cleaned_data -> DataFrame:
        Execution of all operations to get a dataset without missing values.
    """

    TIME_FORMAT = DataCollection.TIME_FORMAT

    MIN_DATE = datetime.strptime("1940-01-01", TIME_FORMAT)

    stations = DataCollection.get_stations()
    renamed_types = {
        "PRCP": "precip_sum",
        "TMAX": "temp_max",
        "TMIN": "temp_min",
        "RHAV": "relat_humidity",
        "ASTP": "pressure_level",
        "ACSC": "cloud_cover",
        "AWDR": "wind_direction",
        "AWND": "wind_speed",
    }

    def __init__(self, station_datasets: pd.DataFrame):
        self.station_datasets = station_datasets

    @classmethod
    def get_station_coords(cls, station_id: str) -> tuple[float, float]:
        lat, lng = np.ravel(
            cls.stations.loc[
                cls.stations["name"] == station_id, ["lat", "lng"]
            ].values
        )
        return (lat, lng)

    def get_combined_dataset(self) -> pd.DataFrame:
        df = self.station_datasets.copy()
        df["date"] = pd.to_datetime(df["DATE"])
        df = df.set_index("date").drop("DATE", axis=1)

        replace_column_names = {
            col: self.renamed_types[col]
            for col in self.station_datasets
            if col in self.renamed_types.keys()
        }
        df.rename(columns=replace_column_names, inplace=True)

        # At first if there are the data from several stations, we will fill
        # missing values taken the nearest one as the main. The next stations
        # will be used to fill in the nearest one in order.
        num_stations = df["STATION"].nunique()
        all_needed_dates = pd.date_range(df.index[0], df.index[-1], freq="D")
        if num_stations > 1:
            station_names = list(df["STATION"].unique())
            print(f"The nearest station is '{station_names[0]}'")
            nearest_station_data = df[df["STATION"] == station_names.pop(0)]
            df_comb = nearest_station_data.copy()
            print("Total missing values:", df_comb.isna().sum().sum())
            print(
                "Total missing days: {}".format(
                    len(set(all_needed_dates) - set(df_comb.index))
                )
            )
            print(
                "Filling them using the other stations: {}".format(
                    ", ".join(station_names)
                ),
                end="\n\n",
            )
            while df_comb.isna().values.any() and station_names:
                station_name = station_names.pop(0)
                next_station_data = df[df["STATION"] == station_name]

                # Filling missing values in the same location
                df_comb = df_comb.combine_first(
                    # We have to have the same dataframes by shapes
                    next_station_data.loc[
                        list(set(next_station_data.index) & set(df_comb.index))
                    ]
                )

                # If there are missing dates from the start date to the last.
                # The last rest of the dates are filled with ERA5 data.
                missing_inds = missing_inds = list(
                    set(next_station_data.index) - set(df_comb.index)
                )
                if missing_inds:
                    df_comb = pd.concat(
                        [df_comb, next_station_data.loc[missing_inds]]
                    ).sort_index()

                print(f"Station '{station_name}'")
                print(
                    "Left missing values -> {num_mis_vals}".format(
                        num_mis_vals=df_comb.isna().sum().sum()
                    )
                )
                print(
                    "Left missing days -> {left_dates}".format(
                        left_dates=len(
                            set(all_needed_dates) - set(df_comb.index)
                        )
                    ),
                    end="\n\n",
                )

            df = df_comb

        print(
            "There were left {} missing values and {} missing days".format(
                df.isna().sum().sum(),
                len(set(all_needed_dates) - set(df.index)),
            ),
            end=". \nNow they will be filled data from ERA5 dataset",
        )
        return df.drop("STATION", axis=1)

    def get_cleaned_data(self):
        self.first_station_coords_ = self.get_station_coords(
            self.station_datasets.loc[1, "STATION"]
        )
        self.combined_dataset_ = self.get_combined_dataset()
        era_data_types = ERA5Service.daily_types | ERA5Service.hourly_types
        data_types = [
            era_data_types[col] for col in self.combined_dataset_.columns
        ]
        self.era_data_ = ERA5Service(
            self.first_station_coords_,
            data_types,
            self.combined_dataset_.index[0].strftime(self.TIME_FORMAT),
            self.combined_dataset_.index[-1].strftime(self.TIME_FORMAT),
        ).get_era_data()

        # Then we will fill the rest of missing values and dates in station
        # data using ERA5 data
        missing_inds = list(
            set(self.era_data_.index) - set(self.combined_dataset_.index)
        )
        data = pd.concat(
            [self.combined_dataset_, self.era_data_.loc[missing_inds]]
        ).sort_index()
        if not data.index.is_unique:  # In any case
            data = data[~data.index.duplicated(keep="first")]

        return data.combine_first(self.era_data_)


class ERA5Service(DataCollection):
    """
    Loading the ERA5 data for one or several station coordinates for each cardinal point since 1940

    ...

    Parameters
    ----------
    loc_coords : tuple
        Coordinates of the nearest station.
    data_types : list[str] | tuple[str] | set[str]], default=[
                "temperature_2m_max", "temperature_2m_min", "precipitation_sum"
            ]
        The fields to return from the dataset. It consists of a comma-delimited
        list of field names. Read [1] to know more.
    start_date : str, default='2000-01-01'
        The date from which we are going to load the data.
    intermidiate_dists : list[int], default=[]
        The boundary distances (km) that determine the borders of sectors
        where neighbouring stations will be searched. For example:
        [100, 500, 1000]. Enter at least two values to start searching neighbouring stations between the distances and adding the data from them to the output dataset.

    References
    ----------
        [1]  https://open-meteo.com/en/docs/historical-weather-api - Historical
    Weather API.

    Attributes
    ----------
    station_dataset_ : DataFrame
        The dataset that was obtained by the coordinates of the nearest (initial) station.

    station_ids_ : dict[dict[str]]
        Identifiers of the neighbouring stations that were found within the boundary distances.

    Methods
    -------
    show_available_data_types -> None:
        Showing the data types that the class accepts. Wrong data types will
        be ignored.
    get_station_names_bw_dists_of_cardinal_points -> dict[dict[str]]:
        Getting station names within each sector.
    get_era_data -> DataFrame:
        Getting ERA5 data of the initial and neighbouring stations.
    """

    daily_types = {
        "temp_max": "temperature_2m_max",
        "temp_min": "temperature_2m_min",
        "precip_sum": "precipitation_sum",
        "wind_direction": "winddirection_10m_dominant",
    }
    hourly_types = {
        "pressure_level": "pressure_msl",
        "relat_humidity": "relativehumidity_2m",
        "cloud_cover": "cloudcover",
        "wind_speed": "windspeed_10m",
    }
    era_data_types = daily_types | hourly_types

    stations = DataCollection.get_stations()

    def __init__(
        self,
        loc_coords: tuple([float, float]),
        data_types: Union[list[str], tuple[str], set[str]] = [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
        ],
        start_date: str = "1940-01-01",
        end_date: str = datetime.today().strftime("%Y-%m-%d"),
        intermidiate_dists: Union[list[int], tuple[int]] = [],
    ):
        super(ERA5Service, self).__init__(
            loc_coords, data_types, start_date, end_date
        )

        self.check_intermidiate_dists(intermidiate_dists)
        self.intermidiate_dists = intermidiate_dists

    @classmethod
    def check_intermidiate_dists(cls, intermidiate_dists):
        if not isinstance(intermidiate_dists, (list, tuple)):
            raise TypeError(
                "'intermidiate_dists' type must be list or tuple "
                f"but got type {type(intermidiate_dists).__name__}"
            )
        if not all(isinstance(i, int) for i in intermidiate_dists):
            raise TypeError("The type of the boundary distance must be int")
        if not all(
            intermidiate_dists[i] + 50 <= intermidiate_dists[i + 1]
            for i in range(len(intermidiate_dists) - 1)
        ):
            raise ValueError(
                "The distance between boundary distances",
                "must be not less than 50 km",
            )

    @classmethod
    def show_era_data_types(cls):
        renamed_types = NOAACleaning.renamed_types
        print("Initial- and ERA5 data types into renamed data type")
        for init_data_type, renamed_type in renamed_types.items():
            print(
                f"{init_data_type} and {cls.era_data_types[renamed_type]} "
                f"are renamed to '{renamed_type}'"
            )

    @staticmethod
    def show_available_data_types():
        ERA5Service.show_era_data_types()

    def get_era_data(self) -> pd.DataFrame:
        self.station_dataset_ = self._call_api()
        if len(self.intermidiate_dists) >= 2:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                warnings.warn(
                    "default", category=pd.errors.SettingWithCopyWarning
                )
                station_ids = self.get_station_ids_bw_dists_of_card_points()
                self.station_ids_ = station_ids
            return self._combine_station_datasets(
                self.station_dataset_, self.station_ids_
            )
        return self.station_dataset_

    def _combine_station_datasets(
        self, station_dataset: pd.DataFrame, station_ids: dict
    ) -> pd.DataFrame:
        """Combining datasets into one dataset via adding their columns."""
        combined_dataset = station_dataset.copy()
        for sector in station_ids.keys():
            for side, station_id in station_ids[sector].items():
                try:
                    station_coords = self.stations.loc[
                        self.stations["name"] == station_id, ["lat", "lng"]
                    ].values[0]
                    time.sleep(0.2)
                    station_era_data = self._call_api(station_coords)
                    station_era_data = station_era_data.rename(
                        columns={
                            old_col: sector[:-2] + "_" + side + "_" + old_col
                            for old_col in station_era_data.columns
                        }
                    )
                    combined_dataset = combined_dataset.merge(
                        station_era_data, on="date"
                    )
                except IndexError:
                    print(f"There was no found a station from {side} side.")

        return combined_dataset

    def get_station_ids_bw_dists_of_card_points(self, degree_step=1e-3) -> dict:
        lat, long = self.loc_coords
        dists = sorted(self.intermidiate_dists)

        def calc_coords(lat, long, min_dist):
            north_lat, south_lat = lat, lat
            while haversine([lat, long], [int(north_lat), long]) < min_dist:
                if north_lat >= 90 - degree_step:
                    break
                north_lat += degree_step
            while haversine([lat, long], [int(south_lat), long]) < min_dist:
                if south_lat <= -(90 - degree_step):
                    break
                south_lat -= degree_step

            west_long, east_long = long, long
            while haversine([lat, long], [lat, int(west_long)]) < min_dist:
                if west_long <= -(180 - degree_step):
                    break
                west_long -= degree_step
            while haversine([lat, long], [lat, int(east_long)]) < min_dist:
                if east_long >= 180 - degree_step:
                    break
                east_long += degree_step

            return (north_lat, south_lat, west_long, east_long)

        extreme_points = {}
        for dist in dists:
            extreme_points[dist] = calc_coords(
                # int() because of 90.000000000043
                int(lat),
                int(long),
                min_dist=dist,
            )

        stations_locs = self.stations.copy().rename(
            columns={"name": "Id", "lat": "Latitude", "lng": "Longitude"}
        )
        stations_locs["Coords"] = tuple(
            zip(stations_locs["Latitude"], stations_locs["Longitude"])
        )

        dist_station = {}
        card_points = {"north": 0, "south": 1, "west": 2, "east": 3}
        for i in range(len(dists) - 1):
            start_dist, end_dist = dists[i], dists[i + 1]
            station_ids = {
                card_point: None for card_point in card_points.keys()
            }

            # WEST
            near_west_long = extreme_points[start_dist][card_points["west"]]
            far_west_long = extreme_points[end_dist][card_points["west"]]
            far_north_lat = extreme_points[end_dist][card_points["north"]]
            far_south_lat = extreme_points[end_dist][card_points["south"]]
            west_sector = stations_locs[
                (stations_locs["Longitude"] < near_west_long)
                & (stations_locs["Longitude"] > far_west_long)
                & (stations_locs["Latitude"] < far_north_lat)
                & (stations_locs["Latitude"] > far_south_lat)
            ].copy()
            if len(west_sector) > 0:
                mean_long = (near_west_long + far_west_long) / 2
                mean_lat = (far_north_lat + far_south_lat) / 2
                central_west = (mean_lat, mean_long)
                west_sector["Dist"] = west_sector["Coords"].map(
                    lambda stat_coords: haversine(central_west, stat_coords)
                )
                station_ind = west_sector["Dist"].idxmin()
                station_id = west_sector.loc[station_ind]["Id"]
                while station_id in station_ids.values():
                    west_sector.drop(station_ind, inplace=True)
                    station_ind = west_sector["Dist"].idxmin()
                    station_id = west_sector.loc[station_ind]["Id"]
                station_ids["west"] = station_id

            # EAST
            near_east_long = extreme_points[start_dist][card_points["east"]]
            far_east_long = extreme_points[end_dist][card_points["east"]]
            far_north_lat = extreme_points[end_dist][card_points["north"]]
            far_south_lat = extreme_points[end_dist][card_points["south"]]
            east_sector = stations_locs[
                (stations_locs["Longitude"] > near_east_long)
                & (stations_locs["Longitude"] < far_east_long)
                & (stations_locs["Latitude"] < far_north_lat)
                & (stations_locs["Latitude"] > far_south_lat)
            ].copy()
            if len(east_sector) > 0:
                mean_long = (near_east_long + far_east_long) / 2
                mean_lat = (far_north_lat + far_south_lat) / 2
                central_east = (mean_lat, mean_long)
                east_sector["Dist"] = east_sector["Coords"].map(
                    lambda stat_coords: haversine(central_east, stat_coords)
                )
                station_ind = east_sector["Dist"].idxmin()
                station_id = east_sector.loc[station_ind]["Id"]
                while station_id in station_ids.values():
                    east_sector.drop(station_ind, inplace=True)
                    station_ind = east_sector["Dist"].idxmin()
                    station_id = east_sector.loc[station_ind]["Id"]
                station_ids["east"] = station_id

            # NORTH
            near_north_lat = extreme_points[start_dist][card_points["north"]]
            far_north_lat = extreme_points[end_dist][card_points["north"]]
            far_west_long = extreme_points[end_dist][card_points["west"]]
            far_east_long = extreme_points[end_dist][card_points["east"]]
            north_sector = stations_locs[
                (stations_locs["Longitude"] > far_west_long)
                & (stations_locs["Longitude"] < far_east_long)
                & (stations_locs["Latitude"] < far_north_lat)
                & (stations_locs["Latitude"] > near_north_lat)
            ].copy()
            if len(north_sector) > 0:
                mean_long = (near_east_long + far_east_long) / 2
                mean_lat = (far_north_lat + near_north_lat) / 2
                central_north = (mean_lat, mean_long)
                north_sector["Dist"] = north_sector["Coords"].map(
                    lambda stat_coords: haversine(central_north, stat_coords)
                )
                station_ind = north_sector["Dist"].idxmin()
                station_id = north_sector.loc[station_ind]["Id"]
                while station_id in station_ids.values():
                    north_sector.drop(station_ind, inplace=True)
                    station_ind = north_sector["Dist"].idxmin()
                    station_id = north_sector.loc[station_ind]["Id"]
                station_ids["north"] = station_id

            # SOUTH
            near_south_lat = extreme_points[start_dist][card_points["south"]]
            far_south_lat = extreme_points[end_dist][card_points["south"]]
            far_west_long = extreme_points[end_dist][card_points["west"]]
            far_east_long = extreme_points[end_dist][card_points["east"]]
            south_sector = stations_locs[
                (stations_locs["Longitude"] > far_west_long)
                & (stations_locs["Longitude"] < far_east_long)
                & (stations_locs["Latitude"] > far_south_lat)
                & (stations_locs["Latitude"] < near_south_lat)
            ].copy()
            if len(south_sector) > 0:
                mean_long = (near_east_long + far_east_long) / 2
                mean_lat = (far_south_lat + near_south_lat) / 2
                central_south = (mean_lat, mean_long)
                south_sector["Dist"] = south_sector["Coords"].map(
                    lambda stat_coords: haversine(central_south, stat_coords)
                )
                station_ind = south_sector["Dist"].idxmin()
                station_id = south_sector.loc[station_ind]["Id"]
                while station_id in station_ids.values():
                    south_sector.drop(station_ind, inplace=True)
                    station_ind = south_sector["Dist"].idxmin()
                    station_id = south_sector.loc[station_ind]["Id"]
                station_ids["south"] = station_id

            dist_station[f"{start_dist}-{end_dist}km"] = station_ids

        return dist_station

    def _call_api(self, loc_coords: tuple([float, float])):
        """Obtaining ERA5 data"""

        lat, lng = loc_coords
        era_data = pd.DataFrame(
            {"date": pd.date_range(self.start_date, self.end_date)}
        )

        # We request historical or forecasted ERA5 data
        def execute_request(
            url: str, data_types: list[str], dataset_type: str
        ) -> pd.DataFrame:
            response = requests.get(url)
            if response.status_code != 200:
                response.raise_for_status()
            result = response.json()

            def collect_data(
                dataset_type: str, time_types: dict
            ) -> pd.DataFrame:
                data = {}
                for data_type in data_types:
                    for key, val in time_types.items():
                        if val == data_type:
                            data[key] = result[dataset_type][data_type]
                            break
                data["date"] = pd.to_datetime(result[dataset_type]["time"])
                return pd.DataFrame(data)

            if dataset_type == "daily":
                daily_data = collect_data(dataset_type, self.daily_types)
                return daily_data

            elif dataset_type == "hourly":
                hourly_data = collect_data(dataset_type, self.hourly_types)
                hourly_data = hourly_data.resample("D", on="date").mean()
                return hourly_data.round().reset_index()

        def obtain_data(dataset_type, data_types):
            url_history = (
                f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&"
                f"longitude={lng}&start_date={self.start_date}&end_date="
                f"{self.end_date}&{dataset_type}={','.join(data_types)}&"
                "timezone=auto"
            )
            historical_data = execute_request(
                url_history, data_types, dataset_type
            )
            # There is a delay of several days in the data, so we remove
            # unknown data for recenst days
            last_idx = historical_data.drop("date", axis=1).last_valid_index()
            historical_data = historical_data.loc[:last_idx]
            # We will use the weather forecast from the same data source to
            # fill in the gaps created by the delay of several days
            last_date = historical_data["date"].iloc[-1]
            if last_date == datetime.strptime(self.end_date, self.TIME_FORMAT):
                return historical_data
            else:
                start_date_fc = str(
                    (
                        datetime.strptime(
                            last_date.strftime(self.TIME_FORMAT),
                            self.TIME_FORMAT,
                        )
                        + timedelta(days=1)
                    ).strftime(self.TIME_FORMAT)
                )
                url_fc = (
                    "https://api.open-meteo.com/v1/forecast?"
                    f"latitude={lat}&longitude={lng}&"
                    f'{dataset_type}={",".join(data_types)}&windspeed_unit=ms&'
                    f"start_date={start_date_fc}&end_date={self.end_date}"
                    "&timezone=auto"
                )
                forecasted_data = execute_request(
                    url_fc, data_types, dataset_type
                )
                return pd.concat([historical_data, forecasted_data])

        daily_types = list(
            set(self.daily_types.values()) & set(self.data_types)
        )
        hourly_types = list(
            set(self.hourly_types.values()) & set(self.data_types)
        )

        if len(daily_types) > 0:
            daily_data = obtain_data("daily", daily_types)
            era_data = era_data.merge(daily_data, on="date")
        if len(hourly_types) > 0:
            hourly_data = obtain_data("hourly", hourly_types)
            era_data = era_data.merge(hourly_data, on="date")

        # There can be missing values on January 1, 1940, so we fill them in
        era_data = era_data.set_index("date").interpolate(
            method="linear", limit_direction="backward"
        )
        # Some weather parameters are expressed in integer digits
        non_int_cols = {"precip_sum", "temp_min", "temp_max"}
        int_cols = list(set(era_data.columns) - non_int_cols)
        era_data[int_cols] = era_data[int_cols].astype(int)
        return era_data
