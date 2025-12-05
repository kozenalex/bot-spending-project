import asyncio
import bot_logic

async def main():
    await bot_logic.dp.start_polling(bot_logic.bot)
    

if __name__ == '__main__':
    asyncio.run(main())