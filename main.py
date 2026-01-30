from config import BOT_TOKEN
from database import db
import admin_handlers
import cart_handlers
import catalog_handlers
import general_handlers
import asyncio
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Добавляем текущую директорию в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
bot = Bot(token=BOT_TOKEN)


async def new_order_notification(order_info: str):
    """Функция для отправки уведомления о новом заказе"""

    await bot.send_message(
        chat_id=1012701165,
        text=order_info,
        parse_mode="HTML"
    )
    await bot.session.close()


async def main():
    try:
        print("=" * 50)
        print("🎿 Запуск магазина липучек для лыж...")

        db.init_db()

        print("✅ База данных инициализирована")

        # Проверяем товары в базе
        products = db.get_all_products()
        print(f"\n📦 Проверка товаров в базе (всего {len(products)}):")
        for product in products:
            has_photo = "✅" if product.get('photo_id') else "❌"
            print(
                f"  {has_photo} {product['name']}: {product.get('quantity', 0)} шт., {product.get('price', 0)} руб.")
            if product.get('photo_id'):
                print(f"     Photo ID: {product['photo_id'][:40]}...")

        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        dp.include_router(general_handlers.router)
        dp.include_router(catalog_handlers.router)
        dp.include_router(cart_handlers.router)
        dp.include_router(admin_handlers.router)

        print("\n✅ Бот запущен")
        print("🔐 Пароль админа: 260707")
        print("🔑 Для входа в админ-панель используйте команду /admin")
        print("=" * 50)

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("Проверьте:")
        print("1. Токен бота в config.py")
        print("2. Подключение к интернету")
        print("3. Установлены ли все зависимости (pip install aiogram)")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
