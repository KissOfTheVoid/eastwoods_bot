import logging

import pandas as pd
import yaml
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext, Filters

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFOб )
logger = logging.getLogger(__name__)

# Загрузка данных из YAML-файла
with open('config.yaml', 'r') as yaml_file:
    config_data = yaml.safe_load(yaml_file)

# Получение токена бота и идентификатора чата с баристой
TOKEN = config_data['telegram_bot']['token']

# Шаги разговора
SELECT_DRINK_TYPE, SELECT_DRINK, SELECT_MILK, APPROVE_SYRUP, SELECT_SYRUP_1, SELECT_SYRUP_2, SELECT_VOLUME, SELECT_TEMPERATURE, CONFIRM_ORDER = range(9)

user_orders = {}


# Загрузка данных из Excel файла
def load_menu_data(file_path):
    drinks = pd.read_excel(file_path, sheet_name='Напитки').set_index('Название').to_dict(orient='index')
    milk = pd.read_excel(file_path, sheet_name='Молоко')
    syrups = pd.read_excel(file_path, sheet_name='Сиропы')
    return drinks, milk['Название'].tolist(), syrups['Название'].tolist()


def available_volumes(drink_name):
    volumes = []
    for volume, status in drinks[drink_name].items():
        if volume != 'Молоко' and volume != 'Тип напитка' and status == '+':
            volumes.append(volume)
    return volumes


def get_unique_drink_types(drinks):
    # Создаем список, в который будем добавлять уникальные значения
    unique_types = []

    # Проходим по каждому напитку в словаре drinks
    for drink, properties in drinks.items():
        drink_type = properties.get('Тип напитка', None)

        # Проверяем, что значение 'Тип напитка' не пустое и не содержится уже в списке unique_types
        if drink_type and drink_type not in unique_types:
            unique_types.append(drink_type)

    return unique_types


def get_drinks_by_type(drinks, drink_type):
    matching_drinks = []
    for drink, properties in drinks.items():
        if properties.get('Тип напитка', None) == drink_type:
            matching_drinks.append(drink)
    return matching_drinks


drinks, milks, syrups = load_menu_data('/Users/walker/Downloads/Eastwood_done.xlsx')

drink_types = get_unique_drink_types(drinks)


# Функции для команд
def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    context.user_data['user_messages'] = []  # Инициализируем список сообщений пользователя

    context.user_data['drink'] = None
    context.user_data['milk'] = None
    context.user_data['syrup'] = None
    context.user_data['volume'] = None
    context.user_data['temperature'] = None

    keyboard = [[InlineKeyboardButton(drink_type, callback_data=f'drink_{drink_type}')] for drink_type in drink_types]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Добро пожаловать в нашу кофейню! Пожалуйста, выберите тип напитка:',
                              reply_markup=reply_markup)
    logger.info(f"Пользователь {update.effective_user.username} выбрал команду /start")

    return SELECT_DRINK_TYPE


def reset_order(update: Update, context: CallbackContext) -> int:
    context.user_data['drink'] = None  # Обнуляем выбранный напиток
    context.user_data['milk'] = None  # Обнуляем выбранное молоко
    context.user_data['syrup'] = None  # Обнуляем выбранный сироп
    context.user_data['volume'] = None  # Обнуляем выбранный объем
    context.user_data['temperature'] = None  # Обнуляем выбранную температуру

    return SELECT_DRINK


# Определение обработчиков для каждого шага
def drink_type(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()

    desired_type = query.data.split('_')[1]
    matched_drinks = get_drinks_by_type(drinks, desired_type)

    keyboard = [[InlineKeyboardButton(drink, callback_data=f'drink_{drink}')] for drink in matched_drinks]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберете напиток:", reply_markup=reply_markup)
    return SELECT_DRINK


def drink(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    context.user_data['drink'] = query.data.split('_')[1]  # Сохраняем выбранный напиток

    # Логируем нажатие кнопки
    logger.info(f"Пользователь {user_update.effective_user.username} выбрал напиток: {context.user_data['drink']}")
    if drinks[context.user_data['drink']]['Молоко'] == '-' and drinks[context.user_data['drink']]['Тип напитка'] == "Кофе":
        keyboard = [[InlineKeyboardButton(syrup, callback_data=f'syrup_{syrup}') for syrup in syrups]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data['milk'] = 'Нет'

        syrup_amount = ["Не хочу", "Один, пожалуйста", "Давайте два"]
        keyboard = [[InlineKeyboardButton(amount, callback_data=f'syrup_{amount}')] for amount in syrup_amount]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Хотите сироп?", reply_markup=reply_markup)

        return APPROVE_SYRUP

    else:
        keyboard = [[InlineKeyboardButton(milk, callback_data=f'milk_{milk}')] for milk in milks]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Выберите тип молока:", reply_markup=reply_markup)

        return SELECT_MILK


def milk(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    context.user_data['milk'] = query.data.split('_')[1]  # Сохраняем выбранное молоко

    # Логируем нажатие кнопки
    logger.info(f"Пользователь {user_update.effective_user.username} выбрал тип молока: {context.user_data['milk']}")
    syrup_amount = ["Не хочу", "Один, пожалуйста", "Давайте два"]
    keyboard = [[InlineKeyboardButton(amount, callback_data=f'syrup_{amount}')] for amount in syrup_amount]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Хотите сироп?", reply_markup=reply_markup)
    return APPROVE_SYRUP


def approve_syrup(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    syrup_amount = query.data.split('_')[1]
    if syrup_amount == "Не хочу":
        context.user_data['syrup_1'] = 'Нет'
        context.user_data['syrup_2'] = 'Нет'
        logger.info(f"Пользователь {user_update.effective_user.username} от сиропа")
        volumes = available_volumes(context.user_data['drink'])
        keyboard = [[InlineKeyboardButton(volume, callback_data=f'volume_{volume}')] for volume in volumes]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Выберите объем:", reply_markup=reply_markup)
        return SELECT_VOLUME
    if syrup_amount == "Один, пожалуйста":
        context.user_data['syrup_1'] = 'Нет'
        keyboard = [[InlineKeyboardButton(syrup, callback_data=f'syrup_{syrup}')] for syrup in syrups]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Выберите сироп:", reply_markup=reply_markup)
        return SELECT_SYRUP_2
    if syrup_amount == "Давайте два":
        keyboard = [[InlineKeyboardButton(syrup, callback_data=f'syrup_{syrup}')] for syrup in syrups]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Выберите сироп:", reply_markup=reply_markup)
        return SELECT_SYRUP_1


def syrup_1(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()

    context.user_data['syrup_1'] = query.data.split('_')[1] # Сохраняем выбранное молоко

    # Логируем нажатие кнопки
    logger.info(f"Пользователь {user_update.effective_user.username} выбрал сироп: {context.user_data['syrup_1']}")

    keyboard = [[InlineKeyboardButton(syrup, callback_data=f'syrup_{syrup}')] for syrup in syrups]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите сироп :) ", reply_markup=reply_markup)

    return SELECT_SYRUP_2


def syrup_2(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    context.user_data['syrup_2'] = query.data.split('_')[1]  # Сохраняем выбранный сироп

    # Логируем нажатие кнопки
    logger.info(f"Пользователь {user_update.effective_user.username} выбрал сироп: {context.user_data['syrup_2']}")
    volumes = available_volumes(context.user_data['drink'])
    keyboard = [[InlineKeyboardButton(volume, callback_data=f'volume_{volume}')] for volume in volumes]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите объем:", reply_markup=reply_markup)

    return SELECT_VOLUME


def volume(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    context.user_data['volume'] = query.data.split('_')[1]  # Сохраняем выбранный объем

    # Логируем нажатие кнопки
    logger.info(f"Пользователь {user_update.effective_user.username} выбрал объем: {context.user_data['volume']}")
    temperatures = ['Холодный', 'Горячий']
    keyboard = [[InlineKeyboardButton(temp, callback_data=f'temperature_{temp}') for temp in temperatures]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите температуру напитка:", reply_markup=reply_markup)

    return SELECT_TEMPERATURE


def temperature(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    context.user_data['temperature'] = query.data.split('_')[1]  # Сохраняем выбранную температуру

    # Логируем нажатие кнопки
    logger.info(
        f"Пользователь {user_update.effective_user.username} выбрал температуру: {context.user_data['temperature']}")

    # Создаем кнопки для подтверждения заказа и отмены
    keyboard = [
        [InlineKeyboardButton("Подтвердить заказ", callback_data="confirm")],
        [InlineKeyboardButton("Отменить заказ", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user_order_description = f"Заказ: {context.user_data['drink']}, {context.user_data['milk']}, {context.user_data['syrup_1']},{context.user_data['syrup_2']}, {context.user_data['volume']}ml, {context.user_data['temperature']}."
    query.edit_message_text(text= user_order_description + "\nПодтвердите ваш заказ или отмените:", reply_markup=reply_markup)

    return CONFIRM_ORDER


def process_user_choice(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    user_choice = query.data
    user = user_update.effective_user

    if user_choice == 'confirm':
        user_order_description = f"Ваш заказ: {context.user_data['drink']}, {context.user_data['milk']}, {context.user_data['syrup_1']},{context.user_data['syrup_2']}, {context.user_data['volume']}ml, {context.user_data['temperature']}."

        barista_chat_username = config_data['telegram_bot']['barista_chat_id']

        user_link = "@" + user.username
        message_to_barista = f"Новый заказ от {user_link}:\n{user_order_description}"
        context.bot.send_message(chat_id=barista_chat_username, text=message_to_barista)
        user_orders[user.username] = {'chat_id': query['message']['chat']['id'], 'order': user_order_description}
        context.bot.send_message(chat_id=user_update.effective_user.id,
                                 text=user_order_description + " подтвержден и отправлен на приготовление.")
    elif user_choice == 'cancel':
        # Логика обработки отмены заказа
        # ...

        context.bot.send_message(chat_id=user_update.effective_user.id, text="Заказ отменен.")

    return reset_order(user_update, context)


def coffee_ready(update: Update, context: CallbackContext) -> None:
    # Проверяем, есть ли активные заказы
    if user_orders:
        # Создаем список кнопок
        keyboard = []
        for username, order_info in user_orders.items():
            order_description = order_info['order']
            # Каждая кнопка содержит описание заказа и имя пользователя
            button_text = f"Заказ для {username}"
            callback_data = f"ready_%@!#@${username}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Выберите заказ, который готов:', reply_markup=reply_markup)
    else:
        # Если заказов нет, отправляем сообщение об этом
        update.message.reply_text('В данный момент активных заказов нет.')


def order_ready(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    # Получаем username из данных callback
    print(query.data)
    _, username = query.data.split('_%@!#@$')
    print(username)


    if username in user_orders:
        chat_id = user_orders[username]['chat_id']
        order_description = user_orders[username]['order']
        context.bot.send_message(chat_id=chat_id, text=f"Ваш заказ готов: {order_description}")
        del user_orders[username]
        query.edit_message_text(text=f"Заказ для {username} отправлен.")
    else:
        query.edit_message_text(text=f"Заказ для {username} уже был обработан или не найден.")


def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_DRINK_TYPE: [CallbackQueryHandler(drink_type)],
            SELECT_DRINK: [CallbackQueryHandler(drink)],
            SELECT_MILK: [CallbackQueryHandler(milk)],
            APPROVE_SYRUP: [CallbackQueryHandler(approve_syrup)],
            SELECT_SYRUP_1: [CallbackQueryHandler(syrup_1)],
            SELECT_SYRUP_2: [CallbackQueryHandler(syrup_2)],
            SELECT_VOLUME: [CallbackQueryHandler(volume)],
            SELECT_TEMPERATURE: [CallbackQueryHandler(temperature)],
            CONFIRM_ORDER: [CallbackQueryHandler(process_user_choice)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('coffee_ready', coffee_ready,
                                  Filters.chat(chat_id=int(config_data['telegram_bot']['barista_chat_id']))))
    dp.add_handler(CallbackQueryHandler(order_ready, pattern='^ready_'))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
