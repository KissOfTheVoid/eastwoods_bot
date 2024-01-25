import logging

import pandas as pd
import yaml
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка данных из YAML-файла
with open('config.yaml', 'r') as yaml_file:
    config_data = yaml.safe_load(yaml_file)

# Получение токена бота и идентификатора чата с баристой
TOKEN = config_data['telegram_bot']['token']

# Шаги разговора
SELECT_DRINK, SELECT_MILK, SELECT_SYRUP, SELECT_VOLUME, SELECT_TEMPERATURE, CONFIRM_ORDER = range(6)

user_messages = {}

# Загрузка данных из Excel файла
def load_menu_data(file_path):
    drinks = pd.read_excel(file_path, sheet_name='Напитки')
    milk = pd.read_excel(file_path, sheet_name='Молоко')
    syrups = pd.read_excel(file_path, sheet_name='Сиропы')
    return drinks['Название'].tolist(), milk['Название'].tolist(), syrups['Название'].tolist()


drinks, milks, syrups = load_menu_data('/Users/walker/Downloads/Eastwood.xlsx')


# Функции для команд
def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    context.user_data['user_messages'] = []  # Инициализируем список сообщений пользователя

    keyboard = [[InlineKeyboardButton(drink, callback_data=f'drink_{drink}') for drink in drinks]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Добро пожаловать в нашу кофейню! Пожалуйста, выберите напиток:', reply_markup=reply_markup)

    return SELECT_DRINK

def order(user_update: Update, context: CallbackContext) -> int:
    user_id = user_update.effective_user.id
    context.user_data['user_messages'] = []  # Инициализируем список сообщений пользователя

    context.user_data['drink'] = None
    context.user_data['milk'] = None
    context.user_data['syrup'] = None
    context.user_data['volume'] = None
    context.user_data['temperature'] = None

    keyboard = [[InlineKeyboardButton(drink, callback_data=f'drink_{drink}') for drink in drinks]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user_update.message.reply_text('Пожалуйста, выберите напиток:', reply_markup=reply_markup)

    logger.info(f"Пользователь {user_update.effective_user.username} выбрал команду /order")

    return SELECT_DRINK


def reset_order(update: Update, context: CallbackContext) -> int:
    context.user_data['drink'] = None  # Обнуляем выбранный напиток
    context.user_data['milk'] = None  # Обнуляем выбранное молоко
    context.user_data['syrup'] = None  # Обнуляем выбранный сироп
    context.user_data['volume'] = None  # Обнуляем выбранный объем
    context.user_data['temperature'] = None  # Обнуляем выбранную температуру

    return SELECT_DRINK


# Определение обработчиков для каждого шага
def drink(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    context.user_data['drink'] = query.data.split('_')[1]  # Сохраняем выбранный напиток

    # Логируем нажатие кнопки
    logger.info(f"Пользователь {user_update.effective_user.username} выбрал напиток: {context.user_data['drink']}")

    keyboard = [[InlineKeyboardButton(milk, callback_data=f'milk_{milk}') for milk in milks]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите тип молока:", reply_markup=reply_markup)

    return SELECT_MILK


def milk(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    context.user_data['milk'] = query.data.split('_')[1]  # Сохраняем выбранное молоко

    # Логируем нажатие кнопки
    logger.info(f"Пользователь {user_update.effective_user.username} выбрал тип молока: {context.user_data['milk']}")

    keyboard = [[InlineKeyboardButton(syrup, callback_data=f'syrup_{syrup}') for syrup in syrups]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите сироп:", reply_markup=reply_markup)

    return SELECT_SYRUP


def syrup(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    context.user_data['syrup'] = query.data.split('_')[1]  # Сохраняем выбранный сироп

    # Логируем нажатие кнопки
    logger.info(f"Пользователь {user_update.effective_user.username} выбрал сироп: {context.user_data['syrup']}")
    volumes = ['250', '350', '500']
    keyboard = [[InlineKeyboardButton(volume, callback_data=f'volume_{volume}') for volume in volumes]]
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
    query.edit_message_text(text="Подтвердите ваш заказ или отмените:", reply_markup=reply_markup)

    return CONFIRM_ORDER


def process_user_choice(user_update: Update, context: CallbackContext) -> int:
    query = user_update.callback_query
    query.answer()
    user_choice = query.data
    user = user_update.effective_user

    if user_choice == 'confirm':
        user_order_description = f"Заказ: {context.user_data['drink']}, {context.user_data['milk']}, {context.user_data['syrup']}, {context.user_data['volume']}ml, {context.user_data['temperature']}."

        barista_chat_username = config_data['telegram_bot']['barista_chat_id']
        user_link = "@" + user.username
        message_to_barista = f"Новый заказ от {user_link}:\n{user_order_description}"

        context.bot.send_message(chat_id=barista_chat_username, text=message_to_barista)

        context.bot.send_message(chat_id=user_update.effective_user.id,
                                 text=user_order_description + " подтвержден и отправлен на приготовление.")
    elif user_choice == 'cancel':
        # Логика обработки отмены заказа
        # ...

        context.bot.send_message(chat_id=user_update.effective_user.id, text="Заказ отменен.")

    return reset_order(user_update, context)


def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('order', order)],
        states={
            SELECT_DRINK: [CallbackQueryHandler(drink)],
            SELECT_MILK: [CallbackQueryHandler(milk)],
            SELECT_SYRUP: [CallbackQueryHandler(syrup)],
            SELECT_VOLUME: [CallbackQueryHandler(volume)],
            SELECT_TEMPERATURE: [CallbackQueryHandler(temperature)],
            CONFIRM_ORDER: [CallbackQueryHandler(process_user_choice)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
