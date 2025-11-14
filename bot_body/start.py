import asyncio
from bot_body import bot_logic
from aiogram import Bot, Dispatcher

def main():
    asyncio.run(_run_bot())

async def _run_bot():
    # Запускаем бота
    await bot_logic.dp.start_polling(bot_logic.bot)

if __name__ == '__main__':
    asyncio.run(main())