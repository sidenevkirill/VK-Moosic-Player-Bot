# main.py
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import logger
from vk_manager import vk_manager
from handlers import start, help_command, token_command, menu_command, handle_token, handle_search_query
from callbacks import handle_callback_query

def main():
    """Основная функция запуска бота"""
    # Загрузка токена из файла при запуске
    vk_manager.load_token_from_file()
    
    # Создание приложения Telegram
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("token", token_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # Добавляем обработчик токена
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token))
    
    # Добавляем обработчик поискового запроса
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query))
    
    # Добавляем обработчик callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Запуск бота
    logger.info("Бот запущен")
    application.run_polling()

if __name__ == "__main__":
    main()