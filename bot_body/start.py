from bot_body import bot_logic
from aiogram import executor

def main():
    # Запускаем бота
    executor.start_polling(bot_logic.dp)

if __name__ == '__main__':
    main()