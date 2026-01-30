from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards import get_cart_keyboard, get_main_keyboard
from states import UserStates
from database import db
from main import bot

router = Router()

# Функция для форматирования цены с разделителями тысяч


def format_price(price: int) -> str:
    """Форматирует цену в читаемый вид (1 000, 2 500 и т.д.)"""
    return f"{price:,}".replace(",", " ")


# Функция для расчета цены за единицу в зависимости от общего количества
def calculate_unit_price(total_quantity: int) -> int:
    """Рассчитывает цену за единицу в зависимости от общего количества товаров"""
    if total_quantity == 1:
        return 650
    elif total_quantity == 2:
        return 625
    elif total_quantity == 3:
        return 600
    elif total_quantity == 4:
        return 575
    else:  # 5 и более
        return 550


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message, state: FSMContext):
    await state.set_state(UserStates.viewing_cart)

    cart_items = db.get_cart_items(message.from_user.id)

    if not cart_items:
        await message.answer(
            "🛒 <b>Ваша корзина пуста</b>\n\n"
            "Перейдите в каталог, чтобы добавить товары",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        return

    # Используем оптимальную ширину сообщения (примерно 35-40 символов)
    text_lines = [
        "🛒 <b>ВАША КОРЗИНА</b>",
        ""  # Пустая строка для разделения
    ]

    total_price = 0
    total_items = 0

    # Сначала считаем общее количество товаров в корзине
    for item in cart_items:
        total_items += item['quantity']

    # Рассчитываем цену за единицу на основе общего количества
    unit_price = calculate_unit_price(total_items)

    for item in cart_items:
        try:
            quantity = item['quantity']
            item_total = quantity * unit_price
            total_price += item_total

            # Форматируем цены
            price_formatted = format_price(unit_price)
            total_formatted = format_price(item_total)

            # Добавляем товар с компактным форматированием
            text_lines.extend([
                f"<b>🏔️ {item.get('name', 'Без названия')}</b>",
                f"   📦 Количество: <b>{quantity} шт.</b>",
                f"   💰 Цена за шт.: <b>{price_formatted} ₽</b>",
                f"   💰 Сумма: <b>{total_formatted} ₽</b>",
                ""  # Пустая строка между товарами
            ])

        except Exception as e:
            print(f"Ошибка обработки товара в корзине: {e}")
            continue

    # Добавляем итоговую информацию
    total_price_formatted = format_price(total_price)

    text_lines.extend([
        f"💰 <b>Итого к оплате: {total_price_formatted} рублей</b>",
        f"📦 <b>Всего товаров: {total_items} шт.</b>"
    ])

    # Объединяем все строки
    text = "\n".join(text_lines)

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_cart_keyboard(has_items=True)
    )


@router.callback_query(F.data == "place_order")
async def place_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.order_comment)

    order_text = [
        "📝 <b>ОФОРМЛЕНИЕ ЗАКАЗА</b>",
        "",
        "Пожалуйста, напишите свои контактные",
        "данные и адрес для доставки:",
        "",
        "<i>Пример заполнения:</i>",
        "",
        "• Имя и фамилия: Иван Иванов",
        "• Номер телефона: +7 (999) 123-45-67",
        "• Адрес доставки: г. Москва,",
        "  ул. Примерная, д. 1, кв. 1",
        "• Время доставки: 14:00-18:00",
        "• Доп. пожелания: Позвонить",
        "  за 30 мин до доставки",
        "",
        "ℹ️ Эта информация будет отправлена",
        "администратору для обработки заказа."
    ]

    await callback.message.edit_text(
        "\n".join(order_text),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(UserStates.order_comment)
async def handle_order_comment(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.full_name or f"Пользователь {user_id}"
    comment = message.text.strip()

    if not comment:
        error_text = [
            "❌ <b>ВНИМАНИЕ</b>",
            "",
            "Пожалуйста, напишите контактные",
            "данные и адрес для доставки.",
            "",
            "Без этой информации мы не сможем",
            "обработать ваш заказ."
        ]

        await message.answer(
            "\n".join(error_text),
            parse_mode="HTML"
        )
        return

    try:
        # Пробуем создать заказ
        order_id, message_text, cart_items = db.create_order(
            user_id, user_name, comment
        )

        print(
            f"DEBUG: create_order вернул: order_id={order_id}, message_text='{message_text}'")

        if order_id:
            # Формируем сообщение для администратора
            admin_lines = [
                f"🆕 <b>НОВЫЙ ЗАКАЗ #{order_id}!</b>",
                "",
                f"👤 <b>Покупатель:</b> {user_name}",
                f"🆔 <b>ID пользователя:</b> {user_id}",
                f"💰 <b>Сумма заказа:</b> {message_text}",
                "",
                "<b>📦 СОСТАВ ЗАКАЗА:</b>",
                ""
            ]

            for item in cart_items:
                item_total = item['quantity'] * item['price']
                admin_lines.append(
                    f"• {item['name']} ×{item['quantity']} = {format_price(item_total)} руб."
                )

            admin_lines.extend([
                "",
                "<b>📝 КОММЕНТАРИЙ И КОНТАКТЫ:</b>",
                "",
                comment,
                "",
                f"<i>📅 Дата: {message.date.strftime('%Y-%m-%d %H:%M')}</i>"
            ])

            admin_text = "\n".join(admin_lines)

            # Отправляем сообщение администратору
            try:
                await bot.send_message(
                    chat_id=1012701165,
                    text=admin_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Ошибка при отправке уведомления админу: {e}")

            # Сообщение для пользователя
            success_lines = [
                f"🎉 <b>ЗАКАЗ #{order_id} УСПЕШНО ОФОРМЛЕН!</b>",
                "",
                f"👤 <b>Покупатель:</b> {user_name}",
                f"💰 <b>Сумма заказа:</b> {message_text}",
                f"📦 <b>Товаров в заказе:</b> {len(cart_items)}",
                "",
                "✅ <i>Товары успешно зарезервированы.</i>",
                "📞 <i>С вами свяжутся для уточнения</i>",
                "<i>деталей доставки в ближайшее время.</i>",
                "",
                "❄️ <b>Спасибо за покупку!</b>",
                "<b>Приятного катания! ❄️</b>"
            ]

            await message.answer(
                "\n".join(success_lines),
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )

            await state.set_state(UserStates.main_menu)
        else:
            # Показываем более подробную информацию об ошибке
            print(f"ERROR: create_order вернул ошибку: {message_text}")

            error_lines = [
                "❌ <b>ОШИБКА ОФОРМЛЕНИЯ ЗАКАЗА</b>",
                "",
                f"{message_text}",
                "",
                "Возможные причины:",
                "• Корзина пуста",
                "• Товаров недостаточно на складе",
                "• Техническая ошибка",
                "",
                "Попробуйте очистить корзину и добавить",
                "товары заново."
            ]

            await message.answer(
                "\n".join(error_lines),
                parse_mode="HTML",
                reply_markup=get_cart_keyboard(has_items=True)
            )
            await state.set_state(UserStates.viewing_cart)

    except Exception as e:
        # Ловим любые неожиданные исключения
        print(f"CRITICAL ERROR в handle_order_comment: {e}")
        import traceback
        traceback.print_exc()

        error_lines = [
            "❌ <b>КРИТИЧЕСКАЯ ОШИБКА</b>",
            "",
            "Произошла непредвиденная ошибка.",
            "Пожалуйста, попробуйте позже или",
            "обратитесь к администратору.",
            "",
            f"Ошибка: {str(e)[:100]}"
        ]

        await message.answer(
            "\n".join(error_lines),
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        await state.set_state(UserStates.main_menu)


@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery, state: FSMContext):
    success = db.clear_cart(callback.from_user.id)

    if success:
        clear_text = [
            "🗑️ <b>КОРЗИНА ОЧИЩЕНА</b>",
            "",
            "Все товары удалены из корзины.",
            "",
            "Вы можете продолжить покупки",
            "в нашем каталоге."
        ]

        await callback.message.edit_text(
            "\n".join(clear_text),
            parse_mode="HTML",
            reply_markup=get_cart_keyboard(has_items=False)
        )
    else:
        error_text = [
            "❌ <b>ОШИБКА ОЧИСТКИ КОРЗИНЫ</b>",
            "",
            "Не удалось очистить корзину.",
            "",
            "Попробуйте еще раз.",
            "Если проблема повторяется,",
            "обратитесь к администратору."
        ]

        await callback.message.edit_text(
            "\n".join(error_text),
            parse_mode="HTML",
            reply_markup=get_cart_keyboard(has_items=True)
        )
    await callback.answer()
