from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards import get_product_keyboard
from states import UserStates
from database import db

router = Router()


async def show_catalog(message: Message, state: FSMContext):
    await state.set_state(UserStates.viewing_catalog)

    products = db.get_all_products()  # Теперь этот метод существует!

    if not products:
        await message.answer("😔 Каталог пуст. Скоро появятся новые товары!")
        return
    # ... остальной код

    intro_message = (
        "🎿 <b>Каталог липучек для лыж</b>\n\n"
        "Выберите цвет и количество:\n"
        "➖ - Уменьшить количество\n"
        "➕ - Увеличить количество\n\n"
        "Все липучки по одной цене - 650 рублей!"
    )

    await message.answer(intro_message, parse_mode="HTML")

    for product in products:
        cart_items = db.get_cart_items(message.from_user.id)
        in_cart = 0
        for item in cart_items:
            if item['product_id'] == product['id']:
                in_cart = item['quantity']
                break

        caption = (
            f"🎿 <b>{product.get('name', 'Без названия')}</b>\n"
            f"📦 В наличии: <b>{product.get('quantity', 0)} шт.</b>\n"
            f"💰 Цена: <b>{product.get('price', 0)} рублей</b>\n\n"
            f"🛒 В корзине: <b>{in_cart} шт.</b>"
        )

        keyboard = get_product_keyboard(
            product['id'],
            in_cart,
            product.get('quantity', 0)
        )

        # Получаем photo_id из базы данных
        photo_id = product.get('photo_id')

        # Проверяем, есть ли photo_id и не пустой ли он
        if photo_id and photo_id.strip():
            try:
                # Отправляем фото с подписью
                await message.answer_photo(
                    photo=photo_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                continue
            except Exception as e:
                print(
                    f"Ошибка при отправке фото товара {product['id']} ({product['name']}): {e}")
                print(f"Photo ID был: {photo_id}")
                # Если не получилось отправить фото, отправляем текст с информацией
                await message.answer(
                    f"❌ Не удалось загрузить фото для товара: {product['name']}\n\n" + caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                continue

        # Если фото нет, отправляем только текст
        await message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    try:
        product_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        success, message_text = db.add_to_cart(user_id, product_id)

        if success:
            product = db.get_product(product_id)
            if not product:
                await callback.answer("❌ Товар не найден", show_alert=True)
                return

            cart_items = db.get_cart_items(user_id)
            in_cart = 0
            for item in cart_items:
                if item['product_id'] == product_id:
                    in_cart = item['quantity']
                    break

            caption = (
                f"🎿 <b>{product.get('name', 'Без названия')}</b>\n"
                f"📦 В наличии: <b>{product.get('quantity', 0)} шт.</b>\n"
                f"💰 Цена: <b>{product.get('price', 0)} рублей</b>\n\n"
                f"🛒 В корзине: <b>{in_cart} шт.</b>"
            )

            keyboard = get_product_keyboard(
                product_id,
                in_cart,
                product.get('quantity', 0)
            )

            try:
                if callback.message.photo:
                    await callback.message.edit_caption(
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.edit_text(
                        caption,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            except Exception as e:
                print(f"Ошибка при редактировании сообщения: {e}")
                # Пытаемся отправить новое сообщение
                await callback.message.answer(
                    f"✅ Товар добавлен! Теперь в корзине: {in_cart} шт.",
                    show_alert=False
                )

            await callback.answer(f"✅ Добавлено в корзину ({in_cart} шт.)")
        else:
            await callback.answer(f"❌ {message_text}", show_alert=True)

    except Exception as e:
        print(f"Ошибка в add_to_cart: {e}")
        await callback.answer("❌ Ошибка при добавлении в корзину", show_alert=True)


@router.callback_query(F.data.startswith("remove:"))
async def remove_from_cart(callback: CallbackQuery):
    try:
        product_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        success, message_text = db.remove_from_cart(user_id, product_id)

        if success:
            product = db.get_product(product_id)
            if product:
                cart_items = db.get_cart_items(user_id)
                in_cart = 0
                for item in cart_items:
                    if item['product_id'] == product_id:
                        in_cart = item['quantity']
                        break

                caption = (
                    f"🎿 <b>{product.get('name', 'Без названия')}</b>\n"
                    f"📦 В наличии: <b>{product.get('quantity', 0)} шт.</b>\n"
                    f"💰 Цена: <b>{product.get('price', 0)} рублей</b>\n\n"
                    f"🛒 В корзине: <b>{in_cart} шт.</b>"
                )

                keyboard = get_product_keyboard(
                    product_id,
                    in_cart,
                    product.get('quantity', 0)
                )

                try:
                    if callback.message.photo:
                        await callback.message.edit_caption(
                            caption=caption,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                    else:
                        await callback.message.edit_text(
                            caption,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                except Exception as e:
                    print(f"Ошибка при редактировании сообщения: {e}")
                    await callback.message.answer(
                        f"🗑️ {message_text}",
                        show_alert=False
                    )

            await callback.answer(f"🗑️ {message_text}")
        else:
            await callback.answer(f"❌ {message_text}", show_alert=True)

    except Exception as e:
        print(f"Ошибка в remove_from_cart: {e}")
        await callback.answer("❌ Ошибка при удалении из корзины", show_alert=True)


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, state: FSMContext):
    await show_catalog(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def handle_ignore(callback: CallbackQuery):
    await callback.answer()
