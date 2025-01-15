import requests
import pandas as pd

import matplotlib.path as mplPath
import numpy as np
import sqlite3


class ChargingStationPipeline:
    def __init__(self):
        self.data_path = 'https://lavenderblush-walrus-833841.hostingersite.com/data/us_ev_charging_stations_2024.json'
        self.data = None

    def _parse_data(self):
        data = self._fetch_data()
        try:
            self.data = data
        except Exception as e:
            raise e

    def _fetch_data(self):
        response = requests.get(self.data_path)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch data from {self.data_path}")

        return response.json()

    def _clean_data(self):
        try:
            res = []
            for data_point in self.data:

                if ("lat" not in data_point or "lng" not in data_point
                        or data_point["lat"] is None or data_point["lng"] is None):
                    print(f"Invalid data point: {data_point}")

                res.append({
                    "latitude": data_point["lat"],
                    "longitude": data_point["lng"],
                })
            return res
        except Exception as e:
            raise e

    def get_data(self):
        self._parse_data()
        try:
            return self._clean_data()
        except Exception as e:
            print(e)
            raise e


class GeometryPipeline:
    def __init__(self):
        self.data_path = 'https://lavenderblush-walrus-833841.hostingersite.com/data/us_states_polygon_2020.json'
        self.data = None

        self.df_selection = None

    def _parse_data(self):
        data = self._fetch_data()
        try:
            self.data = data
        except Exception as e:
            raise e

    def _fetch_data(self):
        response = requests.get(self.data_path)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch data from {self.data_path}")

        return response.json()

    def _clean_data(self):
        try:
            data = self.data

            df = pd.DataFrame(data["features"])

            df['Location'] = df['properties'].apply(lambda x: x['NAME'])
            df['Type'] = df['geometry'].apply(lambda x: x['type'])
            df['Coordinates'] = df['geometry'].apply(lambda x: x['coordinates'])
            df_new = pd.DataFrame()

            for idx, row in df.iterrows():

                if row['Type'] == 'MultiPolygon':
                    polys = []
                    df_row = row['Coordinates']
                    for df_row_ in df_row:
                        pol = mplPath.Path(np.array(df_row_[0]))
                        polys.append(pol)
                    poly = polys

                elif row['Type'] == 'Polygon':
                    df_row = row['Coordinates']
                    poly = mplPath.Path(np.array(df_row[0]))

                else:
                    poly = None

                row['Polygon'] = poly

                df_new = pd.concat([df_new, row], axis=1)

            df_new = df_new.transpose()
            self.df_selection = df_new.drop(columns=['type', 'properties', 'geometry', 'Coordinates'])

        except Exception as e:
            raise e

    def get_state(self, lat, long):

        for idx, row in self.df_selection.iterrows():
            if isinstance(row['Polygon'], list):
                # Polygon is a MultiPolygon
                for poly in row['Polygon']:
                    if poly.contains_point((lat, long)) or poly.contains_point((long, lat)):
                        return row['Location']
            else:
                if row['Polygon'].contains_point((lat, long)) or row['Polygon'].contains_point((long, lat)):
                    return row['Location']

        return None

    def get_data(self):
        self._parse_data()
        try:
            self._clean_data()
        except Exception as e:
            print(e)
            raise e


def data_storage_to_sqlite(data):
    data = dict(sorted(data.items(), key=lambda x: x[0]))
    conn = sqlite3.connect('../data/charging_station.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE charging_stations (
                    state_name VARCHAR(255),
                    count_of_ev_charging_stations INT
                );
            ''')

    for state, count in data.items():
        c.execute(
            f"INSERT INTO charging_stations (state_name, count_of_ev_charging_stations) VALUES ('{state}', {count});")

    conn.commit()
    conn.close()


class ProjectPipeline:

    def __init__(self):
        self.charging_station_pipeline = ChargingStationPipeline()
        self.geometry_pipeline = GeometryPipeline()

    def run_pipeline(self):
        charging_station_data = self.charging_station_pipeline.get_data()
        self.geometry_pipeline.get_data()

        state_count = {}

        for station_location in charging_station_data:
            state = self.geometry_pipeline.get_state(
                lat=station_location["latitude"],
                long=station_location["longitude"]
            )
            if state is not None:
                state_count[state] = state_count.get(state, 0) + 1
            else:
                print(f"Could not find state for location: {station_location}")

        data_storage_to_sqlite(state_count)


if __name__ == "__main__":
    ProjectPipeline().run_pipeline()
