import requests
from math import cos
import click
from dotenv import load_dotenv
import os
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

load_dotenv()


class CityWeather:
    TOKEN = os.environ['TOKEN']

    def __init__(self, city, kilometers):
        self.city = city
        self.kilometers = kilometers

    def get_city_weather(self):
        params = {'q': self.city, 'appid': self.TOKEN}
        resp = requests.get(
            'http://api.openweathermap.org/data/2.5/weather',
            params=params
        )
        data = resp.json()
        if data['cod'] == 200:
            return data

    def get_temperature(self, data):
        # Перевод градусов из кельвинов в цельсии
        return int(data['main']['temp'] - 273.15)

    def get_coordinates(self, data):
        return data['coord']['lon'], data['coord']['lat']

    def get_info(self):
        data = self.get_city_weather()
        if data is not None:
            temp = self.get_temperature(data)
            lon, lat = self.get_coordinates(data)
            coordinates = self.prepare_coordinates(lon, lat)
            average_temp = self.get_average_temp(coordinates)
            return temp, average_temp
            return f'Температура в {self.city}: {temp} C'

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
        if data['cod'] == 200:
            return data

    def get_average_temp(self, coordinates):
        data = self.get_area_weather(coordinates)
        if data is not None:
            cities = [int(city['main']['temp']) for city in data['list']]
            average_temp = sum(cities) / len(cities)
            return average_temp


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
        city = CityWeather(city, km)
        try:
            temp, average_temp = city.get_info()
        except TypeError:
            click.echo(
                'Произошла ошибка во время выполнения, '
                'укажите корректные данные'
            )
        else:
            click.echo(f'Температура в {city.city}: {temp} C')
            click.echo(f'Средняя температура {average_temp:.2f}')
    else:
        with open(file) as f:
            data = f.read().splitlines()
            city_km = (line.split(':') for line in data)
            with ThreadPoolExecutor(5) as pool:
                cities_km = (
                    CityWeather(city[0], int(city[1]))
                    for city in city_km
                )
                futures = {
                    pool.submit(city.get_info): city.city
                    for city in cities_km
                }
                for future in concurrent.futures.as_completed(futures):
                    city_average = {}
                    city = futures[future]
                    try:
                        temp, average_temp = future.result()
                    except Exception:
                        click.echo(
                            f'Произошла ошибка во время запроса '
                            f'по городу {city}'
                        )
                    else:
                        city_average[city] = [temp, average_temp]
                    sort(city_average, key=lambda obj: -obj[1])
                    for city, values in city_average.values(): 
                        click.echo(f'Температура в {city}: {values[0]} C')
                        click.echo(f'Средняя температура {values[1]:.2f}')
                        click.echo('---------------------------------------')


if __name__ == "__main__":
    weather_cli()
