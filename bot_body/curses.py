import requests
import json
COURSES_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'

def get_curses():
    response = requests.get(COURSES_URL)
    res_json = json.loads(response.text)
    return {
        'USD': res_json['Valute']['USD']['Value'],
        'EUR': res_json['Valute']['EUR']['Value']
    }