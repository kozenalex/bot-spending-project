import telebot
from telebot import types
from bot_body import weather_cast, curses
from pathlib import Path
from dotenv import load_dotenv
import os

env_path = os.path.join('.', '.env')
load_dotenv(dotenv_path=env_path)
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', None)

bot = telebot.TeleBot(ACCESS_TOKEN)
startmarkup = types.ReplyKeyboardMarkup(True)
startmarkup.add('Погода', 'Курсы')

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        text="Привет",
        reply_markup=startmarkup
        )

@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text.strip() == 'Погода':
        bot.send_message(message.chat.id, 'Введите город')
        bot.register_next_step_handler(message, weather_msg)
    elif message.text.strip() == 'Курсы':
        currency_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        currency_markup.add('USD', 'EUR')
        bot.send_message(message.chat.id, 'Выбор валюты:', reply_markup=currency_markup)
        bot.register_next_step_handler(message, currency_msg)
    else:
        bot.send_message(message.chat.id, 'Вы написали: ' + message.text)

@bot.message_handler(content_types=["text"])
def weather_msg(message):
    city = message.text.strip()
    m_text = weather_cast.get_weather(city)
    bot.send_message(message.chat.id, m_text)

@bot.message_handler(content_types=["text"])
def currency_msg(message):
    currency = message.text.strip()
    m_text = curses.get_curses()[currency]
    bot.send_message(
        message.chat.id,
        str(m_text) + 'руб.',
        reply_markup=startmarkup
        )