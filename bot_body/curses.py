import requests
import json
COURSES_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'

def get_curses():
    response = requests.get(COURSES_URL)
    res_json = json.loads(response.text)
    usd = res_json.get('Valute', 'OOoops кажется недоступен сервис')
    eur = res_json.get('Valute', 'OOoops кажется недоступен сервис')
    return {
        'USD': usd['USD']['Value'],
        'EUR': eur['USD']['Value']
    }