import httpx
import json
COURSES_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'

async def get_curses():
    async with httpx.AsyncClient() as client:
        response = await client.get(url=COURSES_URL)
        if response.status_code == 200:
            res_json = json.loads(response.text)    
    usd = res_json.get('Valute', 'OOoops кажется недоступен сервис')
    eur = res_json.get('Valute', 'OOoops кажется недоступен сервис')
    cny = res_json.get('Valute', 'OOoops кажется недоступен сервис')
    return {
        'USD': usd['USD']['Value'],
        'EUR': eur['EUR']['Value'],
        'CNY': cny['CNY']['Value']
    }