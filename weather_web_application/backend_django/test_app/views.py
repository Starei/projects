from rest_framework import viewsets, status
from .models import *
from .serializers import *
from django.http import HttpRequest, JsonResponse

import io
from time import time
from datetime import timedelta
import pandas as pd
from haversine import haversine

from .ml_part.data_workflow import DataCollection, DataCleaning, LatestData
from .ml_part.temp import sarima_and_es
from .ml_part.precip import lstm


class CityViewSet(viewsets.ModelViewSet):
    serializer_class = CitySerializer
    queryset = City.objects.all()


class CurrentWeatherViewSet(viewsets.ModelViewSet):
    serializer_class = CurrentWeatherSerializer
    queryset = CurrentWeather.objects.all()


def get_weekly_forecast(request: HttpRequest):
    params = request.GET
    lat, lng = float(params.get('lat')), float(params.get('lng'))
    start_date = '2015-01-01'

    print('='*10 + ' DATA COLLECTION ' + '='*10)
    # Not specify start date here because there may not be the data after this
    # date and we will get an empty dataset
    city_station_dataset = pd.read_csv(io.StringIO(DataCollection(
        (lat, lng), data_types='TMAX,TMIN', num_stations=10
    )._dataset)) 

    print('\n' + '='*10 + ' DATA CLEANING ' + '='*10)
    city_cleaned_df = DataCleaning(
        city_station_dataset, start_date=start_date, cols=['TMAX', 'TMIN']
    ).get_cleaned_data().iloc[:-1] # without today's day

    print('\n\n' +'='*10 + ' TEMPERATURE PREDICTION ' + '='*10)
    start_time = time()
    temp_max_fc = sarima_and_es(city_cleaned_df['temp_max'])
    temp_min_fc = sarima_and_es(city_cleaned_df['temp_min'])
    end_time = time()
    print(f"Total time: {end_time - start_time}")

    print('='*10 + ' DATA COLLECTION ' + '='*10)
    stations = pd.DataFrame(
        Station.objects.values(), 
        columns=[field.name for field in Station._meta.get_fields()]
    )
    stations['coords'] = tuple(zip(stations['lat'], stations['lng']))
    stations['dist'] = stations['coords'].map(
        lambda x: haversine([lat, lng], x)
    )
    nearest_station = stations.loc[stations['dist'].idxmin()]
    data_types = [
        'temperature_2m_max', 'temperature_2m_min', 'precipitation_sum',
        'windspeed_10m_max', 'windgusts_10m_max', 'winddirection_10m_dominant',
        'pressure_msl', 'relativehumidity_2m'
    ]
    combined_dataset = LatestData(
        nearest_station['coords'], data_types
    ).combined_dataset.iloc[:-1]

    print('\n' + '='*10 + ' PRECIPITATION ' + '='*10)
    start_time = time()
    precip_fc = lstm(combined_dataset)
    end_time = time()
    print(f"Total time: {end_time - start_time}")

    forecast = {
        'max_temperature': temp_max_fc,
        'min_temperature': temp_min_fc,
        'calendar_date': pd.date_range(
            start=city_cleaned_df.index[-1] + timedelta(days=1),
            end=city_cleaned_df.index[-1] + timedelta(days=7),
            freq='D'
        ).strftime('%a %d').to_list(),
        'precipitation': precip_fc
    }
    return JsonResponse(forecast)


def check_city(request: HttpRequest):
    params = request.GET
    data = {'status': 0, 'message': ''}

    city = params.get('city', None)
    if city is not None:
        flag = False
        if ',' in city:
            city, country = [s.strip() for s in city.split(',')]  
            found_cities = City.objects.filter(
                name__iexact=city, country__iexact=country
            )
            if len(found_cities): flag = True

        if not flag:
            found_cities = City.objects.filter(name__iexact=city)

        found_cities = list(found_cities.values())     
        if len(found_cities) == 0:
            data['status'] = status.HTTP_404_NOT_FOUND.numerator,
            data['message'] = (
                f"Город '{city}' не найден. " + 
                "Возможно, такого города нет в базе."
            )
        elif len(found_cities) > 1:
            data['status'] = status.HTTP_202_ACCEPTED.numerator
            data['message'] = (
                f"Выберите номер локации города '{city}' из предложенных:" 
            )
            data['cityData'] = found_cities
        else:
            data['status'] = status.HTTP_200_OK.numerator
            data['cityData'] = found_cities[0]

    else:
        lat, lng = float(params.get('lat')), float(params.get('lng')) 
        cities = pd.DataFrame(
            City.objects.values(), 
            columns=[field.name for field in City._meta.get_fields()]
        )
        cities['coords'] = tuple(zip(cities['lat'], cities['lng']))
        cities['dist'] = cities['coords'].map(
            lambda x: haversine([lat, lng], x)
        )
        nearest_city = cities.loc[cities['dist'].idxmin()]
        
        data['status'] = status.HTTP_200_OK.numerator
        city_data = {
            'name': nearest_city['name'], 
            'country': nearest_city['country'],
            'distance': nearest_city['dist']
        }
        if nearest_city['dist'] < 10:
            data['message'] = (
                "Город по координатам: '{name}' из {county}"
            ).format_map(city_data)
        else:
            data['message'] = (
                "Ближайший город {name} из {country} располагается в " +
                "{distance:.1f}км от заданных координат. Продолжить?"
            ).format_map(city_data)
        data['cityData'] = CitySerializer(
            City.objects.get(id=cities['dist'].idxmin())
        ).data

    return JsonResponse(data, status=status.HTTP_200_OK)


