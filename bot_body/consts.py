import os
import json

# Config
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
WEATHER_TOKEN = os.getenv('WEATHER_TOKEN')
TRANSMISSION_URL = os.getenv('TRANSMISSION_URL')
TRANSMISSION_USER = os.getenv('TRANSMISSION_USER')
TRANSMISSION_PASSWORD = os.getenv('TRANSMISSION_PASSWORD')

# Command Buttons
BACK_COMMAND = 'Назад'
ADD_COMMAND = 'Добавить'
LIST_COMMAND = 'Список закачек'

# Text Buttons
WEATHER_BUTTON = 'Погода'
RATES_BUTTON = 'Курсы'
TORRENT_BUTTON = 'Торренты'

# Currency codes
USD_BUTTON = {
    "code": "USD",
    "text": "$_USD"
}

EURO_BUTTON = {
    "code": "EUR",
    "text": "€_EUR"
}

YUAN_BUTTON = {
    "code": "CNY",
    "text": "¥_YUAN"
}

# Users allowed to command bot
ALLOWED_USER_IDS = set(
    json.loads(os.getenv("USER_ADMINS"))
    )


print(f"Loaded conf. Token is {ACCESS_TOKEN} and URL is {TRANSMISSION_URL} and user is {ALLOWED_USER_IDS}")