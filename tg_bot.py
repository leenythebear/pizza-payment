import functools
from textwrap import dedent

from dotenv import load_dotenv
import os

import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, LabeledPrice

from telegram.ext import Filters, Updater, PreCheckoutQueryHandler
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from validate_email import validate_email

from elasticpath import (
    get_token,
    get_products,
    get_product_by_id,
    get_cart,
    get_product_image,
    add_product_to_cart,
    get_carts_sum,
    delete_product_from_cart,
    create_customer,
    get_all_pizzerias, add_customer_address, get_entries_by_id, delete_all_cart_products,
)

from geocoder import get_coordinates, get_distance

import logging

_database = None


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def create_products_buttons(token):
    """
    Функция для создания кнопок меню с товарами
    """
    products = get_products(token)["data"]
    keyboard = [
        [
            InlineKeyboardButton(
                product["attributes"]["name"], callback_data=product["id"]
            )
        ]
        for product in products
    ]
    keyboard.append([InlineKeyboardButton("Корзина", callback_data="cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def start(bot, update, token):
    reply_markup = create_products_buttons(token)
    if update.callback_query:
        bot.send_message(
            chat_id=update.callback_query.message["chat"]["id"],
            text="Добро пожаловать! Выберите пиццу для заказа:",
            reply_markup=reply_markup,
        )
    elif update.message:
        update.message.reply_text("Добро пожаловать! Выберите пиццу для заказа:", reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update, token):
    query = update.callback_query
    if query.data == "cart":
        handle_cart(bot, update, token)
        return "HANDLE_CART"
    product_id = update.callback_query.data
    product = get_product_by_id(product_id, token)

    product_name = product["attributes"]["name"]
    product_price = product["meta"]["display_price"]["without_tax"]["formatted"]
    product_description = product["attributes"]["description"]

    image_id = product["relationships"]["main_image"]["data"]["id"]
    image_url = get_product_image(token, image_id)["data"]["link"]["href"]

    message = f"{product_name}\n\n{product_price}\n\n{product_description}"
    keyboard = [
        [InlineKeyboardButton("Добавить в корзину", callback_data=f"add_to_cart, {product_id}")],
        [InlineKeyboardButton("Назад", callback_data="start")],
        [InlineKeyboardButton("Перейти в корзину", callback_data="cart")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard, n_cols=3)
    bot.send_photo(
        chat_id=query.message.chat_id,
        photo=image_url,
        caption=message,
        reply_markup=reply_markup,
    )
    return "HANDLE_DESCRIPTION"


def handle_description(bot, update, token):
    query = update.callback_query
    chat_id = query["message"]["chat"]["id"]
    if query.data == "start":
        start(bot, update, token)
        return "HANDLE_MENU"
    elif query.data == "cart":
        handle_cart(bot, update, token)
        return "HANDLE_CART"
    else:
        split_query = query.data.split(', ')
        if split_query[0] == "add_to_cart":
            product_id = split_query[1]
            add_product_to_cart(chat_id, token, product_id)
            bot.answer_callback_query(
                callback_query_id=query.id,
                text="Товар добавлен в корзину",
                show_alert=False,
            )
        return "HANDLE_DESCRIPTION"


def handle_cart(bot, update, token):
    query = update.callback_query
    chat_id = query["message"]["chat"]["id"]
    if query.data == "cart":
        products_cart = get_cart(token, chat_id)
        carts_sum = get_carts_sum(token, chat_id)
        message = ""
        for product in products_cart:
            cart_description = f"""\
                                   {product["name"]}
                                   {product["description"]} 

                                   {product["quantity"]} шт.  
                                   Цена за штуку: {product["meta"]["display_price"]["without_tax"]["unit"]["formatted"]}
                                   ______________________________
                                    
                                    """
            message += dedent(cart_description)
        sum_message = f"""\
                            Итого к оплате: {carts_sum}
                                
                        """
        message += dedent(sum_message)
        keyboard = [
            [
                InlineKeyboardButton(
                    f'Удалить {product["name"]}',
                    callback_data=f'delete,{product["id"]}',
                )
            ]
            for product in products_cart
        ]
        if products_cart:
            keyboard.append(
                [InlineKeyboardButton("Оформить заказ", callback_data="order")]
            )
        keyboard.append([InlineKeyboardButton("Меню", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(
            chat_id=chat_id, text=message, reply_markup=reply_markup
        )
        return "HANDLE_DESCRIPTION"
    elif query.data == "start":
        start(bot, update, token)
        return "HANDLE_MENU"
    elif query.data.startswith("delete"):
        product_id = query.data.split(",")[1]
        delete_product_from_cart(token, product_id, chat_id)
        bot.answer_callback_query(
            callback_query_id=query.id,
            text="Товар удален из корзины",
            show_alert=False,
        )
        products_cart = get_cart(token, chat_id)
        carts_sum = get_carts_sum(token, chat_id)
        message = ""
        for product in products_cart:
            cart_description = f"""\
                                   {product["name"]}
                                   {product["description"]} 

                                   {product["quantity"]} шт.  
                                   Цена за штуку: {product["meta"]["display_price"]["without_tax"]["unit"]["formatted"]}
                                   ______________________________
                                    
                                    """
            message += dedent(cart_description)
        sum_message = f"""\
                            Итого к оплате: {carts_sum}
                                
                        """
        message += dedent(sum_message)
        keyboard = [
            [
                InlineKeyboardButton(
                    f'Удалить {product["name"]}',
                    callback_data=f'delete,{product["id"]}',
                )
            ]
            for product in products_cart
        ]
        if products_cart:
            keyboard.append(
                [InlineKeyboardButton("Оплата", callback_data="pay")]
            )
        keyboard.append([InlineKeyboardButton("Меню", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(
            chat_id=chat_id, text=message, reply_markup=reply_markup
        )
        return "HANDLE_DESCRIPTION"
    elif query.data == "order":
        bot.send_message(chat_id=chat_id, text="Введите Ваш email:")
        return "WAITING_EMAIL"


def waiting_email(bot, update, token):
    email = update.message.text
    chat_id = update.message.chat_id
    is_valid = validate_email(email=email)
    if is_valid:
        create_customer(token, email, chat_id)
        message_keyboard = [
            [
                KeyboardButton('Вернуться в главное меню'),
                KeyboardButton('Отправить геолокацию', request_location=True)
            ]
        ]
        markup = ReplyKeyboardMarkup(message_keyboard, one_time_keyboard=False, resize_keyboard=True)

        bot.send_message(chat_id=chat_id, text="Пришлите, пожалуйста, Ваш адрес: текстом или с помощью геолокации",
                         reply_markup=markup
                         )
        return "WAITING_LOCATION"
    else:
        bot.send_message(chat_id=chat_id, text="Введите корректный email")
        return "WAITING_EMAIL"


def handle_waiting(bot, update, api_key, token, db):
    chat_id = update.message.chat_id
    if update.message.location:
        coordinates = (update.message.location.latitude, update.message.location.longitude)
    elif update.message.text:
        user_pos = update.message.text
        coordinates = get_coordinates(api_key, user_pos)
    if not coordinates:
        text = 'Не могу распознать этот адрес!'
        update.effective_message.reply_text(text=text)
        return "WAITING_LOCATION"
    latitude, longitude = coordinates
    customer_address_id = (add_customer_address(token, chat_id, latitude, longitude)).get("data").get("id")

    distances = {}
    all_pizzerias = get_all_pizzerias(token)
    for pizzeria in all_pizzerias['data']:
        pizzeria_coords = (pizzeria['latitude'], pizzeria['longitude'])
        distance_to_pizzeria = get_distance(coordinates, pizzeria_coords)
        distances[distance_to_pizzeria] = (pizzeria['address'], pizzeria['id'])
    min_distance = min(distances.items(), key=lambda x: x[0])

    distance_to_pizzeria = min_distance[0]
    pizzeria_address = min_distance[1][0]
    pizzeria_id = min_distance[1][1]

    db.set(f'{chat_id}_order', f'{customer_address_id}${pizzeria_id}')

    keyboard = [
        [InlineKeyboardButton("Доставка", callback_data="delivery")],
        [InlineKeyboardButton("Самовывоз", callback_data="pickup")]
    ]
    if min_distance[0] > 20.0:
        text = dedent(f"""\
        Простите, но так далеко мы пиццу не доставим.
        Ближайшая пиццерия аж в {distance_to_pizzeria} километрах от Вас.
        """)
        _ = keyboard.pop(0)

    elif 5 < min_distance[0] <= 20:
        text = "Стоимость доставки к Вам составит 300 рублей"

    elif min_distance[0] <= 5:
        text = "Стоимость доставки к Вам составит 100 рублей"
    else:
        text = dedent(f"""\
        Может заберёте пиццу из нашей пиццерии неподалёку? 
        Она всего в {distance_to_pizzeria} километрах от Вас!
        Вот её адрес: {pizzeria_address}
        А можем и бесплатно доставить, нам не сложно 😊
        """)

    reply_markup = InlineKeyboardMarkup(keyboard, n_cols=2)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    return "WAITING_PIZZA"


def handle_delivery(bot, update, token, db):
    query = update.callback_query
    order_type = query['data']
    customer_chat_id = query["message"]["chat"]["id"]

    entry_ids = db.get(f'{customer_chat_id}_order').decode('utf-8')
    customer_address_id, pizzeria_id = entry_ids.split("$")

    pizzeria = get_entries_by_id(token, entry_id=pizzeria_id, flow_slug='pizzeri-aaddresses')

    if order_type == 'delivery':
        keyboard = [[InlineKeyboardButton('Оплатить заказ', callback_data='payment')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=customer_chat_id, text="Оплатите заказ и ожидайте доставки:", reply_markup=reply_markup)
        return "WAITING_PAYMENT"
    elif order_type == "pickup":
        message = f"Вы можете забрать по адресу: {pizzeria.get('data').get('address')}. До свидания!"
        bot.send_message(chat_id=customer_chat_id, text=message)


def pay_for_pizza(bot, provider_token, db, chat_id):
    title = "Payment Example"
    description = "Payment Example using python-telegram-bot"
    payload = "Custom-Payload"
    start_parameter = "test-payment"
    currency = 'RUB'
    price = (db.json().get(f'{chat_id}_menu')['price']).split(' ')[0]
    prices = [LabeledPrice('Test', int(float(price)) * 100)]
    bot.sendInvoice(chat_id, title, description, payload, provider_token, start_parameter, currency, prices)


def precheckout_callback(bot, update):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=False,
                                      error_message="Something went wrong...")
    else:
        bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)


def successful_payment_callback(bot, update):
    update.message.reply_text("Thank you for your payment!")


def send_delivery_notification(bot, chat_id):
    message = dedent(
        '''
        Приятного аппетита! *место для рекламы*\n
        *сообщение что делать если пицца не пришла*
        '''
    )
    bot.send_message(chat_id=chat_id, text=message)


def handle_payment(bot, update, provider_token, db, token):
    query = update.callback_query['data']
    chat_id = update.callback_query['message']['chat']['id']
    if query == 'payment':
        pay_for_pizza(bot, provider_token, db, chat_id)
        send_message_to_courier(bot, update, db, chat_id, token)
        delete_all_cart_products(token, chat_id)
        job.run_once(send_delivery_notification(bot, chat_id), 60)


def send_message_to_courier(bot, update, db, chat_id, token):
    order = get_cart(token, chat_id)
    carts_sum = get_carts_sum(token, chat_id)

    entry_ids = db.get(f'{chat_id}_order').decode('utf-8')
    customer_address_id, pizzeria_id = entry_ids.split("$")

    courier_telegram_id = (get_entries_by_id(token, entry_id=pizzeria_id, flow_slug='pizzeri-aaddresses')).get('data').get('courier-telegram-id')
    customer_address = get_entries_by_id(token, entry_id=customer_address_id, flow_slug='customer-address')

    longitude = customer_address.get('data').get('longitude')
    latitude = customer_address.get('data').get('latitude')

    message = ''
    for product in order:
        cart_description = f"""\
                               {product["name"]}
                               {product["description"]}

                               {product["quantity"]} шт.
                               Цена за штуку: {product["meta"]["display_price"]["without_tax"]["unit"]["formatted"]}
                               ______________________________

                                """
        message += dedent(cart_description)
    sum_message = f"""\
                        Итого к оплате: {carts_sum}

                    """
    message += dedent(sum_message)
    db.json().set(f'{chat_id}_menu', '$', {'menu': message, 'price': carts_sum})
    bot.send_message(chat_id=courier_telegram_id, text=message)
    bot.send_location(chat_id=courier_telegram_id, latitude=latitude, longitude=longitude)


def get_database_connection(host, port, password):
    global _database
    if _database is None:
        _database = redis.Redis(host=host, port=port, password=password)
    return _database


def handle_users_reply(
    bot, update, host, port, password, client_id, client_secret, provider_token, yandex_api_key
):
    db = get_database_connection(host, port, password)
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    elif update.message.location:
        user_reply = update.message.location
        chat_id = update.message.chat_id
    elif update.pre_checkout_query:
        user_reply = update.pre_checkout_query
        chat_id = update.message.chat_id
    else:
        return
    if user_reply == "/start":
        user_state = "START"
    else:
        user_state = db.get(chat_id).decode("utf-8")
    token = get_token(client_id, client_secret, db)
    states_functions = {
        "START": functools.partial(start, token=token),
        "HANDLE_MENU": functools.partial(handle_menu, token=token),
        "HANDLE_DESCRIPTION": functools.partial(
            handle_description, token=token
        ),
        "HANDLE_CART": functools.partial(handle_cart, token=token),
        "WAITING_EMAIL": functools.partial(waiting_email, token=token),
        "WAITING_LOCATION": functools.partial(handle_waiting, api_key=yandex_api_key, token=token, db=db),
        "WAITING_PIZZA": functools.partial(handle_delivery, token=token, db=db),
        "WAITING_PAYMENT": functools.partial(handle_payment, provider_token=provider_token, db=db, token=token),
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        logging.error(err)


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")

    provider_token = os.getenv("TRANZZO_PAYMENT_TOKEN")

    client_id = os.environ["CLIENT_ID"]
    client_secret = os.environ["CLIENT_SECRET"]

    db_host = os.environ["DATABASE_HOST"]
    db_port = os.environ["DATABASE_PORT"]
    db_password = os.environ["DATABASE_PASSWORD"]

    yandex_api_key = os.getenv("YANDEX_API_KEY")

    partial_handle_users_reply = functools.partial(
        handle_users_reply,
        host=db_host,
        port=db_port,
        password=db_password,
        client_id=client_id,
        client_secret=client_secret,
        provider_token=provider_token,
        yandex_api_key=yandex_api_key

    )

    updater = Updater(token)
    job = updater.job_queue
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))
    dispatcher.add_handler(MessageHandler(Filters.location, partial_handle_users_reply))
    dispatcher.add_handler(CallbackQueryHandler(partial_handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, partial_handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", partial_handle_users_reply))
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    dispatcher.add_error_handler(error)

    updater.start_polling()
