from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🏔️ Каталог")],
        [KeyboardButton(text="🛒 Корзина")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_cart_keyboard(has_items: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура корзины с вертикальным расположением кнопок"""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки в зависимости от наличия товаров
    if has_items:
        builder.add(
            InlineKeyboardButton(
                text="✅ Оформить заказ",
                callback_data="place_order"
            ),
            InlineKeyboardButton(
                text="🗑️ Очистить корзину",
                callback_data="clear_cart"
            )
        )

    builder.add(
        InlineKeyboardButton(
            text="🏔️ Вернуться в каталог",
            callback_data="back_to_catalog"
        ),
        InlineKeyboardButton(
            text="🏠 В главное меню",
            callback_data="main_menu"
        )
    )

    # Все кнопки располагаем вертикально (по одной в ряд)
    builder.adjust(1)

    return builder.as_markup()


def get_cart_keyboard_alternative(has_items: bool = True) -> InlineKeyboardMarkup:
    """Альтернативный вариант: все кнопки вертикально (по одной в ряд)"""
    builder = InlineKeyboardBuilder()

    if has_items:
        builder.row(
            InlineKeyboardButton(
                text="✅ Оформить заказ",
                callback_data="place_order"
            ),
            width=1
        )
        builder.row(
            InlineKeyboardButton(
                text="🗑️ Очистить корзину",
                callback_data="clear_cart"
            ),
            width=1
        )

    builder.row(
        InlineKeyboardButton(
            text="🏔️ Вернуться в каталог",
            callback_data="back_to_catalog"
        ),
        width=1
    )
    builder.row(
        InlineKeyboardButton(
            text="🏠 В главное меню",
            callback_data="main_menu"
        ),
        width=1
    )

    return builder.as_markup()


def get_product_keyboard(product_id: int, in_cart: int = 0, available: int = 0) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    row = []

    if in_cart > 0:
        row.append(InlineKeyboardButton(
            text="➖",
            callback_data=f"remove:{product_id}"
        ))
    else:
        row.append(InlineKeyboardButton(
            text="➖",
            callback_data="ignore"
        ))

    row.append(InlineKeyboardButton(
        text=f"{in_cart} шт" if in_cart > 0 else "Добавить",
        callback_data=f"info:{product_id}"
    ))

    if in_cart < available:
        row.append(InlineKeyboardButton(
            text="➕",
            callback_data=f"add:{product_id}"
        ))
    else:
        row.append(InlineKeyboardButton(
            text="➕",
            callback_data="ignore"
        ))

    keyboard.inline_keyboard.append(row)

    return keyboard


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админ-клавиатура с аккуратным расположением"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🏔️ Все товары",
                             callback_data="admin_all_products"),
        InlineKeyboardButton(text="➕ Добавить товар",
                             callback_data="admin_add_product"),
        width=2
    )

    builder.row(
        InlineKeyboardButton(text="✏️ Изменить кол-во",
                             callback_data="admin_edit_product"),
        InlineKeyboardButton(text="💰 Изменить цену",
                             callback_data="admin_edit_price"),
        width=2
    )

    builder.row(
        InlineKeyboardButton(text="🖼️ Изменить фото",
                             callback_data="admin_edit_photo"),
        InlineKeyboardButton(text="🗑️ Удалить товар",
                             callback_data="admin_delete_product"),
        width=2
    )

    builder.row(
        InlineKeyboardButton(text="📊 Все заказы",
                             callback_data="admin_all_orders"),
        InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats"),
        width=2
    )

    builder.row(
        InlineKeyboardButton(text="🏠 В главное меню",
                             callback_data="main_menu"),
        width=1
    )

    return builder.as_markup()


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в админ-панель",
                              callback_data="admin_panel")]
    ])


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")]
    ])


def get_edit_photo_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔄 Заменить фото",
                             callback_data="replace_photo"),
        InlineKeyboardButton(text="❌ Удалить фото",
                             callback_data="remove_photo"),
        width=2
    )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад в админ-панель",
                             callback_data="admin_panel"),
        width=1
    )

    return builder.as_markup()


def get_order_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отмены ввода комментария к заказу"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить оформление",
                              callback_data="cancel_order")]
    ])
