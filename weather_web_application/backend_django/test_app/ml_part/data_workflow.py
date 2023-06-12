import time
import datetime
import requests
import warnings
import numpy as np
import pandas as pd
from haversine import haversine
from ..models import City, Station


class DataCollection:
    def __init__(
        self, loc_coords: tuple, num_stations=3,
        dataset='daily-summaries', data_types='PRCP,TMAX,TMIN',  
        start_date=datetime.date.min.strftime('%Y-%m-%d'),
        end_date=datetime.datetime.today().strftime('%Y-%m-%d'),     
    ):
        self._base_api_url = (
            'https://www.ncei.noaa.gov/access/services/data/v1/?'
        )
        self.stations = pd.DataFrame(
            Station.objects.values(), 
            columns=[field.name for field in Station._meta.get_fields()]
        )
        self.cities = pd.DataFrame(
            City.objects.values(), 
            columns=[field.name for field in City._meta.get_fields()]
        )
        self._dataset = self.__call_api(
            loc_coords, num_stations, dataset, data_types, start_date, end_date 
        )


    def __call_api(
        self, loc_coords, num_stations, dataset, data_types, 
        start_date, end_date
    ):
        stations = self._get_nearest_station(*loc_coords, num_stations)
        full_url = self._base_api_url + 'dataset=' + dataset + '&dataTypes=' + \
            data_types + '&stations=' + stations + '&startDate=' + start_date \
            + '&endDate=' + end_date + '&boundingBox=90,-180,-90,180' + \
            '&units=metric'

        response = requests.get(full_url)
        if response.status_code != 200: response.raise_for_status()
        return response.text

    
    def _get_nearest_station(self, lat, long, num_stations=3):
        stations_locs = pd.DataFrame({
            'Id': self.stations['name'],
            'Coords': tuple(zip(
                self.stations['lat'], self.stations['lng']
            ))
        })
        cities_locs = pd.DataFrame({
            'City': self.cities['name'], 
            'Coords': tuple(zip(
                self.cities['lat'], self.cities['lng']
            ))
        })

        station_ids = []
        coords = (lat, long)
        for i in range(num_stations):    
            stations_locs['Dist'] = stations_locs['Coords'].map(
                lambda x: haversine(coords, x)
            )
            cities_locs['Dist'] = cities_locs['Coords'].map(
                lambda x: haversine(coords, x)
            )
            
            nearest_station_ind = stations_locs['Dist'].idxmin()
            nearest_station = stations_locs.loc[nearest_station_ind]
            nearest_city = cities_locs.loc[cities_locs['Dist'].idxmin()]
            
            if i > 0 and nearest_station['Dist'] >= 150:
                print(
                    f"{i} stations were only used. The rest are located > 150km"
                )
                break  
                
            if i == 0:
                print("The nearest city is {city} -> {dist} km".format_map({
                    'city': nearest_city['City'], 
                    'dist': round(nearest_city['Dist'], 3)
                }))
                print('*'*10 + ' Stations ' + '*'*10)
                
            print("{counter}. {id} -> {dist} km".format_map({
                'counter': i + 1,
                'id': nearest_station['Id'], 
                'dist': round(nearest_station['Dist'], 3)
            })) 
            
            station_ids.append(nearest_station['Id'])
            stations_locs.drop(nearest_station_ind, inplace=True)

        return ','.join(station_ids)
    


class DataCleaning:
    def __init__(
        self, station_data, cols=['PRCP', 'TMAX', 'TMIN'], 
        start_date='1940-01-02'
    ):
        # Getting the coordinates of the first station
        self.station_coords = self.get_station_coords(
            station_data.loc[1, 'STATION']
        )
        self.start_date = start_date 
        self._data = self.wrangle(station_data, cols)
        
    
    def get_station_coords(self, station_id):
        ghcnd_stations = pd.DataFrame(
            Station.objects.values(), 
            columns=[field.name for field in Station._meta.get_fields()]
        )
        lat, lng = np.ravel(ghcnd_stations.loc[
            ghcnd_stations['name'] == station_id, ['lat', 'lng']
        ].values)
        return (lat, lng)
    
    
    def wrangle(self, station_data: pd.DataFrame, cols: list):
        station_data['date'] = pd.to_datetime(station_data['DATE'])
        station_data = station_data.set_index('date').drop('DATE', axis=1)
        # We remove data which are before 'start_date'
        station_data = station_data[station_data.index >= self.start_date]
        
        all_cols = {
            'PRCP': 'precip_sum', 'TMAX': 'temp_max', 'TMIN': 'temp_min'
        }
        df = station_data.copy()
        replaced_cols = {col: all_cols[col] for col in cols}
        df.rename(columns=replaced_cols, inplace=True)
        
        # At first if there are the data from several stations, we will fill
        # missing values taken the nearest one as the main. The next stations 
        # will be used to fill in the nearest one in order.
        num_stations = df['STATION'].nunique()
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        all_needed_dates = pd.date_range(self.start_date, today, freq='D')
        if num_stations > 1:
            station_names = list(df['STATION'].unique())
            print(f"The nearest station is '{station_names[0]}'")
            nearest_station_data = df[df['STATION'] == station_names.pop(0)]
            df_comb = nearest_station_data.copy()
            print("Total missing values:", df_comb.isna().sum().sum())
            print("Total missing dates: {}".format(
                len(set(all_needed_dates)- set(df_comb.index))
            )) 
            print("Filling them using the other stations: {}".format(
                ', '.join(station_names)
            ), end='\n\n')
            while df_comb.isna().values.any() and station_names:
                station_name = station_names.pop(0)
                next_station_data = df[df['STATION'] == station_name]
                
                # Filling missing values in the same location
                df_comb = df_comb.combine_first(
                    # We have to have the same dataframes by shapes
                    next_station_data.loc[list(
                        set(next_station_data.index) & set(df_comb.index)
                    )]
                )
                
                # If there are missing dates from the start date to the last.
                # The last rest of the dates are filled with ERA5 data. 
                missing_inds = missing_inds = list(
                    set(next_station_data.index) - set(df_comb.index)
                )
                if missing_inds:
                    df_comb = pd.concat([
                        df_comb, next_station_data.loc[missing_inds]
                    ]).sort_index()
                    
                print(f"Station '{station_name}'")
                print("Left missing values -> {num_mis_vals}".format(
                    num_mis_vals=df_comb.isna().sum().sum()
                ))
                print("Left missing dates -> {left_dates}".format(
                    left_dates=len(set(all_needed_dates)- set(df_comb.index))
                ), end='\n\n')
                
            df = df_comb
        
        print("There were left {} missing values and {} missing dates".format(
            df.isna().sum().sum(), len(set(all_needed_dates) - set(df.index))
        ), end='. Now they will be filled data from ERA5 dataset')
        return df[replaced_cols.values()]
    
    
    @staticmethod
    def get_era_data(
        lat, lng, start_date='1940-01-02', data_types=[
            'temperature_2m_max', 'temperature_2m_min', 'precipitation_sum'
        ]
    ):
        # Get the ERA reanalysis dataset
        def execute_request(url):
            response = requests.get(url)
            if response.status_code != 200: response.raise_for_status()
            result = response.json()
            if 'daily' in result.keys():
                renamed_elems = {
                    'temperature_2m_max': 'temp_max',
                    'temperature_2m_min': 'temp_min',
                    'precipitation_sum' : 'precip_sum',
                    'rain_sum'          : 'rain_sum', 
                    'snowfall_sum'      : 'snowfall_sum',
                    'windspeed_10m_max' : 'windspeed_max',
                    'windgusts_10m_max' : 'windgusts_max',
                    'winddirection_10m_dominant': 'winddirection_dominant' 
                }
                data = {
                    renamed_elems[data_type]: result['daily'][data_type] 
                    for data_type in data_types
                }
                return pd.DataFrame({'date': result['daily']['time']} | data)
            elif 'hourly' in result.keys():
                data = {
                    'pressure_msl': result['hourly']['pressure_msl'],
                    'relat_humidity': result['hourly']['relativehumidity_2m']
                }
                df = pd.DataFrame({'time': result['hourly']['time']} | data)
                df['time'] = pd.to_datetime(df['time'])
                df = df.resample('D', on='time').mean().round().reset_index()
                #df['pressure_msl'] = np.round(df['pressure_msl'])
                return df.rename(columns={'time': 'date'})
        
        
        hourly_types = ['pressure_msl', 'relativehumidity_2m']
        hourly_flag = list(set(hourly_types) & set(data_types)) == hourly_types
        data_types = list(set(data_types) - set(hourly_types))
        
        end_date = datetime.datetime.today().strftime('%Y-%m-%d')
        era_data_url = (
            f'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&'
            f'longitude={lng}&start_date={start_date}&end_date={end_date}&'
            f'daily={",".join(data_types)}&windspeed_unit=ms&timezone=auto'
        )
        era_data = execute_request(era_data_url) # Without last today

        # Deleting unknown data for today's day and January 1st of 
        era_data = era_data[~era_data.isna().any(axis=1)]

        # There is a delay of 5 days in the data above, 
        # so one also needs to get the records for these days
        start_date_fc = str((datetime.datetime.strptime(
            era_data["date"].iloc[-1], '%Y-%m-%d'
        ) + datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
        era_data_url_fc = (
            'https://api.open-meteo.com/v1/forecast?'
            f'latitude={lat}&longitude={lng}&'
            f'daily={",".join(data_types)}&windspeed_unit=ms&'
            f'forecast_days=1&start_date={start_date_fc}&'
            f'end_date={end_date}&timezone=auto'
        )
        era_data_fc = execute_request(era_data_url_fc)
        
        era_data = pd.concat([era_data, era_data_fc])
        era_data['date'] = pd.to_datetime(era_data['date'])
        
        if hourly_flag:
            era_pressure_url = (
                f'https://archive-api.open-meteo.com/v1/archive?'
                f'latitude={lat}&longitude={lng}&'
                f'start_date={start_date}&end_date={end_date}&'
                f'hourly={",".join(hourly_types)}'
            )
            era_pressure_fc = (
                'https://api.open-meteo.com/v1/forecast?'
                f'latitude={lat}&longitude={lng}&'
                f'start_date={start_date_fc}&end_date={end_date}&'
                f'hourly={",".join(hourly_types)}&forecast_days=1'
            )
            era_data_pressure = execute_request(era_pressure_url)
            era_data_pressure_fc = execute_request(era_pressure_fc)
            era_pressure = pd.concat([era_data_pressure, era_data_pressure_fc])
            era_data = era_data.merge(era_pressure, on='date')
            if any(era_data['date'].duplicated()):
                # There is an issue with the last week
                era_data = era_data[~era_data['date'].duplicated(keep='last')]

        era_data.set_index('date', inplace=True)
        return era_data
    
    
    def _filling_station_data(self, era_data):
        # Then we will fill the rest of missing values and dates in station
        # data using ERA5 data
        missing_inds = list(set(era_data.index) - set(self._data.index))
        data = pd.concat([self._data, era_data.loc[missing_inds]]).sort_index()
        if not data.index.is_unique:  # In any case
            data = data[~data.index.duplicated(keep='first')]
        return data.combine_first(era_data)
    
    
    def get_cleaned_data(self):
        return self._filling_station_data(
            self.get_era_data(*self.station_coords, self.start_date)
        )
    

class LatestData:
    def __init__(
        self, station_coords, data_types, start_date='2000-01-01',
        intermidiate_dists=[100, 500, 1000]
    ):
        self.all_stations = pd.DataFrame(
            Station.objects.values(), 
            columns=[field.name for field in Station._meta.get_fields()]
        )
        self.station_dataset = DataCleaning.get_era_data(
            *station_coords, start_date, data_types
        )
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            warnings.warn('default', category=pd.errors.SettingWithCopyWarning)
            station_names = self.get_station_names_bw_dists_of_cardinal_points(
                *station_coords, dists=intermidiate_dists
            )
        self.station_names = station_names
        
        self.combined_dataset = self.combine_station_datasets(
            station_names, start_date, data_types
        )


    def combine_station_datasets(
        self, station_names, start_date, data_types
    ) -> pd.DataFrame:
        combined_dataset = self.station_dataset.copy()
        for ind, dist in zip(['near', 'far'], station_names.keys()):
            for side, station_id in station_names[dist].items():
                try: 
                    station_coords = self.all_stations.loc[
                        self.all_stations['name'] == station_id, ['lat', 'lng']
                    ].values[0]
                except: print(f"There is no a station from {side} side.")
                time.sleep(0.2)
                station_era_data = DataCleaning.get_era_data(
                    *station_coords, start_date, data_types
                )
                station_era_data = station_era_data.rename(columns={
                    old_col: ind + side + old_col 
                    for old_col in station_era_data.columns
                })
                combined_dataset = combined_dataset.merge(
                    station_era_data, on='date'
                )
        return combined_dataset


    def get_station_names_bw_dists_of_cardinal_points(
        self, lat, long, dists: list, degree_step=1e-3
    ) -> dict:
        dists.sort()
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
                int(lat), int(long), min_dist=dist
            )
            
        stations_locs = self.all_stations.copy().rename(
            columns={'name': 'Id', 'lat': 'Latitude', 'lng': 'Longitude'}
        )
        stations_locs['Coords'] = tuple(zip(
            stations_locs['Latitude'], stations_locs['Longitude']
        ))
        
        dist_station = {}
        card_points = {'north': 0, 'south': 1, 'west': 2, 'east': 3}
        for i in range(len(dists)-1):
            start_dist, end_dist = dists[i], dists[i+1]
            station_ids = {
                card_point: None for card_point in card_points.keys()
            }
            
            # WEST
            near_west_long = extreme_points[start_dist][card_points['west']]
            far_west_long = extreme_points[end_dist][card_points['west']]
            far_north_lat = extreme_points[end_dist][card_points['north']]
            far_south_lat = extreme_points[end_dist][card_points['south']]
            west_sector = stations_locs[
                (stations_locs['Longitude'] < near_west_long) &
                (stations_locs['Longitude'] > far_west_long) &
                (stations_locs['Latitude'] < far_north_lat) &
                (stations_locs['Latitude'] > far_south_lat)
            ].copy()
            if len(west_sector) > 0:
                mean_long = (near_west_long + far_west_long) / 2
                mean_lat = (far_north_lat + far_south_lat) / 2
                central_west = (mean_lat, mean_long)
                west_sector['Dist'] = west_sector['Coords'].map(
                    lambda stat_coords: haversine(central_west, stat_coords)
                )
                station_ind = west_sector['Dist'].idxmin()
                station_id = west_sector.loc[station_ind]['Id']
                while station_id in station_ids.values():
                    west_sector.drop(station_ind, inplace=True)
                    station_ind = west_sector['Dist'].idxmin()
                    station_id = west_sector.loc[station_ind]['Id']
                station_ids['west'] = station_id
            
            # EAST
            near_east_long = extreme_points[start_dist][card_points['east']]
            far_east_long = extreme_points[end_dist][card_points['east']]
            far_north_lat = extreme_points[end_dist][card_points['north']]
            far_south_lat = extreme_points[end_dist][card_points['south']]
            east_sector = stations_locs[
                (stations_locs['Longitude'] > near_east_long) &
                (stations_locs['Longitude'] < far_east_long) &
                (stations_locs['Latitude'] < far_north_lat) &
                (stations_locs['Latitude'] > far_south_lat)
            ].copy()
            if len(east_sector) > 0:
                mean_long = (near_east_long + far_east_long) / 2
                mean_lat = (far_north_lat + far_south_lat) / 2
                central_east = (mean_lat, mean_long)
                east_sector['Dist'] = east_sector['Coords'].map(
                    lambda stat_coords: haversine(central_east, stat_coords)
                )
                station_ind = east_sector['Dist'].idxmin()
                station_id = east_sector.loc[station_ind]['Id']
                while station_id in station_ids.values():
                    east_sector.drop(station_ind, inplace=True)
                    station_ind = east_sector['Dist'].idxmin()
                    station_id = east_sector.loc[station_ind]['Id']
                station_ids['east'] = station_id
            
            # NORTH
            near_north_lat = extreme_points[start_dist][card_points['north']]
            far_north_lat = extreme_points[end_dist][card_points['north']]
            far_west_long = extreme_points[end_dist][card_points['west']]
            far_east_long = extreme_points[end_dist][card_points['east']]
            north_sector = stations_locs[
                (stations_locs['Longitude'] > far_west_long) &
                (stations_locs['Longitude'] < far_east_long) &
                (stations_locs['Latitude'] < far_north_lat) &
                (stations_locs['Latitude'] > near_north_lat)
            ].copy()
            if len(north_sector) > 0:
                mean_long = (near_east_long + far_east_long) / 2
                mean_lat = (far_north_lat + near_north_lat) / 2
                central_north = (mean_lat, mean_long)
                north_sector['Dist'] = north_sector['Coords'].map(
                    lambda stat_coords: haversine(central_north, stat_coords)
                )
                station_ind = north_sector['Dist'].idxmin()
                station_id = north_sector.loc[station_ind]['Id']
                while station_id in station_ids.values():
                    north_sector.drop(station_ind, inplace=True)
                    station_ind = north_sector['Dist'].idxmin()
                    station_id = north_sector.loc[station_ind]['Id']
                station_ids['north'] = station_id
            
            # SOUTH
            near_south_lat = extreme_points[start_dist][card_points['south']]
            far_south_lat = extreme_points[end_dist][card_points['south']]
            far_west_long = extreme_points[end_dist][card_points['west']]
            far_east_long = extreme_points[end_dist][card_points['east']]
            south_sector = stations_locs[
                (stations_locs['Longitude'] > far_west_long) &
                (stations_locs['Longitude'] < far_east_long) &
                (stations_locs['Latitude'] > far_south_lat) &
                (stations_locs['Latitude'] < near_south_lat)
            ].copy()
            if len(south_sector) > 0:
                mean_long = (near_east_long + far_east_long) / 2
                mean_lat = (far_south_lat + near_south_lat) / 2
                central_south = (mean_lat, mean_long)
                south_sector['Dist'] = south_sector['Coords'].map(
                    lambda stat_coords: haversine(central_south, stat_coords)
                )
                station_ind = south_sector['Dist'].idxmin()
                station_id = south_sector.loc[station_ind]['Id']
                while station_id in station_ids.values():
                    south_sector.drop(station_ind, inplace=True)
                    station_ind = south_sector['Dist'].idxmin()
                    station_id = south_sector.loc[station_ind]['Id']
                station_ids['south'] = station_id
            
            dist_station[f'{start_dist}-{end_dist}km'] = station_ids
            
        return dist_station