# Бот для заказа и оплаты пиццы 

## Как установить:

1. Скачайте код
2. Для работы скрипта нужен Python версии не ниже 3.7
3. Установите зависимости, указанные в файле ``requirements.txt`` командой:

   ```pip install -r requirements.txt```
4. Создайте бота и получите его токен, написав в Telegram [BotFather](https://telegram.me/BotFather)
5. Создайте базу данных в [Redis](https://redis.com/)
6. Создайте аккаунт в [Moltin](https://www.elasticpath.com/) и получите client_id и client_secret
7. Получите Yandex-api-ключ, который можно получить в [кабинете разработчика](https://developer.tech.yandex.ru/)
8. Для созданного бота получите Tranzzo-payment-token, снова обратившись к [BotFather](https://telegram.me/BotFather).
9. Создайте в корне проекта файл ``.env`` и укажите в нем все вышеуказанные данные, по образцу:

```
TELEGRAM_TOKEN=токен, полученный в п. 4
DATABASE_HOST=хост базы данных из п. 5 
DATABASE_PORT=порт базы данных из п. 5 
DATABASE_PASSWORD=пароль к базе данных из п. 5 
CLIENT_ID=client_id из п. 6
CLIENT_SECRET=client_secret из п. 6
YANDEX_API_KEY=api_key из п. 7
TRANZZO_PAYMENT_TOKEN=token из п. 8
```

## Начало работы:

Для начала работы необходимо:

1. Создать товары (можно воcпользоваться функцией ``add_products()`` из скрипта ``elasticpath.py``. Пример оформления файла с меню: ``example_menu.json``)
2. Загрузить и привязать фото к товарам (можно воcпользоваться функциями  ``load_file()`` и ``add_file_to_product()`` из скрипта ``elasticpath.py``)
3. Создать pricebook (можно воcпользоваться функцией ``add_pricebook()`` из скрипта ``elasticpath.py``)
4. Добавить цены для товаров в pricebook (можно воcпользоваться функциями  ``create_currency()`` и ``add_price_for_product()`` из скрипта ``elasticpath.py``)
5. Опубликовать каталог с товарами
6. Создать flow c адресами пиццерий и адресами клиентов (можно воcпользоваться функциями  ``create_flow()`` и ``create_field()`` из скрипта ``elasticpath.py``)
7. Создать пиццерии с адресами (можно воcпользоваться функцией ``add_pizzeria_address()`` из скрипта ``elasticpath.py``. Пример оформления файла с меню: ``example_addresses.json``)

## Как запустить
- Telegram-бот запускается командой:

```python3 tg_bot.py```