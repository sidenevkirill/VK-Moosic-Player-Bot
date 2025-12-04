import os
import logging
import requests
import tempfile
import subprocess
import sys
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

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
    "name": "Transfeero - Музыка из ВК",
    "version": "0.0.3",
    "author": "Разработчик <a href='https://t.me/lisdevs'>LisDevs</a>",
    "description": "Telegram бот для работы с музыкой ВК",
    "release_date": "2025",
    "features": [
        "🎵 Воспроизведение личной музыки",
        "👥 Музыка друзей", 
        "👥 Музыка групп",
        "📋 Управление плейлистов", 
        "🔍 Поиск треков по запросу",
        "📻 Рекомендации и популярная музыка",
        "🤖 Алгоритмические подборки VK"
    ]
}

class VKMusicManager:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.user_info = None
        # User-Agent для Kate Mobile
        self.kate_user_agent = "KateMobileAndroid/51.1-442 (Android 11; SDK 30; arm64-v8a; Samsung SM-G991B; ru_RU)"
        self.headers = {
            'User-Agent': self.kate_user_agent,
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive'
        }

    def set_token(self, token):
        """Установить токен"""
        self.token = token
        if token and '.' in token:
            parts = token.split('.')
            if len(parts) > 0:
                try:
                    self.user_id = int(parts[0])
                except ValueError:
                    self.user_id = None
        else:
            self.user_id = None

    def load_token_from_file(self, filename='vk_token.txt'):
        """Загрузить токен из файла"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    token = f.read().strip()
                    if token:
                        self.set_token(token)
                        logger.info(f"Токен загружен из файла {filename}")
                        return True
            logger.warning(f"Файл {filename} не найден или пуст")
            return False
        except Exception as e:
            logger.error(f"Ошибка при чтении файла: {e}")
            return False

    def save_token_to_file(self, filename='vk_token.txt'):
        """Сохранить токен в файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.token)
            logger.info(f"Токен сохранен в файл {filename}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении токена: {e}")
            return False

    def check_token_validity(self):
        """Проверить валидность токена"""
        if not self.token:
            return {"valid": False, "error_msg": "Токен не установлен"}
        
        url = "https://api.vk.com/method/users.get"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "fields": "first_name,last_name"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                self.user_info = data["response"][0]
                self.user_id = self.user_info.get('id')
                return {"valid": True, "user_info": self.user_info}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"valid": False, "error_msg": error_msg}
                
        except Exception as e:
            return {"valid": False, "error_msg": f"Ошибка запроса: {e}"}

    def get_friends_list(self):
        """Получить список друзей"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен или user_id не определен"}
        
        url = "https://api.vk.com/method/friends.get"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "count": 100,
            "fields": "first_name,last_name,photo_100",
            "order": "name"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {"success": True, "friends": data["response"]["items"]}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_groups_list(self):
        """Получить список групп пользователя"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен или user_id не определен"}
        
        url = "https://api.vk.com/method/groups.get"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "count": 100,
            "extended": 1,
            "fields": "name,photo_100",
            "filter": "groups"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {"success": True, "groups": data["response"]["items"]}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_friend_audio_list(self, friend_id):
        """Получить список аудиозаписей друга"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
        
        url = "https://api.vk.com/method/audio.get"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "count": 100,
            "owner_id": friend_id
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {"success": True, "audio_list": data["response"]["items"]}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_group_audio_list(self, group_id):
        """Получить список аудиозаписей группы"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
        
        owner_id = -abs(int(group_id))
        
        url = "https://api.vk.com/method/audio.get"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "count": 100,
            "owner_id": owner_id
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {"success": True, "audio_list": data["response"]["items"]}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_my_audio_list(self):
        """Получить список моих аудиозаписей"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен или user_id не определен"}
        
        url = "https://api.vk.com/method/audio.get"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "count": 100,
            "owner_id": self.user_id
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {"success": True, "audio_list": data["response"]["items"]}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_playlists(self):
        """Получить список плейлистов"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен или user_id не определен"}
        
        url = "https://api.vk.com/method/audio.getPlaylists"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "owner_id": self.user_id,
            "count": 50
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {"success": True, "playlists": data["response"]["items"]}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_playlist_tracks(self, playlist_id):
        """Получить треки из плейлиста"""
        if not self.token or not self.user_id:
            return {"success": False, "error": "Токен не установлен или user_id не определен"}
        
        url = "https://api.vk.com/method/audio.get"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "count": 100,
            "album_id": playlist_id,
            "owner_id": self.user_id
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {"success": True, "audio_list": data["response"]["items"]}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_recommendations(self):
        """Получить рекомендации"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
        
        url = "https://api.vk.com/method/audio.getRecommendations"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "count": 50,
            "shuffle": 1
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {"success": True, "audio_list": data["response"]["items"]}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                logger.warning(f"Метод getRecommendations не доступен: {error_msg}")
                return self.get_popular_music()
                
        except Exception as e:
            logger.warning(f"Ошибка в getRecommendations: {e}")
            return self.get_popular_music()

    def get_popular_music(self):
        """Получить популярную музыку"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
            
        popular_queries = [
            "популярные песни 2024", "хиты", "top hits", "новинки музыки",
            "русские хиты", "зарубежные хиты", "топ чарт", "billboard top 100"
        ]
        
        query = random.choice(popular_queries)
        
        url = "https://api.vk.com/method/audio.search"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "q": query,
            "count": 50,
            "auto_complete": 1,
            "sort": 2
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {"success": True, "audio_list": data["response"]["items"]}
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def search_audio(self, query):
        """Поиск музыки"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
        
        url = "https://api.vk.com/method/audio.search"
        params = {
            "access_token": self.token,
            "v": "5.131",
            "q": query,
            "count": 50,
            "auto_complete": 1
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                return {
                    "success": True, 
                    "results": data["response"]["items"],
                    "total_count": data["response"]["count"]
                }
            else:
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def download_audio(self, audio_url, filename):
        """Скачать аудиозапись"""
        try:
            headers = self.headers.copy()
            headers.update({
                'Referer': 'https://vk.com/',
                'Origin': 'https://vk.com'
            })
            response = requests.get(audio_url, stream=True, headers=headers)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при скачивании: {e}")
            return False

    def get_audio_info_text(self, audio_list, start_index=0, page_size=10):
        """Получить текст с информацией об аудиозаписях"""
        if not audio_list:
            return "🎵 Нет аудиозаписей"
        
        text = ""
        end_index = min(start_index + page_size, len(audio_list))
        current_page = start_index // page_size + 1
        total_pages = (len(audio_list) - 1) // page_size + 1
        
        for i in range(start_index, end_index):
            track = audio_list[i]
            artist = track.get('artist', 'Unknown Artist')
            title = track.get('title', 'Unknown Title')
            duration = track.get('duration', 0)
            
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"{minutes}:{seconds:02d}"
            
            text += f"{i+1}. {artist} - {title} ({duration_str})\n"
        
        text += f"\n📄 Страница {current_page}/{total_pages}"
        return text

    def create_audio_keyboard(self, audio_list, start_index=0, page_size=10, prefix="play_audio"):
        """Создать клавиатуру для списка аудиозаписей с пагинацией - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        if not audio_list:
            return None
        
        keyboard = []
        end_index = min(start_index + page_size, len(audio_list))
        
        # Добавляем кнопки для треков
        for i in range(start_index, end_index):
            track = audio_list[i]
            artist = track.get('artist', 'Unknown Artist')[:20]
            title = track.get('title', 'Unknown Title')[:20]
            button_text = f"{i+1}. {artist} - {title}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"{prefix}_{i}")])
        
        # Кнопки навигации по страницам
        nav_buttons = []
        current_page = start_index // page_size + 1
        total_pages = (len(audio_list) - 1) // page_size + 1
        
        # Кнопка "Назад" (предыдущая страница)
        if start_index > 0:
            prev_index = max(0, start_index - page_size)
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}_page_{prev_index}"))
        
        # Показать номер страницы (не кликабельная кнопка)
        if total_pages > 1:
            nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop"))
        
        # Кнопка "Вперед" (следующая страница)
        if end_index < len(audio_list):
            next_index = end_index
            nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"{prefix}_page_{next_index}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)

# Глобальный экземпляр менеджера
vk_manager = VKMusicManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        f"🎵 Добро пожаловать в {PROGRAM_INFO['name']}!\n\n"
        f"📝 {PROGRAM_INFO['description']}\n\n"
        "✨ Возможности:\n"
    )
    
    for feature in PROGRAM_INFO["features"]:
        welcome_text += f"   {feature}\n"
    
    welcome_text += "\n🔑 Для начала работы установите VK токен командой /token"
    
    keyboard = [
        [InlineKeyboardButton("🔑 Установить токен", callback_data="set_token")],
        [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "🎵 VK Music Manager Bot - Помощь\n\n"
        "Основные команды:\n"
        "/start - Начать работу с ботом\n"
        "/token - Установить VK токен\n"
        "/menu - Главное меню\n"
        "/help - Показать эту справку\n\n"
        "Для работы с ботом необходим VK токен с доступом к аудио."
    )
    await update.message.reply_text(help_text)

async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /token"""
    await update.message.reply_text(
        "🔑 Пожалуйста, отправьте ваш VK токен. "
        "Вы можете получить его здесь: https://vkhost.github.io/\n\n"
        "⚠️ Никому не передавайте ваш токен!"
    )

async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода токена"""
    token = update.message.text.strip()
    
    if not token:
        await update.message.reply_text("❌ Токен не может быть пустым")
        return
    
    old_token = vk_manager.token
    vk_manager.set_token(token)
    
    validity = vk_manager.check_token_validity()
    if not validity["valid"]:
        await update.message.reply_text(f"❌ Токен невалиден: {validity.get('error_msg')}")
        vk_manager.token = old_token
        return
    
    user_info = validity["user_info"]
    first_name = user_info.get('first_name', '')
    last_name = user_info.get('last_name', '')
    
    vk_manager.save_token_to_file()
    
    await update.message.reply_text(
        f"✅ Токен успешно установлен!\n"
        f"👤 Пользователь: {first_name} {last_name}\n\n"
        "Теперь вы можете использовать главное меню: /menu"
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu"""
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    if not vk_manager.token:
        keyboard = [
            [InlineKeyboardButton("🔑 Установить токен", callback_data="set_token")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ Токен не установлен. Сначала установите VK токен.",
            reply_markup=reply_markup
        )
        return
    
    # Проверяем валидность токена
    validity = vk_manager.check_token_validity()
    if not validity["valid"]:
        keyboard = [
            [InlineKeyboardButton("🔑 Установить токен", callback_data="set_token")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❌ Токен невалиден: {validity.get('error_msg')}",
            reply_markup=reply_markup
        )
        return
    
    user_info = validity["user_info"]
    first_name = user_info.get('first_name', '')
    last_name = user_info.get('last_name', '')
    
    keyboard = [
        [InlineKeyboardButton("🎵 Моя музыка", callback_data="my_music")],
        [InlineKeyboardButton("👥 Музыка друзей", callback_data="friends_music")],
        [InlineKeyboardButton("👥 Музыка групп", callback_data="groups_music")],
        [InlineKeyboardButton("📋 Мои плейлисты", callback_data="playlists")],
        [InlineKeyboardButton("🔍 Поиск музыки", callback_data="search_music")],
        [InlineKeyboardButton("📻 Рекомендации", callback_data="recommendations")],
        [InlineKeyboardButton("🤖 Алгоритмические подборки", callback_data="algorithmic_mixes")],
        [InlineKeyboardButton("⚙️ Управление токеном", callback_data="token_management")],
        [InlineKeyboardButton("ℹ️ О программе", callback_data="program_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👤 {first_name} {last_name}\n"
        "🎵 Выберите действие:",
        reply_markup=reply_markup
    )

async def show_main_menu_from_query(query, context):
    """Показать главное меню из callback query"""
    if not vk_manager.token:
        keyboard = [[InlineKeyboardButton("🔑 Установить токен", callback_data="set_token")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Токен не установлен. Сначала установите VK токен.",
            reply_markup=reply_markup
        )
        return
    
    validity = vk_manager.check_token_validity()
    if not validity["valid"]:
        keyboard = [[InlineKeyboardButton("🔑 Установить токен", callback_data="set_token")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"❌ Токен невалиден: {validity.get('error_msg')}",
            reply_markup=reply_markup
        )
        return
    
    user_info = validity["user_info"]
    first_name = user_info.get('first_name', '')
    last_name = user_info.get('last_name', '')
    
    keyboard = [
        [InlineKeyboardButton("🎵 Моя музыка", callback_data="my_music")],
        [InlineKeyboardButton("👥 Музыка друзей", callback_data="friends_music")],
        [InlineKeyboardButton("👥 Музыка групп", callback_data="groups_music")],
        [InlineKeyboardButton("📋 Мои плейлисты", callback_data="playlists")],
        [InlineKeyboardButton("🔍 Поиск музыки", callback_data="search_music")],
        [InlineKeyboardButton("📻 Рекомендации", callback_data="recommendations")],
        [InlineKeyboardButton("🤖 Алгоритмические подборки", callback_data="algorithmic_mixes")],
        [InlineKeyboardButton("⚙️ Управление токеном", callback_data="token_management")],
        [InlineKeyboardButton("ℹ️ О программе", callback_data="program_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"👤 {first_name} {last_name}\n"
        "🎵 Выберите действие:",
        reply_markup=reply_markup
    )

async def show_program_info(query):
    """Показать информацию о программе"""
    info_text = (
        f"🤖 {PROGRAM_INFO['name']} v{PROGRAM_INFO['version']}\n"
        f"📅 {PROGRAM_INFO['release_date']}\n"
        f"👨‍💻 {PROGRAM_INFO['author']}\n\n"
        f"📝 {PROGRAM_INFO['description']}\n\n"
        "✨ Возможности:\n"
    )
    
    for feature in PROGRAM_INFO["features"]:
        info_text += f"   {feature}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(info_text, reply_markup=reply_markup, parse_mode='HTML')

async def show_info(query):
    """Показать информацию о программе"""
    info_text = (
        f"🤖 {PROGRAM_INFO['name']} v{PROGRAM_INFO['version']}\n"
        f"📅 {PROGRAM_INFO['release_date']}\n"
        f"👨‍💻 {PROGRAM_INFO['author']}\n\n"
        f"📝 {PROGRAM_INFO['description']}\n\n"
        "✨ Возможности:\n"
    )
    
    for feature in PROGRAM_INFO["features"]:
        info_text += f"   {feature}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(info_text, reply_markup=reply_markup, parse_mode='HTML')

async def show_token_management(query):
    """Показать меню управления токеном"""
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить токен", callback_data="check_token")],
        [InlineKeyboardButton("🔑 Изменить токен", callback_data="set_token")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ Управление токеном:",
        reply_markup=reply_markup
    )

async def show_my_music(query, context):
    """Показать мою музыку"""
    result = vk_manager.get_my_audio_list()
    if not result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    audio_list = result["audio_list"]
    if not audio_list:
        await query.edit_message_text(
            "🎵 У вас нет аудиозаписей",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    # Сохраняем список аудиозаписей в контексте
    context.user_data['current_audio_list'] = audio_list
    context.user_data['audio_source'] = 'my_music'
    
    text = vk_manager.get_audio_info_text(audio_list)
    keyboard = vk_manager.create_audio_keyboard(audio_list, prefix="play_audio")
    
    await query.edit_message_text(text, reply_markup=keyboard)

async def show_friends_list(query, context):
    """Показать список друзей"""
    result = vk_manager.get_friends_list()
    if not result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    friends = result["friends"]
    if not friends:
        await query.edit_message_text(
            "👥 У вас нет друзей или доступ ограничен",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    keyboard = []
    for i, friend in enumerate(friends[:10]):
        first_name = friend.get('first_name', '')
        last_name = friend.get('last_name', '')
        button_text = f"{i+1}. {first_name} {last_name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"friend_{friend['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👥 Выберите друга для просмотра музыки:",
        reply_markup=reply_markup
    )

async def show_groups_list(query, context):
    """Показать список групп"""
    result = vk_manager.get_groups_list()
    if not result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    groups = result["groups"]
    if not groups:
        await query.edit_message_text(
            "👥 У вас нет групп или доступ ограничен",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    keyboard = []
    for i, group in enumerate(groups[:10]):
        name = group.get('name', 'Без названия')
        button_text = f"{i+1}. {name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"group_{group['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👥 Выберите группу для просмотра музыки:",
        reply_markup=reply_markup
    )

async def show_playlists(query, context):
    """Показать список плейлистов"""
    result = vk_manager.get_playlists()
    if not result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    playlists = result["playlists"]
    if not playlists:
        await query.edit_message_text(
            "📋 У вас нет плейлистов",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    keyboard = []
    for i, playlist in enumerate(playlists[:10]):
        title = playlist.get('title', 'Без названия')
        count = playlist.get('count', 0)
        button_text = f"{i+1}. {title} ({count})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"playlist_{playlist['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📋 Выберите плейлист:",
        reply_markup=reply_markup
    )

async def show_recommendations(query, context):
    """Показать рекомендации"""
    result = vk_manager.get_recommendations()
    if not result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    audio_list = result["audio_list"]
    if not audio_list:
        await query.edit_message_text(
            "🎵 Нет рекомендаций",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    # Сохраняем список аудиозаписей в контексте
    context.user_data['current_audio_list'] = audio_list
    context.user_data['audio_source'] = 'recommendations'
    
    text = vk_manager.get_audio_info_text(audio_list)
    keyboard = vk_manager.create_audio_keyboard(audio_list, prefix="play_audio")
    
    await query.edit_message_text(text, reply_markup=keyboard)

async def show_algorithmic_mixes(query, context):
    """Показать алгоритмические подборки"""
    result = vk_manager.get_recommendations()
    if not result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка: {result.get('error')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    audio_list = result["audio_list"]
    if not audio_list:
        await query.edit_message_text(
            "🤖 Нет алгоритмических подборок",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    # Сохраняем список аудиозаписей в контексте
    context.user_data['current_audio_list'] = audio_list
    context.user_data['audio_source'] = 'algorithmic_mixes'
    
    text = vk_manager.get_audio_info_text(audio_list)
    keyboard = vk_manager.create_audio_keyboard(audio_list, prefix="play_audio")
    
    await query.edit_message_text(text, reply_markup=keyboard)

async def handle_search_request(query, context):
    """Обработчик запроса поиска музыки"""
    await query.edit_message_text(
        "🔍 Введите поисковый запрос:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
    )
    context.user_data['awaiting_search_query'] = True

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода поискового запроса"""
    if not context.user_data.get('awaiting_search_query'):
        return
    
    search_query = update.message.text.strip()
    if not search_query:
        await update.message.reply_text("❌ Поисковый запрос не может быть пустым")
        return
    
    context.user_data['awaiting_search_query'] = False
    
    # Показываем сообщение о поиске
    message = await update.message.reply_text("🔍 Ищу музыку...")
    
    # Выполняем поиск
    result = vk_manager.search_audio(search_query)
    if not result["success"]:
        await message.edit_text(
            f"❌ Ошибка поиска: {result.get('error')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    audio_list = result["results"]
    if not audio_list:
        await message.edit_text(
            "🎵 Ничего не найдено",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return
    
    # Сохраняем список аудиозаписей в контексте
    context.user_data['current_audio_list'] = audio_list
    context.user_data['audio_source'] = 'search'
    
    text = f"🔍 Результаты поиска по запросу: '{search_query}'\n\n"
    text += vk_manager.get_audio_info_text(audio_list)
    keyboard = vk_manager.create_audio_keyboard(audio_list, prefix="play_audio")
    
    await message.edit_text(text, reply_markup=keyboard)

async def play_audio_track(query, context, audio_index):
    """Воспроизвести аудиозапись"""
    audio_list = context.user_data.get('current_audio_list', [])
    if not audio_list or audio_index >= len(audio_list):
        await query.answer("❌ Аудиозапись не найдена")
        return
    
    track = audio_list[audio_index]
    artist = track.get('artist', 'Unknown Artist')
    title = track.get('title', 'Unknown Title')
    url = track.get('url')
    
    if not url:
        await query.answer("❌ Невозможно воспроизвести (отсутствует URL)")
        return
    
    # Показываем сообщение о загрузке
    await query.edit_message_text(f"📥 Загружаю: {artist} - {title}...")
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
        temp_filename = tmp_file.name
    
    # Скачиваем аудио
    success = vk_manager.download_audio(url, temp_filename)
    if not success:
        await query.edit_message_text(
            f"❌ Ошибка загрузки: {artist} - {title}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"{context.user_data.get('audio_source', 'main_menu')}")]])
        )
        os.unlink(temp_filename)
        return
    
    try:
        # Отправляем аудиофайл
        with open(temp_filename, 'rb') as audio_file:
            audio_source = context.user_data.get('audio_source', 'main_menu')
            
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_file,
                title=title,
                performer=artist,
                caption=f"🎵 {artist} - {title}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад к списку", callback_data=f"{audio_source}")]])
            )
        
    except Exception as e:
        logger.error(f"Ошибка при отправке аудио: {e}")
        await query.edit_message_text(
            f"❌ Ошибка отправки аудио: {e}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"{context.user_data.get('audio_source', 'main_menu')}")]])
        )
    finally:
        # Удаляем временный файл
        try:
            os.unlink(temp_filename)
        except:
            pass

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Получен callback: {data}")
    
    try:
        if data == "main_menu":
            await show_main_menu_from_query(query, context)
        
        elif data == "noop":
            # Пустой callback (кнопка с номером страницы)
            return
        
        elif data == "set_token":
            await query.edit_message_text(
                "🔑 Пожалуйста, отправьте ваш VK токен. "
                "Вы можете получить его здесь: https://vkhost.github.io/\n\n"
                "⚠️ Никому не передавайте ваш токен!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        
        elif data == "info":
            await show_info(query)
        
        elif data == "program_info":
            await show_program_info(query)
        
        elif data == "token_management":
            await show_token_management(query)
        
        elif data == "check_token":
            validity = vk_manager.check_token_validity()
            if validity["valid"]:
                user_info = validity["user_info"]
                first_name = user_info.get('first_name', '')
                last_name = user_info.get('last_name', '')
                await query.edit_message_text(
                    f"✅ Токен валиден!\n👤 Пользователь: {first_name} {last_name}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="token_management")]])
                )
            else:
                await query.edit_message_text(
                    f"❌ Токен невалиден: {validity.get('error_msg')}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="token_management")]])
                )
        
        # Обработка возврата к разным источникам музыки
        elif data in ["my_music", "friends_music", "groups_music", 
                     "playlists", "recommendations", "algorithmic_mixes", 
                     "search_music"]:
            
            if data == "my_music":
                await show_my_music(query, context)
            elif data == "friends_music":
                await show_friends_list(query, context)
            elif data == "groups_music":
                await show_groups_list(query, context)
            elif data == "playlists":
                await show_playlists(query, context)
            elif data == "recommendations":
                await show_recommendations(query, context)
            elif data == "algorithmic_mixes":
                await show_algorithmic_mixes(query, context)
            elif data == "search_music":
                await handle_search_request(query, context)
        
        elif data.startswith("friend_"):
            friend_id = data.split("_")[1]
            result = vk_manager.get_friend_audio_list(friend_id)
            if not result["success"]:
                await query.edit_message_text(
                    f"❌ Ошибка: {result.get('error')}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="friends_music")]])
                )
                return
            
            audio_list = result["audio_list"]
            if not audio_list:
                await query.edit_message_text(
                    "🎵 У друга нет аудиозаписей или доступ ограничен",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="friends_music")]])
                )
                return
            
            # Сохраняем список аудиозаписей и источник в контексте
            context.user_data['current_audio_list'] = audio_list
            context.user_data['audio_source'] = 'friends_music'  # сохраняем общий источник
            
            text = vk_manager.get_audio_info_text(audio_list)
            keyboard = vk_manager.create_audio_keyboard(audio_list, prefix="play_audio")
            
            await query.edit_message_text(text, reply_markup=keyboard)
        
        elif data.startswith("group_"):
            group_id = data.split("_")[1]
            result = vk_manager.get_group_audio_list(group_id)
            if not result["success"]:
                await query.edit_message_text(
                    f"❌ Ошибка: {result.get('error')}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="groups_music")]])
                )
                return
            
            audio_list = result["audio_list"]
            if not audio_list:
                await query.edit_message_text(
                    "🎵 В группе нет аудиозаписей или доступ ограничен",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="groups_music")]])
                )
                return
            
            # Сохраняем список аудиозаписей и источник в контексте
            context.user_data['current_audio_list'] = audio_list
            context.user_data['audio_source'] = 'groups_music'  # сохраняем общий источник
            
            text = vk_manager.get_audio_info_text(audio_list)
            keyboard = vk_manager.create_audio_keyboard(audio_list, prefix="play_audio")
            
            await query.edit_message_text(text, reply_markup=keyboard)
        
        elif data.startswith("playlist_"):
            playlist_id = data.split("_")[1]
            result = vk_manager.get_playlist_tracks(playlist_id)
            if not result["success"]:
                await query.edit_message_text(
                    f"❌ Ошибка: {result.get('error')}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="playlists")]])
                )
                return
            
            audio_list = result["audio_list"]
            if not audio_list:
                await query.edit_message_text(
                    "🎵 Плейлист пуст",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="playlists")]])
                )
                return
            
            # Сохраняем список аудиозаписей и источник в контексте
            context.user_data['current_audio_list'] = audio_list
            context.user_data['audio_source'] = 'playlists'  # сохраняем общий источник
            
            text = vk_manager.get_audio_info_text(audio_list)
            keyboard = vk_manager.create_audio_keyboard(audio_list, prefix="play_audio")
            
            await query.edit_message_text(text, reply_markup=keyboard)
        
        elif data.startswith("play_audio_page_"):
            # ПЕРЕКЛЮЧЕНИЕ СТРАНИЦ - ВЫНЕСЕН В ОТДЕЛЬНЫЙ БЛОК
            try:
                logger.info(f"Обрабатываем пагинацию: {data}")
                
                # Извлекаем индекс страницы из формата "play_audio_page_10"
                start_index_str = data.replace("play_audio_page_", "")
                page_index = int(start_index_str)
                logger.info(f"Переключение на страницу с индексом: {page_index}")
                
                # Получаем список треков
                audio_list = context.user_data.get('current_audio_list', [])
                if not audio_list:
                    await query.answer("❌ Список треков не найден")
                    await query.edit_message_text(
                        "❌ Список треков не найден. Вернитесь в меню.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
                    )
                    return
                
                logger.info(f"Всего треков в списке: {len(audio_list)}")
                
                # Проверяем границы
                if page_index < 0:
                    page_index = 0
                if page_index >= len(audio_list):
                    # Возвращаемся к последней возможной странице
                    page_size = 10
                    last_page_start = (len(audio_list) - 1) // page_size * page_size
                    page_index = last_page_start
                    logger.info(f"Скорректированный индекс: {page_index}")
                
                # Обновляем сообщение
                text = vk_manager.get_audio_info_text(audio_list, page_index)
                keyboard = vk_manager.create_audio_keyboard(audio_list, page_index, prefix="play_audio")
                
                await query.edit_message_text(text, reply_markup=keyboard)
                logger.info(f"Страница успешно переключена на индекс {page_index}")
                
            except ValueError as e:
                logger.error(f"Ошибка ValueErrror при пагинации: {e}, data: {data}")
                await query.answer("❌ Ошибка: неверный номер страницы")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при пагинации: {e}")
                await query.answer("❌ Ошибка при переключении страницы")
        
        elif data.startswith("play_audio_"):
            # Воспроизведение конкретного трека (но не пагинация!)
            try:
                # Проверяем, что это не пагинация
                parts = data.split("_")
                if len(parts) == 3 and parts[0] == "play" and parts[1] == "audio":
                    # Формат: play_audio_0
                    audio_index = int(parts[2])
                    await play_audio_track(query, context, audio_index)
                else:
                    logger.error(f"Неверный формат callback_data: {data}")
                    await query.answer("❌ Ошибка: неверный формат команды")
                    
            except (ValueError, IndexError) as e:
                logger.error(f"Ошибка при обработке play_audio: {e}, data: {data}")
                await query.answer("❌ Ошибка: неверный индекс трека")
        
        else:
            await query.edit_message_text(
                "❌ Неизвестная команда",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
    
    except Exception as e:
        logger.error(f"Ошибка в обработчике callback: {e}")
        await query.edit_message_text(
            f"❌ Произошла ошибка: {e}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )

def main():
    """Основная функция"""
    # Загрузка токена из файла при запуске
    vk_manager.load_token_from_file()
    
    # Создание приложения
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("token", token_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # Добавляем обработчик токена
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token))
    
    # Добавляем обработчик поискового запроса
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query))
    
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Запуск бота
    logger.info("Бот запущен")
    application.run_polling()

if __name__ == "__main__":
    main()