import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы для ConversationHandler
SET_REMINDER, SET_DATE, SET_TIME, SET_TEXT = range(4)
SET_BIRTHDAY, SET_BIRTHDATE, SET_BIRTHNAME = range(4, 7)

# Вставьте сюда токен вашего бота, полученный от @BotFather
TELEGRAM_BOT_TOKEN = "8123115540:AAE80rOVsbDWkKqjZBXqzp8mFgVAD1d3QVQ"

# Класс для хранения данных
class ReminderBot:
    def __init__(self):
        self.reminders = {}
        self.birthdays = {}

    def add_reminder(self, user_id, date_time, text):
        if user_id not in self.reminders:
            self.reminders[user_id] = []
        self.reminders[user_id].append({'date_time': date_time, 'text': text})
    
    def add_birthday(self, user_id, date, name):
        if user_id not in self.birthdays:
            self.birthdays[user_id] = []
        self.birthdays[user_id].append({'date': date, 'name': name})
    
    def get_reminders(self, user_id):
        return self.reminders.get(user_id, [])
    
    def get_birthdays(self, user_id):
        return self.birthdays.get(user_id, [])

# Инициализация бота
bot_data = ReminderBot()

# Функции для работы с датами
def parse_date(text):
    try:
        return datetime.strptime(text, '%d.%m.%Y').date()
    except ValueError:
        return None

def parse_time(text):
    try:
        return datetime.strptime(text, '%H:%M').time()
    except ValueError:
        return None

def create_datetime(date, time):
    return datetime.combine(date, time)

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот-напоминалка.\n"
        "Я могу напоминать тебе о важных делах и днях рождения.\n"
        "Используй команды:\n"
        "/add_reminder - добавить напоминание\n"
        "/add_birthday - добавить день рождения\n"
        "/my_reminders - посмотреть мои напоминания\n"
        "/my_birthdays - посмотреть дни рождения"
    )

async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите дату напоминания в формате ДД.ММ.ГГГГ (например, 31.12.2023):"
    )
    return SET_DATE

async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = parse_date(update.message.text)
    if not date:
        await update.message.reply_text("Неверный формат даты. Попробуйте еще раз (ДД.ММ.ГГГГ):")
        return SET_DATE
    
    context.user_data['reminder_date'] = date
    await update.message.reply_text("Теперь введите время в формате ЧЧ:ММ (например, 14:30):")
    return SET_TIME

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time = parse_time(update.message.text)
    if not time:
        await update.message.reply_text("Неверный формат времени. Попробуйте еще раз (ЧЧ:ММ):")
        return SET_TIME
    
    context.user_data['reminder_time'] = time
    await update.message.reply_text("Теперь введите текст напоминания:")
    return SET_TEXT

async def set_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    date = context.user_data['reminder_date']
    time = context.user_data['reminder_time']
    date_time = create_datetime(date, time)
    
    user_id = update.effective_user.id
    bot_data.add_reminder(user_id, date_time, text)
    
    # Запланировать напоминание
    schedule_reminder(user_id, date_time, text, context)
    
    await update.message.reply_text(
        f"Напоминание установлено на {date_time.strftime('%d.%m.%Y %H:%M')}:\n{text}"
    )
    return ConversationHandler.END

async def add_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите дату рождения в формате ДД.ММ (например, 31.12):"
    )
    return SET_BIRTHDATE

async def set_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        date = datetime.strptime(update.message.text, '%d.%m').date()
        context.user_data['birthdate'] = update.message.text
        await update.message.reply_text("Введите имя человека:")
        return SET_BIRTHNAME
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Попробуйте еще раз (ДД.ММ):")
        return SET_BIRTHDATE

async def set_birthname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    birthdate = context.user_data['birthdate']
    
    user_id = update.effective_user.id
    bot_data.add_birthday(user_id, birthdate, name)
    
    await update.message.reply_text(
        f"День рождения {name} ({birthdate}) добавлен. Я буду напоминать вам каждый год!"
    )
    
    today = datetime.now().strftime('%d.%m')
    if birthdate == today:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 Сегодня день рождения у {name}! 🎉"
        )
    
    return ConversationHandler.END

async def my_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reminders = bot_data.get_reminders(user_id)
    
    if not reminders:
        await update.message.reply_text("У вас нет активных напоминаний.")
        return
    
    text = "Ваши напоминания:\n\n"
    for i, reminder in enumerate(reminders, 1):
        text += (
            f"{i}. {reminder['date_time'].strftime('%d.%m.%Y %H:%M')}\n"
            f"   {reminder['text']}\n\n"
        )
    
    await update.message.reply_text(text)

async def my_birthdays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    birthdays = bot_data.get_birthdays(user_id)
    
    if not birthdays:
        await update.message.reply_text("У вас нет сохраненных дней рождения.")
        return
    
    text = "Дни рождения:\n\n"
    for i, birthday in enumerate(birthdays, 1):
        text += f"{i}. {birthday['name']} - {birthday['date']}\n"
    
    await update.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

def schedule_reminder(user_id, date_time, text, context):
    delta = date_time - datetime.now()
    seconds = delta.total_seconds()
    
    if seconds > 0:
        context.job_queue.run_once(
            callback=send_reminder,
            when=seconds,
            chat_id=user_id,
            data=text
        )

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"⏰ Напоминание: {job.data}"
    )

async def check_birthdays(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime('%d.%m')
    for user_id, birthdays in bot_data.birthdays.items():
        for birthday in birthdays:
            if birthday['date'] == today:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 Сегодня день рождения у {birthday['name']}! 🎉"
                )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Ошибка в боте:", exc_info=context.error)
    if update.message:
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

def main():
    try:
        # Улучшенная проверка токена
        if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.strip() == "1234567890:AAFm2e4f5g6h7j8k9l0z1x2c3v4b5n6m7q8w9e":
            error_msg = """
            ОШИБКА: Необходимо указать токен бота!
            
            1. Получите токен у @BotFather в Telegram
            2. Замените строку 
               TELEGRAM_BOT_TOKEN = "1234567890:AAFm2e4f5g6h7j8k9l0z1x2c3v4b5n6m7q8w9e"
               на
               TELEGRAM_BOT_TOKEN = "ВАШ_НАСТОЯЩИЙ_ТОКЕН"
            
            Токен должен выглядеть примерно так: 1234567890:AAFm2e4f5g6h7j8k9l0z1x2c3v4b5n6m7q8w9e
            """
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Проверка формата токена
        if ":" not in TELEGRAM_BOT_TOKEN or len(TELEGRAM_BOT_TOKEN) < 30:
            error_msg = "Неверный формат токена! Токен должен содержать ':' и быть длиннее 30 символов"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Попытка запуска бота с токеном: %s...", TELEGRAM_BOT_TOKEN[:10] + "..." + TELEGRAM_BOT_TOKEN[-5:])
        
        # Создаем Application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # ConversationHandler для добавления напоминания
        conv_handler_reminder = ConversationHandler(
            entry_points=[CommandHandler('add_reminder', add_reminder)],
            states={
                SET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_date)],
                SET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time)],
                SET_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_text)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        
        # ConversationHandler для добавления дня рождения
        conv_handler_birthday = ConversationHandler(
            entry_points=[CommandHandler('add_birthday', add_birthday)],
            states={
                SET_BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_birthdate)],
                SET_BIRTHNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_birthname)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        
        # Добавление обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("my_reminders", my_reminders))
        application.add_handler(CommandHandler("my_birthdays", my_birthdays))
        application.add_handler(conv_handler_reminder)
        application.add_handler(conv_handler_birthday)
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Планировщик для проверки дней рождения каждый день
        job_queue = application.job_queue
        job_queue.run_daily(
            check_birthdays,
            time=datetime.strptime("09:00", "%H:%M").time(),
            days=(0, 1, 2, 3, 4, 5, 6),
        )
        
        logger.info("Бот успешно запущен!")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        print(f"\n\nОШИБКА: {str(e)}\n")
        print("Проверьте следующее:")
        print("1. Токен должен быть вставлен в код (строка TELEGRAM_BOT_TOKEN)")
        print("2. Токен должен быть получен от @BotFather")
        print("3. Токен должен выглядеть как: 1234567890:AAFm2e4f5g6h7j8k9l0z1x2c3v4b5n6m7q8w9e")
        print("4. В токене не должно быть лишних пробелов или кавычек")
        raise

if __name__ == '__main__':
    main()