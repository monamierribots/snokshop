from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards import get_main_keyboard, get_admin_keyboard
from states import UserStates, AdminStates
from config import ADMIN_PASSWORD

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserStates.main_menu)

    welcome_text = (
        "🎿 Добро пожаловать в магазин липучек для лыж!\n\n"
        "У нас вы найдете качественные липучки разных цветов:\n"
        "• Черные\n"
        "• Розовые\n"
        "• Желтые\n"
        "• Зеленые\n"
        "• Синие\n\n"
        "Идеальное решение для фиксации лыж.\n\n"
        "Используйте кнопки ниже для навигации по магазину.\n"
        "Приятных покупок! ❄️"
    )

    await message.answer(welcome_text, reply_markup=get_main_keyboard())


@router.message(Command("admin"))
async def admin_auth(message: Message, state: FSMContext):
    await state.set_state(UserStates.admin_auth)
    await message.answer(
        "🔐 Введите пароль для доступа к админ-панели:",
        reply_markup=get_main_keyboard()
    )


@router.message(UserStates.admin_auth)
async def check_admin_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.set_state(AdminStates.admin_panel)
        await message.answer(
            "✅ Пароль верный! Добро пожаловать в админ-панель.\n\n"
            "Выберите действие:",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer("❌ Неверный пароль! Попробуйте снова.")


@router.callback_query(F.data == "main_menu")
async def return_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.main_menu)
    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    # Если находимся в админ-состояниях, возвращаем в админ-панель
    if current_state and current_state.startswith("AdminStates"):
        await state.set_state(AdminStates.admin_panel)
        await callback.message.edit_text(
            "👑 Админ-панель\n\n"
            "Выберите действие:",
            reply_markup=get_admin_keyboard()
        )
    else:
        # Иначе возвращаем в главное меню
        await state.set_state(UserStates.main_menu)
        await callback.message.edit_text(
            "🏠 Главное меню",
            reply_markup=get_main_keyboard()
        )

    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "🎿 <b>Помощь по магазину липучек для лыж</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/admin - Вход в админ-панель\n\n"

        "<b>Кнопки:</b>\n"
        "🏔️ Каталог - Просмотр всех товаров\n"
        "🛒 Корзина - Просмотр корзины и оформление заказа\n\n"

        "<b>Как купить:</b>\n"
        "1. Нажмите '🏔️ Каталог'\n"
        "2. Выберите товар и количество (кнопки +/-)\n"
        "3. Нажмите '🛒 Корзина'\n"
        "4. Оформите заказ\n\n"

        "🎿 <i>Надежная фиксация для ваших лыж!</i>"
    )

    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "🏔️ Каталог")
async def catalog_handler(message: Message, state: FSMContext):
    from catalog_handlers import show_catalog
    await message.answer(text="""Стоимость при  заказе:

🔸 1 шт. — 650₽  
🔸 2 шт. — 625₽ за штуку  
🔸 3 шт. — 600₽ за штуку  
🔸 4 шт. — 575₽ за штуку  
🔸 От 5 до 10 шт. — 550₽ за штуку  

📦 *Цена указана за 1 единицу в зависимости от общего количества в заказе.*""")
    await show_catalog(message, state)

    # await message.answer_photo(photo="AgACAgIAAxkBAAOxaXvmVGmNtTXt4WylZvx9MhCj1esAAngTaxuncthLy-o5Wrov9KABAAMCAAN5AAM4BA", caption="⬛ Чёрные липучки ⬛")
    # await message.answer(photo="AgACAgIAAxkBAAO3aXvmYsIZUurEc2YPPgABzlk6Vl1AAAJ5E2sbp3LYS1oNUQN_70_lAQADAgADeQADOAQ", caption="🟩 Зелёные липучки 🟩")
    # await message.answer(photo="AgACAgIAAxkBAAO5aXvmaazTMXklSGxnA6rT5xe5jggAAnoTaxuncthLkqK4IV-LBWUBAAMCAAN5AAM4BA", caption="🟦 Синие липучки 🟦")
    # await message.answer(photo="AgACAgIAAxkBAAO1aXvmX6UtPR2RD_EpZfXqqVwbZ8kAAnYTaxuncthLXn2gNqFYu9sBAAMCAAN5AAM4BA", caption="🟨 Жёлтые липучки 🟨")
    # await message.answer(photo="AgACAgIAAxkBAAOzaXvmW1Zm9Zhmb1BgzTSfB81iOCgAAncTaxuncthL2cBKs0K_iQMBAAMCAAN5AAM4BA", caption="🩷 Розовые липучки 🩷")


# @router.message(F.photo)
# async def get_photo_id(message: Message):
#     """Получить file_id отправленного фото"""
#     photo_id = message.photo[-1].file_id
#     await message.answer(
#         f"📸 <b>File ID получен!</b>\n\n"
#         f"<code>{photo_id}</code>\n\n"
#         f"Этот file_id можно использовать в боте.",
#         parse_mode="HTML"
#     )
