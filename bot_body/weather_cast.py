import httpx
import json


async def get_weather(city: str, lat=None, lon=None):
    url = 'http://api.openweathermap.org/data/2.5/weather'
    if lat and lon:
        params = {
            'lat': lat,
            'lon': lon,
            'APPID': '64c67d223f951745cb062a250e5b5ff4',
            'units': 'metric'
        }
    else:
        params={
                'q': city,
                'APPID': '64c67d223f951745cb062a250e5b5ff4',
                'units': 'metric'
            }
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