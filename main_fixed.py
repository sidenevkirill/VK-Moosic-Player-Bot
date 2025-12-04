# main_fixed.py
import os
import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

try:
    import imghdr
except ImportError:
    # Создаем фиктивный модуль imghdr для Python 3.13
    import types
    imghdr_module = types.ModuleType('imghdr')
    
    def what(file, h=None):
        return None
    
    imghdr_module.what = what
    sys.modules['imghdr'] = imghdr_module

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import logger
from vk_manager import vk_manager
from handlers import start, help_command, token_command, menu_command, handle_token, handle_search_query
from callbacks import handle_callback_query

def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления: {context.error}")

def main():
    """Основная функция запуска бота"""
    # Загрузка токена из файла при запуске
    vk_manager.load_token_from_file()
    
    # Получаем токен бота
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в .env файле")
        return
    
    try:
        # Создание приложения Telegram
        application = Application.builder().token(bot_token).build()
        
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
        
        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Запуск бота
        logger.info("Бот запущен")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    main()