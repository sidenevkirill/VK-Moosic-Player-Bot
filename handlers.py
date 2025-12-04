# handlers.py
import tempfile
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import logger, PROGRAM_INFO
from vk_manager import vk_manager
from utils import get_audio_info_text, create_audio_keyboard

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
    
    text = get_audio_info_text(audio_list)
    keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
    
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
    
    text = get_audio_info_text(audio_list)
    keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
    
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
    
    text = get_audio_info_text(audio_list)
    keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
    
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
    text += get_audio_info_text(audio_list)
    keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
    
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