from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from keyboards import get_admin_keyboard, get_back_to_admin_keyboard, get_cancel_keyboard, get_edit_photo_keyboard
from states import AdminStates
from database import db

router = Router()


@router.callback_query(F.data == "admin_all_products")
async def admin_all_products(callback: CallbackQuery):
    products = db.get_all_products()

    if not products:
        await callback.message.edit_text(
            "🎿 <b>Товаров нет</b>\n\n"
            "Добавьте первый товар через админ-панель",
            parse_mode="HTML",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    text = "🎿 <b>Все товары в магазине:</b>\n\n"

    for product in products:
        text += (
            f"🆔 <b>ID:</b> {product.get('id', 'N/A')}\n"
            f"📦 <b>Название:</b> {product.get('name', 'Без названия')}\n"
            f"🔢 <b>В наличии:</b> {product.get('quantity', 0)} шт.\n"
            f"💰 <b>Цена:</b> {product.get('price', 0)} рублей\n"
            f"📸 <b>Фото:</b> {'Есть' if product.get('photo_id') else 'Нет'}\n"
            f"────────────────────\n"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_back_to_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_product")
async def admin_add_product(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.adding_product_name)
    await callback.message.edit_text(
        "➕ <b>Добавление нового товара</b>\n\n"
        "Отправьте <b>название товара</b>\n\n"
        "Пример: <i>Липучки для лыж фиолетовые</i>\n\n"
        "Или нажмите ❌ для отмены",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.adding_product_name))
async def handle_product_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Название должно содержать минимум 2 символа")
        return

    await state.update_data(product_name=message.text.strip())
    await state.set_state(AdminStates.adding_product_quantity)

    await message.answer(
        "✅ <b>Название сохранено</b>\n\n"
        "Теперь отправьте <b>количество товара</b> (число)\n\n"
        "Пример: <i>10, 25, 100</i>\n\n"
        "Или нажмите ❌ для отмены",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(StateFilter(AdminStates.adding_product_quantity))
async def handle_product_quantity(message: Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
        if quantity < 0:
            await message.answer("❌ Количество не может быть отрицательным")
            return

        await state.update_data(product_quantity=quantity)
        await state.set_state(AdminStates.adding_product_price)

        await message.answer(
            "✅ <b>Количество сохранено</b>\n\n"
            "Теперь отправьте <b>цену товара</b> (число в рублях)\n\n"
            "Пример: <i>500, 750, 1000</i>\n\n"
            "Или нажмите ❌ для отмены",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )

    except ValueError:
        await message.answer("❌ Введите корректное число")


@router.message(StateFilter(AdminStates.adding_product_price))
async def handle_product_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        if price < 0:
            await message.answer("❌ Цена не может быть отрицательной")
            return

        await state.update_data(product_price=price)
        await state.set_state(AdminStates.adding_product_photo)

        await message.answer(
            "✅ <b>Цена сохранена</b>\n\n"
            "Теперь отправьте <b>фото товара</b> (или напишите 'пропустить' чтобы добавить без фото)\n\n"
            "Или нажмите ❌ для отмены",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )

    except ValueError:
        await message.answer("❌ Введите корректное число")


@router.message(StateFilter(AdminStates.adding_product_photo))
async def handle_product_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = ""

    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.lower() == 'пропустить':
        photo_id = ""
    else:
        await message.answer(
            "❌ Отправьте фото или напишите 'пропустить'\n"
            "Или нажмите ❌ для отмены",
            reply_markup=get_cancel_keyboard()
        )
        return

    product_id = db.add_product(
        name=data['product_name'],
        quantity=data['product_quantity'],
        price=data['product_price'],
        photo_id=photo_id
    )

    if product_id:
        await message.answer(
            f"✅ <b>Товар успешно добавлен!</b>\n\n"
            f"🆔 ID: {product_id}\n"
            f"📦 Название: {data['product_name']}\n"
            f"🔢 Количество: {data['product_quantity']} шт.\n"
            f"💰 Цена: {data['product_price']} рублей\n"
            f"📸 Фото: {'Добавлено' if photo_id else 'Нет'}",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "❌ <b>Не удалось добавить товар</b>\n\n"
            "Попробуйте еще раз",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )

    await state.set_state(AdminStates.admin_panel)


@router.callback_query(F.data == "admin_edit_product")
async def admin_edit_product(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.editing_product_id)

    products = db.get_all_products()

    if not products:
        await callback.message.edit_text(
            "❌ <b>Товаров нет для редактирования</b>",
            parse_mode="HTML",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    text = "✏️ <b>Редактирование количества товара</b>\n\n"
    text += "Отправьте <b>ID товара</b> (число):\n\n"
    text += "<b>Доступные товары:</b>\n"

    for product in products[:10]:
        text += f"🆔 {product.get('id', 'N/A')}: {product.get('name', 'Без названия')} - {product.get('quantity', 0)} шт.\n"

    if len(products) > 10:
        text += f"\n... и еще {len(products) - 10} товаров"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

    await callback.answer()


@router.message(StateFilter(AdminStates.editing_product_id))
async def handle_edit_product_id(message: Message, state: FSMContext):
    try:
        product_id = int(message.text.strip())
        product = db.get_product(product_id)

        if not product:
            await message.answer("❌ Товар с таким ID не найден")
            return

        await state.update_data(editing_product_id=product_id)
        await state.set_state(AdminStates.editing_product_quantity)

        await message.answer(
            f"✏️ <b>Редактирование товара</b>\n\n"
            f"🆔 ID: {product_id}\n"
            f"📦 Название: {product.get('name', 'Без названия')}\n"
            f"🔢 Текущее количество: {product.get('quantity', 0)} шт.\n\n"
            f"Отправьте <b>новое количество</b> (число):\n\n"
            f"Или нажмите ❌ для отмены",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )

    except ValueError:
        await message.answer("❌ Введите корректный ID товара (число)")


@router.message(StateFilter(AdminStates.editing_product_quantity))
async def handle_edit_product_quantity(message: Message, state: FSMContext):
    try:
        new_quantity = int(message.text.strip())
        if new_quantity < 0:
            await message.answer("❌ Количество не может быть отрицательным")
            return

        data = await state.get_data()
        product_id = data.get('editing_product_id')

        if not product_id:
            await message.answer("❌ Не найден ID товара для редактирования")
            await state.set_state(AdminStates.admin_panel)
            return

        success = db.update_product_quantity(product_id, new_quantity)

        if success:
            product = db.get_product(product_id)
            await message.answer(
                f"✅ <b>Товар обновлен!</b>\n\n"
                f"🆔 ID: {product_id}\n"
                f"📦 Название: {product.get('name', 'Без названия')}\n"
                f"🔢 Новое количество: {new_quantity} шт.\n"
                f"💰 Цена: {product.get('price', 0)} рублей",
                parse_mode="HTML",
                reply_markup=get_admin_keyboard()
            )
        else:
            await message.answer(
                "❌ <b>Не удалось обновить товар</b>\n\n"
                "Попробуйте еще раз",
                parse_mode="HTML",
                reply_markup=get_admin_keyboard()
            )

        await state.set_state(AdminStates.admin_panel)

    except ValueError:
        await message.answer("❌ Введите корректное число")


@router.callback_query(F.data == "admin_edit_price")
async def admin_edit_price(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.editing_product_price_id)

    products = db.get_all_products()

    if not products:
        await callback.message.edit_text(
            "❌ <b>Товаров нет для изменения цены</b>",
            parse_mode="HTML",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    text = "💰 <b>Изменение цены товара</b>\n\n"
    text += "Отправьте <b>ID товара</b> (число):\n\n"
    text += "<b>Доступные товары:</b>\n"

    for product in products[:10]:
        text += f"🆔 {product.get('id', 'N/A')}: {product.get('name', 'Без названия')} - {product.get('price', 0)} руб.\n"

    if len(products) > 10:
        text += f"\n... и еще {len(products) - 10} товаров"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

    await callback.answer()


@router.message(StateFilter(AdminStates.editing_product_price_id))
async def handle_edit_price_id(message: Message, state: FSMContext):
    try:
        product_id = int(message.text.strip())
        product = db.get_product(product_id)

        if not product:
            await message.answer("❌ Товар с таким ID не найден")
            return

        await state.update_data(editing_product_price_id=product_id)
        await state.set_state(AdminStates.editing_product_price)

        await message.answer(
            f"💰 <b>Изменение цены товара</b>\n\n"
            f"🆔 ID: {product_id}\n"
            f"📦 Название: {product.get('name', 'Без названия')}\n"
            f"💰 Текущая цена: {product.get('price', 0)} рублей\n\n"
            f"Отправьте <b>новую цену</b> (число в рублях):\n\n"
            f"Или нажмите ❌ для отмены",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )

    except ValueError:
        await message.answer("❌ Введите корректный ID товара (число)")


@router.message(StateFilter(AdminStates.editing_product_price))
async def handle_edit_product_price(message: Message, state: FSMContext):
    try:
        new_price = int(message.text.strip())
        if new_price < 0:
            await message.answer("❌ Цена не может быть отрицательной")
            return

        data = await state.get_data()
        product_id = data.get('editing_product_price_id')

        if not product_id:
            await message.answer("❌ Не найден ID товара для изменения цены")
            await state.set_state(AdminStates.admin_panel)
            return

        success = db.update_product_price(product_id, new_price)

        if success:
            product = db.get_product(product_id)
            await message.answer(
                f"✅ <b>Цена товара обновлена!</b>\n\n"
                f"🆔 ID: {product_id}\n"
                f"📦 Название: {product.get('name', 'Без названия')}\n"
                f"💰 Новая цена: {new_price} рублей\n"
                f"🔢 Количество: {product.get('quantity', 0)} шт.",
                parse_mode="HTML",
                reply_markup=get_admin_keyboard()
            )
        else:
            await message.answer(
                "❌ <b>Не удалось обновить цену товара</b>\n\n"
                "Попробуйте еще раз",
                parse_mode="HTML",
                reply_markup=get_admin_keyboard()
            )

        await state.set_state(AdminStates.admin_panel)

    except ValueError:
        await message.answer("❌ Введите корректное число")


@router.callback_query(F.data == "admin_edit_photo")
async def admin_edit_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.editing_photo_id)

    products = db.get_all_products()

    if not products:
        await callback.message.edit_text(
            "❌ <b>Товаров нет для изменения фото</b>",
            parse_mode="HTML",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    text = "🖼️ <b>Изменение фото товара</b>\n\n"
    text += "Отправьте <b>ID товара</b> (число):\n\n"
    text += "<b>Доступные товары:</b>\n"

    for product in products[:10]:
        has_photo = "📸" if product.get('photo_id') else "❌"
        text += f"🆔 {product.get('id', 'N/A')}: {product.get('name', 'Без названия')} {has_photo}\n"

    if len(products) > 10:
        text += f"\n... и еще {len(products) - 10} товаров"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

    await callback.answer()


@router.message(StateFilter(AdminStates.editing_photo_id))
async def handle_edit_photo_id(message: Message, state: FSMContext):
    try:
        product_id = int(message.text.strip())
        product = db.get_product(product_id)

        if not product:
            await message.answer("❌ Товар с таким ID не найден")
            return

        await state.update_data(editing_photo_id=product_id)
        await state.set_state(AdminStates.editing_photo)

        has_photo = "📸 (Есть фото)" if product.get(
            'photo_id') else "❌ (Нет фото)"
        await message.answer(
            f"🖼️ <b>Изменение фото товара</b>\n\n"
            f"🆔 ID: {product_id}\n"
            f"📦 Название: {product.get('name', 'Без названия')}\n"
            f"📷 Статус фото: {has_photo}\n\n"
            f"Отправьте <b>новое фото товара</b>\n"
            f"Или нажмите кнопку ниже для других действий",
            parse_mode="HTML",
            reply_markup=get_edit_photo_keyboard()
        )

    except ValueError:
        await message.answer("❌ Введите корректный ID товара (число)")


@router.callback_query(F.data == "replace_photo", StateFilter(AdminStates.editing_photo))
async def handle_replace_photo(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🖼️ <b>Замена фото товара</b>\n\n"
        "Отправьте новое фото товара\n"
        "Или нажмите ❌ для отмены",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "remove_photo", StateFilter(AdminStates.editing_photo))
async def handle_remove_photo(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('editing_photo_id')

    if not product_id:
        await callback.answer("❌ Не найден ID товара")
        return

    success = db.update_product_photo(product_id, "")

    if success:
        await callback.message.edit_text(
            f"✅ <b>Фото товара удалено!</b>\n\n"
            f"🆔 ID: {product_id}\n"
            f"📦 Товар теперь без фото",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )
    else:
        await callback.message.edit_text(
            "❌ <b>Не удалось удалить фото</b>\n\n"
            "Попробуйте еще раз",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )

    await state.set_state(AdminStates.admin_panel)
    await callback.answer()


@router.message(StateFilter(AdminStates.editing_photo))
async def handle_new_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('editing_photo_id')

    if not product_id:
        await message.answer("❌ Не найден ID товара")
        await state.set_state(AdminStates.admin_panel)
        return

    if not message.photo:
        await message.answer("❌ Отправьте фото товара")
        return

    photo_id = message.photo[-1].file_id
    success = db.update_product_photo(product_id, photo_id)

    if success:
        await message.answer(
            f"✅ <b>Фото товара обновлено!</b>\n\n"
            f"🆔 ID: {product_id}\n"
            f"📦 Фото успешно сохранено",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "❌ <b>Не удалось обновить фото</b>\n\n"
            "Попробуйте еще раз",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )

    await state.set_state(AdminStates.admin_panel)


@router.callback_query(F.data == "admin_delete_product")
async def admin_delete_product(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.deleting_product)

    products = db.get_all_products()

    if not products:
        await callback.message.edit_text(
            "❌ <b>Товаров нет для удаления</b>",
            parse_mode="HTML",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    text = "🗑️ <b>Удаление товара</b>\n\n"
    text += "Отправьте <b>ID товара</b> для удаления (число):\n\n"
    text += "<b>Доступные товары:</b>\n"

    for product in products[:10]:
        text += f"🆔 {product.get('id', 'N/A')}: {product.get('name', 'Без названия')}\n"

    if len(products) > 10:
        text += f"\n... и еще {len(products) - 10} товаров"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

    await callback.answer()


@router.message(StateFilter(AdminStates.deleting_product))
async def handle_delete_product(message: Message, state: FSMContext):
    try:
        product_id = int(message.text.strip())
        product = db.get_product(product_id)

        if not product:
            await message.answer("❌ Товар с таким ID не найден")
            return

        success = db.delete_product(product_id)

        if success:
            await message.answer(
                f"✅ <b>Товар удален!</b>\n\n"
                f"🆔 ID: {product_id}\n"
                f"📦 Название: {product.get('name', 'Без названия')}",
                parse_mode="HTML",
                reply_markup=get_admin_keyboard()
            )
        else:
            await message.answer(
                "❌ <b>Не удалось удалить товар</b>\n\n"
                "Возможно, товар используется в заказах",
                parse_mode="HTML",
                reply_markup=get_admin_keyboard()
            )

        await state.set_state(AdminStates.admin_panel)

    except ValueError:
        await message.answer("❌ Введите корректный ID товара (число)")


@router.callback_query(F.data == "admin_all_orders")
async def admin_all_orders(callback: CallbackQuery):
    orders = db.get_all_orders()

    if not orders:
        await callback.message.edit_text(
            "📊 <b>Заказов нет</b>",
            parse_mode="HTML",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    text = "📊 <b>Все заказы:</b>\n\n"

    for order in orders[:10]:  # Показываем только 10 последних заказов
        comment = order.get('comment', '')
        comment_preview = comment[:50] + \
            "..." if len(comment) > 50 else comment

        text += (
            f"🆔 <b>Заказ #{order.get('id', 'N/A')}</b>\n"
            f"👤 Покупатель: {order.get('user_name', 'Неизвестно')}\n"
            f"💰 Сумма: {order.get('total_amount', 0)} рублей\n"
            f"📦 Товары: {order.get('items', 'Не указаны')}\n"
        )

        if comment:
            text += f"📝 Комментарий: {comment_preview}\n"

        text += f"📅 Дата: {order.get('created_at', 'Неизвестно')}\n"
        text += f"────────────────────\n"

    if len(orders) > 10:
        text += f"\n... и еще {len(orders) - 10} заказов"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_back_to_admin_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    products = db.get_all_products()
    orders = db.get_all_orders()

    total_products = len(products)
    total_stock = sum(p.get('quantity', 0) for p in products)
    total_orders = len(orders)
    total_revenue = sum(o.get('total_amount', 0) for o in orders)

    low_stock = [p for p in products if p.get('quantity', 0) <= 3]

    text = (
        "📈 <b>Статистика магазина</b>\n\n"
        f"🎿 <b>Товаров в каталоге:</b> {total_products} шт.\n"
        f"📦 <b>Общий остаток на складе:</b> {total_stock} шт.\n"
        f"📊 <b>Всего заказов:</b> {total_orders} шт.\n"
        f"💰 <b>Общая выручка:</b> {total_revenue} рублей\n\n"
    )

    if low_stock:
        text += "⚠️ <b>Товары с малым остатком (≤3 шт.):</b>\n"
        for product in low_stock[:5]:
            text += f"  • {product.get('name', 'Без названия')}: {product.get('quantity', 0)} шт.\n"

        if len(low_stock) > 5:
            text += f"  ... и еще {len(low_stock) - 5} товаров\n"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_back_to_admin_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data == "admin_panel")
async def return_to_admin(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.admin_panel)
    await callback.message.edit_text(
        "👑 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()
