from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    main_menu = State()
    viewing_catalog = State()
    viewing_cart = State()
    order_comment = State()  # <-- ДОБАВЛЕНО НОВОЕ СОСТОЯНИЕ
    admin_auth = State()


class AdminStates(StatesGroup):
    admin_panel = State()
    adding_product_name = State()
    adding_product_quantity = State()
    adding_product_price = State()
    adding_product_photo = State()
    editing_product_id = State()
    editing_product_quantity = State()
    editing_product_price_id = State()
    editing_product_price = State()
    editing_photo_id = State()
    editing_photo = State()
    deleting_product = State()
