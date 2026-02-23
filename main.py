# main.py
import os
import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

# Применяем фикс для imghdr
import fix_imghdr

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, PreCheckoutQueryHandler
from config import logger, TELEGRAM_BOT_TOKEN
from vk_manager import vk_manager
from subscription_manager import subscription_manager
from handlers import (
    start, help_command, token_command, menu_command, subscription_command,
    handle_token, handle_message, handle_search_query, handle_screenshot_submission,
    handle_admin_command, handle_pre_checkout, handle_successful_payment
)
from callbacks import handle_callback_query

def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления: {context.error}")

def main():
    """Основная функция запуска бота"""
    # Загрузка токена из файла при запуске
    vk_manager.load_token_from_file()
    
    # Инициализация менеджера подписок
    subscription_manager.load_data()
    
    # Добавляем admin_id из конфига если нет в данных
    if "admin_id" not in subscription_manager.data:
        from config import SUBSCRIPTION_CONFIG
        subscription_manager.data["admin_id"] = SUBSCRIPTION_CONFIG["admin_id"]
        subscription_manager.save()
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен")
        return
    
    try:
        # Создание Updater (для python-telegram-bot 13.15)
        updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Добавление обработчиков команд
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("token", token_command))
        dispatcher.add_handler(CommandHandler("menu", menu_command))
        dispatcher.add_handler(CommandHandler("subscription", subscription_command))
        dispatcher.add_handler(CommandHandler("admin", handle_admin_command))
        
        # Добавляем обработчик текстовых сообщений
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # Добавляем обработчик поискового запроса
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_search_query))
        
        # Добавляем обработчик фотографий (скриншоты)
        dispatcher.add_handler(MessageHandler(Filters.photo, handle_screenshot_submission))
        
        # Добавляем обработчики платежей
        dispatcher.add_handler(PreCheckoutQueryHandler(handle_pre_checkout))
        dispatcher.add_handler(MessageHandler(Filters.successful_payment, handle_successful_payment))
        
        # Добавляем обработчик callback запросов
        dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Добавляем обработчик ошибок
        dispatcher.add_error_handler(error_handler)
        
        # Запуск бота
        logger.info("Бот запущен")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    main()
