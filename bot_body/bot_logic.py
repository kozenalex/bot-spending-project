import telebot
from telebot import types
from bot_body import weather_cast

# Создаем экземпляр бота
bot = telebot.TeleBot('5561759053:AAESUfexBwfp-ftqVSP30lg6_uO5ddVnJ5w')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(True)
    markup.add('Погода', 'Эхо')
    bot.send_message(
        message.chat.id,
        text="Привет",
        reply_markup=markup
        )

@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text.strip() == 'Погода':
        bot.send_message(message.chat.id, 'Введите город')
        bot.register_next_step_handler(message, weather_msg)        
    else:
        bot.send_message(message.chat.id, 'Вы написали: ' + message.text)

@bot.message_handler(content_types=["text"])
def weather_msg(message):
    city = message.text.strip()
    m_text = weather_cast.get_weather(city)
    bot.send_message(message.chat.id, m_text)