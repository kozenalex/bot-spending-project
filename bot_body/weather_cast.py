import httpx
import json
from dotenv import load_dotenv
import os

env_path = os.path.join('.', '.env')
load_dotenv(dotenv_path=env_path)
WEATHER_TOKEN = os.getenv('WEATHER_TOKEN', None)


async def get_weather(city: str, lat=None, lon=None):
    url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {
        'APPID': WEATHER_TOKEN,
        'units': 'metric'
    }
    if lat and lon:
        params['lat'] = lat
        params['lon'] = lon
    else:
        params['q'] = city
    message = 'Ошибка какая-то'
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, params=params)
        res_dict = json.loads(response.text)
        if res_dict.get('cod', None) != 200:
            message = 'Город не найден или сервис недоступен :('
        else:
            message = 'Город: ' + res_dict['name'] + '\n'
            message += 'Температура: ' + str(res_dict['main']['temp']) + '\n'
            message += 'Ощущается как: ' + str(res_dict['main']['feels_like']) + '\n'
    return message