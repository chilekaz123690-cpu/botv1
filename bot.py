import telebot
from telebot import types
from telebot.types import ReplyKeyboardRemove
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
MANAGER_CHAT_ID = 8098616790
GOOGLE_CREDENTIALS = 'dag-bot-credentials.json'
SHEET_ID = '1HcGcdLB7h2KxQhQr5722awfKBTOnqgKmKUJE8BP6JY4'
SHEET_NAME = 'Лист1'

# Назва бота
BOT_NAME = "VK"

bot = telebot.TeleBot(BOT_TOKEN)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

print("Бот запущений, Google Sheets підключено")

user_states = {}
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = 'question1'
    user_data[user_id] = {}
    bot.send_message(message.chat.id, "Привет! Давай пройдем опрос для подбора работы.")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("16-25", "25-35", "35-45", "45-55", "больше")
    bot.send_message(message.chat.id, "Сколько тебе лет?", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    if state is None:
        return

    if state == 'question1':
        if message.text in ["16-25", "25-35", "35-45", "45-55", "больше"]:
            user_data[user_id]['age_range'] = message.text
            user_states[user_id] = 'question2'
            bot.send_message(message.chat.id, "В каком городе тебя интересует работа?", reply_markup=ReplyKeyboardRemove())
        else:
            bot.send_message(message.chat.id, "Пожалуйста, выбери один из вариантов возраста.")

    elif state == 'question2':
        user_data[user_id]['city'] = message.text
        user_states[user_id] = 'question3'
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Спокойная работа зарплата до 35 000 рублей")
        markup.add("Рискованная работа зарплата от 120 000 рублей")
        bot.send_message(message.chat.id, "Тебя больше интересует", reply_markup=markup)

    elif state == 'question3':
        interest = message.text
        result = "Відмовлено"

        if interest == "Спокойная работа зарплата до 35 000 рублей":
            bot.send_message(message.chat.id, "Спасибо, нас интересуют более авантюрные кандидаты", reply_markup=ReplyKeyboardRemove())

        elif interest == "Рискованная работа зарплата от 120 000 рублей":
            bot.send_message(message.chat.id, "Наш менеджер свяжется с вами в течение 24 часов", reply_markup=ReplyKeyboardRemove())
            result = "Кваліфікований"

            first_name = message.from_user.first_name or "Невідомо"
            last_name = message.from_user.last_name or "Невідомо"
            username = message.from_user.username or "немає"
            language = message.from_user.language_code or "невідома"
            premium = "Так" if getattr(message.from_user, 'is_premium', False) else "Ні"
            is_bot_status = "Так" if message.from_user.is_bot else "Ні"
            clickable_id = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
            age = user_data[user_id].get('age_range', 'Не вказано')
            city = user_data[user_id].get('city', 'Не вказано')
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

            notification = (
                f"Новий кваліфікований лід!\n\n"
                f"Ім'я: {first_name}\n"
                f"Прізвище: {last_name}\n"
                f"Username: @{username}\n"
                f"Мова: {language}\n"
                f"Premium: {premium}\n"
                f"Це бот: {is_bot_status}\n"
                f"ID: {clickable_id}\n\n"
                f"Вік: {age}\n"
                f"Місто: {city}\n"
                f"Час проходження: {timestamp}\n\n"
                f"Бот: {BOT_NAME}"
            )
            bot.send_message(MANAGER_CHAT_ID, notification, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "Пожалуйста, выбери один из вариантов.")
            result = "Невідомо"

        # Запис у Google Таблицю для ВСІХ
        first_name = message.from_user.first_name or "Невідомо"
        last_name = message.from_user.last_name or "Невідомо"
        username = message.from_user.username or "немає"
        language = message.from_user.language_code or "невідома"
        premium = "Так" if getattr(message.from_user, 'is_premium', False) else "Ні"
        is_bot_status = "Так" if message.from_user.is_bot else "Ні"
        age = user_data[user_id].get('age_range', 'Не вказано')
        city = user_data[user_id].get('city', 'Не вказано')
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

        row = [
            user_id,
            first_name,
            last_name,
            f"@{username}",
            language,
            premium,
            is_bot_status,
            age,
            city,
            timestamp,
            result,
            BOT_NAME  # Новий останній стовпець — назва бота
        ]
        sheet.append_row(row)
        print(f"Записано в таблицю: {result} (Бот: {BOT_NAME})")

        # Очищення стану
        del user_states[user_id]
        del user_data[user_id]

print("Полінг запущено...")
bot.infinity_polling()
