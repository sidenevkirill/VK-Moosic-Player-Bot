import os
import logging
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Информация о программе
PROGRAM_INFO = {
    "name": "VK Moosic Transfer - Трансфер музыки из ВК",
    "version": "0.0.1",
    "author": "Разработчик <a href='https://t.me/lisdevs'>LisDevs</a>",
    "donation": "<a href='https://tips.yandex.ru/guest/payment/3657677'>Поддержите нас</a>",
    "description": "Telegram бот для работы с музыкой ВК",
    "release_date": "2025",
    "features": [
        "🎵 Моя музыка",
        "👥 Музыка друзей",
        "👥 Музыка групп",
        "📋 Музыка из плейлистов",
        "🔍 Поиск музыки",
        "📻 Рекомендации",
        "🤖 Алгоритмы"
    ]
}

# Конфигурация VK API
VK_API_VERSION = "5.199"
KATE_USER_AGENT = "KateMobileAndroid/51.1-442 (Android 11; SDK 30; arm64-v8a; Samsung SM-G991B; ru_RU)"

# Настройки пагинации
PAGE_SIZE = 10

# Пути к файлам
TOKEN_FILE = 'vk_token.txt'

# Конфигурация подписок
SUBSCRIPTION_CONFIG = {
    "admin_id": [7708249698, 6344982306],  # Ваши ID администраторов
    "channel_id": "-1003394561601",  # ID канала (если нужен)
    "admin_channel_id": "-1003427114624",  # Канал для уведомлений
    "support_link": "https://t.me/KarloBoss",  # Ссылка на поддержку
    "payment_provider_token": os.getenv('PAYMENT_PROVIDER_TOKEN', ''),  # Токен платежной системы
}

# Конфигурация бесплатных запросов
FREE_REQUESTS_CONFIG = {
    "max_free_requests": 10,  # Количество бесплатных запросов
    "requests_reset_days": 30,  # Сброс через 30 дней
}

# Функции, требующие подписки
SUBSCRIPTION_REQUIRED_FEATURES = ["search_music"]  # Только поиск требует подписки

# Токен бота
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не установлен в .env файле")
