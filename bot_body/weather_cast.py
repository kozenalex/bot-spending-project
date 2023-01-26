import requests
import json

def get_weather(city: str):
    url = 'http://api.weatherapi.com/v1/current.json'
    response = requests.get(
        url,
        params={
            'key': '3f134828acca4068a1280558232301',
            'q': city
        }
    )
    res_dict = json.loads(response.text)
    if res_dict.get('error', None):
        message = 'Город не найден или сервис недоступен :('
    else:
        message = 'Температура: ' + str(res_dict['current']['temp_c']) + '\n'
        message += 'Ощущается как: ' + str(res_dict['current']['feelslike_c']) + '\n'
    return message