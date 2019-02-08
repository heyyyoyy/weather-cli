from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='weather-cli',
    version='0.1',
    py_modules=['weather'],
    include_package_data=True,
    install_requires=required,
    entry_points='''
        [console_scripts]
        weather=weather:weather_cli
    ''',
)
