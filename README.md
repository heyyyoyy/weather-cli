# weather-cli

Приложение с помощью которого можно узнать температуру в городе и указаной области

1. Создаем и активируем окружение
`python3.7 -m venv venv && source venv/bin/activate`

2. Собираем наше приложение
`python setup.py install`

3. Проверяем
```
$ weather --city Moscow --km 300

Температура в Moscow: 1 C
Средняя температура -1.31
```

Справка по программе `weather --help`