import requests
from math import cos
import click
from dotenv import load_dotenv
import os
import sys
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

load_dotenv()


class CityWeather:
    TOKEN = os.environ['TOKEN']

    def __init__(self, city, kilometers):
        self.city = city
        self.kilometers = kilometers
        self.data = self.get_city_weather()

    def get_city_weather(self):
        params = {'q': self.city, 'appid': self.TOKEN}
        resp = requests.get(
            'http://api.openweathermap.org/data/2.5/weather',
            params=params
        )
        data = resp.json()
        if data['cod'] == 200:
            return data

    def get_temperature(self):
        self.get_city_weather()
        if self.data is not None:
            # Перевод градусов из кельвинов в цельсии
            return int(self.data['main']['temp'] - 273.15)

    def get_coordinates(self):
        if self.data is not None:
            return self.data['coord']['lon'], self.data['coord']['lat']

    def prepare_coordinates(self, lon, lat):
        '''
        Преобразование киллометров в градусы
        Latitude:  1 deg = 111 km
        Longitude: 1 deg = 111 * cos(latitude) km
        '''
        lat_deg = self.kilometers / 111
        lon_deg = self.kilometers / (111 * cos(lat))

        lat_bottom = round(lat - lat_deg, 2)
        lat_top = round(lat + lat_deg, 2)
        lon_left = round(lon - lon_deg, 2)
        lon_right = round(lon + lon_deg, 2)
        return f'{lon_left},{lat_bottom},{lon_right},{lat_top}'

    def get_area_weather(self, coordinates):
        params = {'bbox': f'{coordinates},10', 'appid': self.TOKEN}
        resp = requests.get(
            'http://api.openweathermap.org/data/2.5/box/city',
            params=params
        )
        data = resp.json()
        if data and data['cod'] == 200:
            return data

    def get_average_temp(self, lon, lat):
        coordinates = self.prepare_coordinates(lon, lat)
        data = self.get_area_weather(coordinates)
        if data:
            cities = [int(city['main']['temp']) for city in data['list']]
            average_temp = sum(cities) / len(cities)
            return average_temp


def pipeline(city, km):
    city = CityWeather(city, km)
    temp = city.get_temperature()
    if temp is None:
        click.echo(f'{city.city} - Неверно указан город')
        return city.city, None, None
    coordinates = city.get_coordinates()
    average_temp = city.get_average_temp(*coordinates)
    if average_temp is None:
        click.echo(f'{city.city} - Укажите большее расстояние')
        return city.city, temp, None

    return city.city, temp, average_temp


@click.command()
@click.option(
    '--city', default='Yaroslavl',
    help='Город по которому будет показана температура'
)
@click.option(
    '--km', default=150,
    help='Расстояние от города в заданном квадрате'
)
@click.option(
    '--file',
    help='Название txt файла, с перечислением город:километры'
)
def weather_cli(city, km, file):
    '''
    Инструмент, с помощью которого,
    вы сможете узнать температуру в вашем городе

    \b
    weather --city Moscow --km 200
    weather --file cities.txt
    '''
    if file is None:
        city, temp, average_temp = pipeline(city, km)
        if temp is None:
            sys.exit(1)
        if average_temp is None:
            sys.exit(1)

        click.echo(f'Температура в {city}: {temp} C')
        click.echo(f'Средняя температура {average_temp:.2f}')
    else:
        with open(file) as f:
            data = f.read().splitlines()
            city_km = (line.split(':') for line in data)
            city_average = []

            with ThreadPoolExecutor(5) as pool:
                futures = {
                    pool.submit(pipeline, city, int(km))
                    for city, km in city_km
                }
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()

                    if all(result):
                        city_average.append(result)

            city_average.sort(key=lambda lst: lst[-1])

            for city, temp, avr in city_average:
                click.echo(f'Температура в {city}: {temp} C')
                click.echo(f'Средняя температура {avr:.2f}')
                click.echo('---------------------------------------')


if __name__ == "__main__":
    weather_cli()
