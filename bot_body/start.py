from bot_body import bot_logic

def main():
    # Запускаем бота
    bot_logic.bot.polling(none_stop=True, interval=0)

if __name__ == '__main__':
    main()