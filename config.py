# config.py
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
import logging
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
    "description": "Telegram бот для работы с музыкой ВК",
    "release_date": "2025",
    "features": [
        "🎵 Моя музыка",
        "👥 Музыка друзей", 
        "👥 Музыка групп",
        "📋 Музака из плейлистов", 
        "🔍 Поиск музыки",
        "📻 Рекомендации и популярная музыка",
        "🤖 Алгоритмические подборки VK"
    ]
}

# Конфигурация VK API
VK_API_VERSION = "5.131"
KATE_USER_AGENT = "KateMobileAndroid/51.1-442 (Android 11; SDK 30; arm64-v8a; Samsung SM-G991B; ru_RU)"

# Настройки пагинации
PAGE_SIZE = 10

# Пути к файлам
TOKEN_FILE = 'vk_token.txt'