import io
from datetime import timedelta
from time import time

import pandas as pd
from django.http import HttpRequest, JsonResponse
from haversine import haversine
from rest_framework import status, viewsets

from .config.config import logger
from .ml_part.data_workflow import ERA5Service, NOAACleaning, NOAAService
from .ml_part.precip import lstm
from .ml_part.temp import sarima_and_es
from .models import City, Station
from .serializers import CitySerializer


def get_weekly_forecast(request: HttpRequest) -> JsonResponse:
    params = request.GET
    lat, lng = float(params.get("lat")), float(params.get("lng"))
    start_date = "2015-01-01"

    logger.info("=" * 10 + " DATA COLLECTION " + "=" * 10)
    # Not specify start date here because there may not be the data after this
    # date and we will get an empty dataset
    noaa_initial_df = NOAAService(
        (lat, lng),
        data_types=["TMAX", "TMIN"],
        start_date=start_date,
        num_nearby_stations=10,
    ).get_noaa_data()

    logger.info("\n" + "=" * 10 + " DATA CLEANING " + "=" * 10)
    # Since we make prediction also for today,
    # we take the data without today's day
    noaa_cleaned_df = NOAACleaning(noaa_initial_df).get_cleaned_data().iloc[:-1]

    logger.info("\n\n" + "=" * 10 + " TEMPERATURE PREDICTION " + "=" * 10)
    start_time = time()
    temp_max_fc = sarima_and_es(noaa_cleaned_df["temp_max"])
    temp_min_fc = sarima_and_es(noaa_cleaned_df["temp_min"])
    end_time = time()
    logger.info(f"Total time: {end_time - start_time}")

    logger.info("=" * 10 + " DATA COLLECTION " + "=" * 10)
    stations = pd.DataFrame(
        Station.objects.values(),
        columns=[field.name for field in Station._meta.get_fields()],
    )
    stations["coords"] = tuple(zip(stations["lat"], stations["lng"]))
    stations["dist"] = stations["coords"].map(
        lambda x: haversine([lat, lng], x)
    )
    nearest_station = stations.loc[stations["dist"].idxmin()]
    era_data_types = [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "windspeed_10m",
        "winddirection_10m_dominant",
        "pressure_msl",
        "relativehumidity_2m",
    ]
    era_df = (
        ERA5Service(
            nearest_station["coords"],
            data_types=era_data_types,
            start_date=start_date,
        )
        .get_era_data()
        .iloc[:-1]
    )

    logger.info("\n" + "=" * 10 + " PRECIPITATION " + "=" * 10)
    start_time = time()
    precip_fc = lstm(era_df)
    end_time = time()
    logger.info(f"Total time: {end_time - start_time}")

    forecast = {
        "max_temperature": temp_max_fc,
        "min_temperature": temp_min_fc,
        "calendar_date": pd.date_range(
            start=noaa_cleaned_df.index[-1] + timedelta(days=1),
            end=noaa_cleaned_df.index[-1] + timedelta(days=7),
            freq="D",
        )
        .strftime("%a %d")
        .to_list(),
        "precipitation": precip_fc,
    }
    return JsonResponse(forecast)


def check_city(request: HttpRequest) -> JsonResponse:
    params = request.GET
    data = {"status": 0, "message": ""}

    city = params.get("city", None)
    if city is not None:
        flag = False
        if "," in city:
            city, country = [s.strip() for s in city.split(",")]
            found_cities = City.objects.filter(
                name__iexact=city, country__iexact=country
            )
            if len(found_cities):
                flag = True

        if not flag:
            found_cities = City.objects.filter(name__iexact=city)

        found_cities = list(found_cities.values())
        if len(found_cities) == 0:
            data["status"] = status.HTTP_404_NOT_FOUND.numerator
            data["message"] = (
                f"{city} city was not found. "
                + "Perhaps there is no such city in the database."
            )
        elif len(found_cities) > 1:
            data["status"] = status.HTTP_202_ACCEPTED.numerator
            data[
                "message"
            ] = f"Choose the point number for {city} from the proposed list:"
            data["cityData"] = found_cities
        else:
            data["status"] = status.HTTP_200_OK.numerator
            data["cityData"] = found_cities[0]

    else:
        lat, lng = float(params.get("lat")), float(params.get("lng"))
        cities = pd.DataFrame(
            City.objects.values(),
            columns=[field.name for field in City._meta.get_fields()],
        )
        cities["coords"] = tuple(zip(cities["lat"], cities["lng"]))
        cities["dist"] = cities["coords"].map(
            lambda x: haversine([lat, lng], x)
        )
        nearest_city = cities.loc[cities["dist"].idxmin()]

        data["status"] = status.HTTP_200_OK.numerator
        city_data = {
            "name": nearest_city["name"],
            "country": nearest_city["country"],
            "distance": nearest_city["dist"],
        }
        if nearest_city["dist"] < 10:
            data["message"] = (
                "The city by coordinates: '{name}' in {county}"
            ).format_map(city_data)
        else:
            data["message"] = (
                "The nearest {name} city in {country} is located "
                + "{distance:.1f}км from the specified coordinates. Continue?"
            ).format_map(city_data)
        data["cityData"] = CitySerializer(
            City.objects.get(id=cities["dist"].idxmin())
        ).data

    return JsonResponse(data, status=status.HTTP_200_OK)
