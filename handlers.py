# handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import CallbackContext
from config import logger, PROGRAM_INFO, SUBSCRIPTION_CONFIG, FREE_REQUESTS_CONFIG
from vk_manager import vk_manager
from subscription_manager import subscription_manager
from utils import get_audio_info_text, create_audio_keyboard, format_subscription_period, get_time_left_text
import tempfile
import os
from datetime import datetime

def start(update: Update, context: CallbackContext):
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
        [InlineKeyboardButton("💎 Подписка", callback_data="subscription_required")],
        [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(welcome_text, reply_markup=reply_markup)

def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    help_text = (
        "VK Moosic Player Bot - Помощь\n\n"
        "Основные команды:\n"
        "/start - Начать работу с ботом\n"
        "/token - Установить VK токен\n"
        "/menu - Главное меню\n"
        "/subscription - Управление подпиской\n"
        "/help - Показать эту справку\n\n"
        "Для работы с ботом необходим VK токен с доступом к аудио.\n"
        "Для поиска музыки доступно 10 бесплатных запросов, затем требуется подписка."
    )
    update.message.reply_text(help_text)

def token_command(update: Update, context: CallbackContext):
    """Обработчик команды /token"""
    update.message.reply_text(
        "🔑 Пожалуйста, отправьте ваш VK токен. "
        "Вы можете получить его здесь: https://vkhost.github.io/\n\n"
        "⚠️ Никому не передавайте ваш токен!"
    )
    context.user_data['awaiting_token'] = True

def subscription_command(update: Update, context: CallbackContext):
    """Обработчик команды /subscription"""
    show_subscription_menu(update.message, context)

def handle_token(update: Update, context: CallbackContext):
    """Обработчик ввода токена"""
    token = update.message.text.strip()

    if not token:
        update.message.reply_text("❌ Токен не может быть пустым")
        return

    old_token = vk_manager.token
    vk_manager.set_token(token)

    validity = vk_manager.check_token_validity()
    if not validity["valid"]:
        update.message.reply_text(f"❌ Токен невалиден: {validity.get('error_msg')}")
        vk_manager.token = old_token
        return

    user_info = validity["user_info"]
    first_name = user_info.get('first_name', '')
    last_name = user_info.get('last_name', '')

    vk_manager.save_token_to_file()

    update.message.reply_text(
        f"✅ Токен успешно установлен!\n"
        f"👤 Пользователь: {first_name} {last_name}\n\n"
        "Теперь вы можете использовать главное меню: /menu"
    )

def menu_command(update: Update, context: CallbackContext):
    """Обработчик команды /menu"""
    show_main_menu(update, context)

def show_main_menu(update: Update, context: CallbackContext):
    """Показать главное меню"""
    if not vk_manager.token:
        keyboard = [
            [InlineKeyboardButton("🔑 Установить токен", callback_data="set_token")],
            [InlineKeyboardButton("💎 Подписка", callback_data="subscription_required")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "❌ Токен не установлен. Сначала установите VK токен.",
            reply_markup=reply_markup
        )
        return

    # Проверяем валидность токена
    validity = vk_manager.check_token_validity()
    if not validity["valid"]:
        keyboard = [
            [InlineKeyboardButton("🔑 Установить токен", callback_data="set_token")],
            [InlineKeyboardButton("💎 Подписка", callback_data="subscription_required")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"❌ Токен невалиден: {validity.get('error_msg')}",
            reply_markup=reply_markup
        )
        return

    user_info = validity["user_info"]
    first_name = user_info.get('first_name', '')
    last_name = user_info.get('last_name', '')

    # Проверяем статус подписки и запросов
    user_id = update.message.from_user.id
    is_subscribed = subscription_manager.is_subscribed(user_id)

    if is_subscribed:
        subscription_status = "✅ Активна"
        requests_status = "∞ неограниченно"
    else:
        subscription_status = "❌ Не активна"
        requests_info = subscription_manager.get_free_requests_info(user_id)
        requests_status = f"{requests_info['remaining']}/10"

    keyboard = [
        [InlineKeyboardButton("🎵 Моя музыка", callback_data="my_music")],
        [InlineKeyboardButton("👥 Друзья", callback_data="friends_music")],
        [InlineKeyboardButton("👥 Группы", callback_data="groups_music")],
        [InlineKeyboardButton("📋 Плейлисты", callback_data="playlists")],
        [InlineKeyboardButton("🔍 Поиск музыки", callback_data="search_music")],
        [InlineKeyboardButton("📻 Рекомендации", callback_data="recommendations")],
        [InlineKeyboardButton("🤖 Алгоритмы", callback_data="algorithmic_mixes")],
        [InlineKeyboardButton("💎 Управление подпиской", callback_data="subscription_required")],
        [InlineKeyboardButton("📊 Мои запросы", callback_data="my_requests_info")],
        [InlineKeyboardButton("⚙️ Управление токеном", callback_data="token_management")],
        [InlineKeyboardButton("ℹ️ О программе", callback_data="program_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        f"👤 {first_name} {last_name}\n"
        f"💎 Подписка: {subscription_status}\n"
        f"🔍 Бесплатные запросы: {requests_status}\n"
        "🎵 Выберите действие:",
        reply_markup=reply_markup
    )

def show_main_menu_from_query(query, context: CallbackContext):
    """Показать главное меню из callback query"""
    if not vk_manager.token:
        keyboard = [
            [InlineKeyboardButton("🔑 Установить токен", callback_data="set_token")],
            [InlineKeyboardButton("💎 Подписка", callback_data="subscription_required")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            query.edit_message_text(
                "❌ Токен не установлен. Сначала установите VK токен.",
                reply_markup=reply_markup
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Токен не установлен. Сначала установите VK токен.",
                reply_markup=reply_markup
            )
        return

    validity = vk_manager.check_token_validity()
    if not validity["valid"]:
        keyboard = [
            [InlineKeyboardButton("🔑 Установить токен", callback_data="set_token")],
            [InlineKeyboardButton("💎 Подписка", callback_data="subscription_required")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            query.edit_message_text(
                f"❌ Токен невалиден: {validity.get('error_msg')}",
                reply_markup=reply_markup
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Токен невалиден: {validity.get('error_msg')}",
                reply_markup=reply_markup
            )
        return

    user_info = validity["user_info"]
    first_name = user_info.get('first_name', '')
    last_name = user_info.get('last_name', '')

    # Проверяем статус подписки и запросов
    user_id = query.from_user.id
    is_subscribed = subscription_manager.is_subscribed(user_id)

    if is_subscribed:
        subscription_status = "✅ Активна"
        requests_status = "∞ неограниченно"
    else:
        subscription_status = "❌ Не активна"
        requests_info = subscription_manager.get_free_requests_info(user_id)
        requests_status = f"{requests_info['remaining']}/10"

    keyboard = [
        [InlineKeyboardButton("🎵 Моя музыка", callback_data="my_music")],
        [InlineKeyboardButton("👥 Друзья", callback_data="friends_music")],
        [InlineKeyboardButton("👥 Группы", callback_data="groups_music")],
        [InlineKeyboardButton("📋 Плейлисты", callback_data="playlists")],
        [InlineKeyboardButton("🔍 Поиск музыки", callback_data="search_music")],
        [InlineKeyboardButton("📻 Рекомендации", callback_data="recommendations")],
        [InlineKeyboardButton("🤖 Алгоритмы", callback_data="algorithmic_mixes")],
        [InlineKeyboardButton("💎 Управление подпиской", callback_data="subscription_required")],
        [InlineKeyboardButton("📊 Мои запросы", callback_data="my_requests_info")],
        [InlineKeyboardButton("⚙️ Управление токеном", callback_data="token_management")],
        [InlineKeyboardButton("ℹ️ О программе", callback_data="program_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        query.edit_message_text(
            f"👤 {first_name} {last_name}\n"
            f"💎 Подписка: {subscription_status}\n"
            f"🔍 Бесплатные запросы: {requests_status}\n"
            "🎵 Выберите действие:",
            reply_markup=reply_markup
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"👤 {first_name} {last_name}\n"
                 f"💎 Подписка: {subscription_status}\n"
                 f"🔍 Бесплатные запросы: {requests_status}\n"
                 "🎵 Выберите действие:",
            reply_markup=reply_markup
        )

def show_program_info(query):
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

    try:
        query.edit_message_text(info_text, reply_markup=reply_markup, parse_mode='HTML')
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=info_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

def show_info(query):
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

    try:
        query.edit_message_text(info_text, reply_markup=reply_markup, parse_mode='HTML')
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=info_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

def show_token_management(query):
    """Показать меню управления токеном"""
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить токен", callback_data="check_token")],
        [InlineKeyboardButton("🔑 Изменить токен", callback_data="set_token")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        query.edit_message_text(
            "⚙️ Управление токеном:",
            reply_markup=reply_markup
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⚙️ Управление токеном:",
            reply_markup=reply_markup
        )

def show_my_music(query, context: CallbackContext):
    """Показать мою музыку"""
    result = vk_manager.get_my_audio_list()
    if not result["success"]:
        try:
            query.edit_message_text(
                f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        return

    audio_list = result["audio_list"]
    if not audio_list:
        try:
            query.edit_message_text(
                "🎵 У вас нет аудиозаписей",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🎵 У вас нет аудиозаписей",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        return

    # Сохраняем список аудиозаписей в контексте
    context.user_data['current_audio_list'] = audio_list
    context.user_data['audio_source'] = 'my_music'

    text = get_audio_info_text(audio_list)
    keyboard = create_audio_keyboard(audio_list, prefix="play_audio")

    try:
        query.edit_message_text(text, reply_markup=keyboard)
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=keyboard
        )

def show_friends_list(query, context: CallbackContext):
    """Показать список друзей"""
    result = vk_manager.get_friends_list()
    if not result["success"]:
        try:
            query.edit_message_text(
                f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        return

    friends = result["friends"]
    if not friends:
        try:
            query.edit_message_text(
                "👥 У вас нет друзей или доступ ограничен",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="👥 У вас нет друзей или доступ ограничен",
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

    try:
        query.edit_message_text(
            "👥 Выберите друга для просмотра музыки:",
            reply_markup=reply_markup
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👥 Выберите друга для просмотра музыки:",
            reply_markup=reply_markup
        )

def show_groups_list(query, context: CallbackContext):
    """Показать список групп"""
    result = vk_manager.get_groups_list()
    if not result["success"]:
        try:
            query.edit_message_text(
                f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        return

    groups = result["groups"]
    if not groups:
        try:
            query.edit_message_text(
                "👥 У вас нет групп или доступ ограничен",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="👥 У вас нет групп или доступ ограничен",
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

    try:
        query.edit_message_text(
            "👥 Выберите группу для просмотра музыки:",
            reply_markup=reply_markup
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👥 Выберите группу для просмотра музыки:",
            reply_markup=reply_markup
        )

def show_playlists(query, context: CallbackContext):
    """Показать список плейлистов"""
    result = vk_manager.get_playlists()
    if not result["success"]:
        try:
            query.edit_message_text(
                f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        return

    playlists = result["playlists"]
    if not playlists:
        try:
            query.edit_message_text(
                "📋 У вас нет плейлистов",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="📋 У вас нет плейлистов",
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

    try:
        query.edit_message_text(
            "📋 Выберите плейлист:",
            reply_markup=reply_markup
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="📋 Выберите плейлист:",
            reply_markup=reply_markup
        )

def show_recommendations(query, context: CallbackContext):
    """Показать рекомендации"""
    result = vk_manager.get_recommendations()
    if not result["success"]:
        try:
            query.edit_message_text(
                f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        return

    audio_list = result["audio_list"]
    if not audio_list:
        try:
            query.edit_message_text(
                "🎵 Нет рекомендаций",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🎵 Нет рекомендаций",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        return

    # Сохраняем список аудиозаписей в контексте
    context.user_data['current_audio_list'] = audio_list
    context.user_data['audio_source'] = 'recommendations'

    text = get_audio_info_text(audio_list)
    keyboard = create_audio_keyboard(audio_list, prefix="play_audio")

    try:
        query.edit_message_text(text, reply_markup=keyboard)
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=keyboard
        )

def show_algorithmic_mixes(query, context: CallbackContext):
    """Показать алгоритмические подборки"""
    result = vk_manager.get_recommendations()
    if not result["success"]:
        try:
            query.edit_message_text(
                f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Ошибка: {result.get('error')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        return

    audio_list = result["audio_list"]
    if not audio_list:
        try:
            query.edit_message_text(
                "🤖 Нет алгоритмических подборок",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🤖 Нет алгоритмических подборок",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        return

    # Сохраняем список аудиозаписей в контексте
    context.user_data['current_audio_list'] = audio_list
    context.user_data['audio_source'] = 'algorithmic_mixes'

    text = get_audio_info_text(audio_list)
    keyboard = create_audio_keyboard(audio_list, prefix="play_audio")

    try:
        query.edit_message_text(text, reply_markup=keyboard)
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=keyboard
        )

def handle_search_request(query, context: CallbackContext):
    """Обработчик запроса поиска музыки с проверкой бесплатных запросов"""
    user_id = query.from_user.id

    # Проверяем подписку
    if subscription_manager.is_subscribed(user_id):
        try:
            query.edit_message_text(
                "🔍 Введите поисковый запрос:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🔍 Введите поисковый запрос:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        context.user_data['awaiting_search_query'] = True
        return

    # Проверяем бесплатные запросы
    requests_info = subscription_manager.get_free_requests_info(user_id)

    if requests_info['remaining'] > 0:
        # Есть бесплатные запросы - позволяем поиск
        context.user_data['free_search_request'] = True
        context.user_data['awaiting_search_query'] = True

        text = (
            f"🔍 Введите поисковый запрос:\n\n"
            f"📊 У вас осталось {requests_info['remaining']} "
            f"бесплатных запросов из {FREE_REQUESTS_CONFIG['max_free_requests']}\n\n"
            f"📅 Сброс через: {requests_info['days_to_reset']} дней"
        )

        try:
            query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
    else:
        # Нет бесплатных запросов - предлагаем подписку
        show_subscription_required_with_free_info(query, context, requests_info)

def handle_search_query(update: Update, context: CallbackContext):
    """Обработчик ввода поискового запроса с учетом бесплатных запросов"""
    if not context.user_data.get('awaiting_search_query'):
        return

    user_id = update.message.from_user.id

    # Проверяем подписку
    if subscription_manager.is_subscribed(user_id):
        # Пользователь с подпиской - обычная обработка
        process_search_with_subscription(update, context)
        context.user_data['awaiting_search_query'] = False
        return

    # Проверяем бесплатные запросы
    requests_info = subscription_manager.get_free_requests_info(user_id)

    if requests_info['remaining'] > 0:
        # Используем один бесплатный запрос
        updated_status = subscription_manager.use_free_request(user_id)

        # Показываем пользователю, что запрос использован
        remaining = updated_status["remaining"]

        message = update.message.reply_text(
            f"🔍 Ищу музыку...\n"
            f"📊 Использовано {FREE_REQUESTS_CONFIG['max_free_requests'] - remaining}/"
            f"{FREE_REQUESTS_CONFIG['max_free_requests']} бесплатных запросов"
        )

        # Выполняем поиск
        search_query = update.message.text.strip()
        result = vk_manager.search_audio(search_query)

        if result["success"]:
            audio_list = result.get("results", [])

            if audio_list:
                # Сохраняем список аудиозаписей в контексте
                context.user_data['current_audio_list'] = audio_list
                context.user_data['audio_source'] = 'search'

                text = f"🔍 Результаты поиска по запросу: '{search_query}'\n\n"
                text += get_audio_info_text(audio_list)
                text += f"\n\n📊 Осталось бесплатных запросов: {remaining}"

                # Добавляем кнопку для подписки если мало запросов
                keyboard = create_audio_keyboard(audio_list, prefix="play_audio")

                if remaining <= 3 and remaining > 0:
                    keyboard.inline_keyboard.append([
                        InlineKeyboardButton(
                            f"💎 Подписка (осталось {remaining} запросов)",
                            callback_data="subscribe"
                        )
                    ])
                elif remaining == 0:
                    keyboard.inline_keyboard.append([
                        InlineKeyboardButton(
                            "💎 Запросы закончились - оформите подписку",
                            callback_data="subscribe"
                        )
                    ])

                message.edit_text(text, reply_markup=keyboard)
            else:
                message.edit_text(
                    f"🎵 Ничего не найдено по запросу: '{search_query}'\n\n"
                    f"📊 Осталось бесплатных запросов: {remaining}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад", callback_data="search_music")],
                        [InlineKeyboardButton("💎 Подписка", callback_data="subscribe")]
                    ])
                )
        else:
            message.edit_text(
                f"❌ Ошибка поиска: {result.get('error')}\n\n"
                f"📊 Осталось бесплатных запросов: {remaining}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="search_music")],
                    [InlineKeyboardButton("💎 Подписка", callback_data="subscribe")]
                ])
            )
    else:
        # Нет бесплатных запросов
        show_subscription_required_with_free_info_message(update.message, context, requests_info)

    context.user_data['awaiting_search_query'] = False

def process_search_with_subscription(update: Update, context: CallbackContext):
    """Обработка поиска для пользователей с подпиской"""
    search_query = update.message.text.strip()

    message = update.message.reply_text("🔍 Ищу музыку...")

    # Выполняем поиск
    result = vk_manager.search_audio(search_query)

    if not result["success"]:
        message.edit_text(
            f"❌ Ошибка поиска: {result.get('error')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
        return

    audio_list = result.get("results", [])
    if not audio_list:
        message.edit_text(
            f"🎵 Ничего не найдено по запросу: '{search_query}'",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="search_music")]])
        )
        return

    # Сохраняем список аудиозаписей в контексте
    context.user_data['current_audio_list'] = audio_list
    context.user_data['audio_source'] = 'search'

    text = f"🔍 Результаты поиска по запросу: '{search_query}'\n\n"
    text += get_audio_info_text(audio_list)
    text += "\n\n✅ <b>У вас активная подписка - неограниченный поиск</b>"

    keyboard = create_audio_keyboard(audio_list, prefix="play_audio")

    message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')

def play_audio_track(query, context: CallbackContext, audio_index):
    """Воспроизвести аудиозапись"""
    audio_list = context.user_data.get('current_audio_list', [])
    if not audio_list or audio_index >= len(audio_list):
        query.answer("❌ Аудиозапись не найдена")
        return

    track = audio_list[audio_index]
    artist = track.get('artist', 'Unknown Artist')
    title = track.get('title', 'Unknown Title')
    url = track.get('url')

    if not url:
        query.answer("❌ Невозможно воспроизвести (отсутствует URL)")
        return

    # Показываем сообщение о загрузке
    loading_message = None
    try:
        loading_message = query.edit_message_text(f"📥 Загружаю: {artist} - {title}...")
    except:
        loading_message = context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"📥 Загружаю: {artist} - {title}..."
        )

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
        temp_filename = tmp_file.name

    try:
        # Скачиваем аудио
        logger.info(f"Скачиваю аудио: {url[:50]}...")
        success = vk_manager.download_audio(url, temp_filename)
        
        if not success:
            logger.error(f"Ошибка загрузки аудио: {artist} - {title}")
            error_text = f"❌ Ошибка загрузки: {artist} - {title}\n\nПопробуйте другой трек."
            try:
                query.edit_message_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад к списку", callback_data=f"{context.user_data.get('audio_source', 'main_menu')}")]])
                )
            except:
                context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=error_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад к списку", callback_data=f"{context.user_data.get('audio_source', 'main_menu')}")]])
                )
            return

        # Проверяем размер файла
        file_size = os.path.getsize(temp_filename)
        logger.info(f"Файл скачан, размер: {file_size} байт")
        
        if file_size == 0:
            logger.error("Файл пустой")
            error_text = f"❌ Файл пустой: {artist} - {title}"
            try:
                query.edit_message_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад к списку", callback_data=f"{context.user_data.get('audio_source', 'main_menu')}")]])
                )
            except:
                context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=error_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад к списку", callback_data=f"{context.user_data.get('audio_source', 'main_menu')}")]])
                )
            return

        # Отправляем аудиофайл
        with open(temp_filename, 'rb') as audio_file:
            audio_source = context.user_data.get('audio_source', 'main_menu')
            
            # Отправляем аудио
            context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_file,
                title=title,
                performer=artist,
                caption=f"🎵 {artist} - {title}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад к списку", callback_data=f"{audio_source}")]])
            )
            
            # Удаляем сообщение о загрузке
            try:
                if loading_message:
                    context.bot.delete_message(
                        chat_id=query.message.chat_id,
                        message_id=loading_message.message_id
                    )
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения о загрузке: {e}")

    except Exception as e:
        logger.error(f"Ошибка при отправке аудио: {e}")
        error_text = f"❌ Ошибка отправки аудио: {str(e)[:100]}"
        try:
            query.edit_message_text(
                error_text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад к списку", callback_data=f"{context.user_data.get('audio_source', 'main_menu')}")]])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=error_text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад к списку", callback_data=f"{context.user_data.get('audio_source', 'main_menu')}")]])
            )
    finally:
        # Удаляем временный файл
        try:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
                logger.info(f"Временный файл удален: {temp_filename}")
        except Exception as e:
            logger.error(f"Ошибка удаления временного файла: {e}")

# Функции для работы с подписками
def show_subscription_menu(message, context: CallbackContext):
    """Показать меню подписки"""
    keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="subscribe")],
        [InlineKeyboardButton("📋 Проверить подписку", callback_data="check_subscription")],
        [InlineKeyboardButton("ℹ️ Информация", callback_data="subscription_info")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]

    message.reply_text(
        "💎 <b>Управление подписки</b>\n\n"
        "Здесь вы можете оформить или продлить подписку.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

def show_subscription_required(query, context: CallbackContext):
    """Показать сообщение о необходимости подписки"""
    user_id = query.from_user.id

    if subscription_manager.is_subscribed(user_id):
        query.answer("✅ У вас уже есть активная подписка", show_alert=True)
        return

    # Получаем информацию о запросах
    requests_info = subscription_manager.get_free_requests_info(user_id)

    text = (
        "🔒 <b>Подписка на поиск музыки</b>\n\n"
        f"📊 Бесплатные запросы: использовано {requests_info['used']}/10\n"
        f"🔄 Сброс через: {requests_info['days_to_reset']} дней\n\n"
        "✨ <b>Преимущества подписки:</b>\n"
        "• 🔍 Неограниченный поиск музыки\n"
        "• 🎵 Приоритетная загрузка треков\n"
        "• ⚡ Быстрый доступ ко всем функциям\n"
        "• 📈 Статистика прослушиваний\n\n"
        "💎 <b>Выберите действие:</b>"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="subscribe")],
        [InlineKeyboardButton("📋 Мои запросы", callback_data="my_requests_info")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def show_subscription_required_with_free_info(query, context: CallbackContext, requests_info):
    """Показать сообщение о необходимости подписки с информацией о бесплатных запросах"""
    used = requests_info.get("used", 0)

    text = (
        f"🔒 <b>Бесплатные запросы закончились!</b>\n\n"
        f"📊 Вы использовали {used}/{FREE_REQUESTS_CONFIG['max_free_requests']} бесплатных запросов\n\n"
        f"✨ <b>Преимущества подписки:</b>\n"
        f"• 🔍 Неограниченный поиск музыки\n"
        f"• 🎵 Приоритетная загрузка треков\n"
        f"• ⚡ Быстрый доступ ко всем функциям\n"
        f"• 📈 Статистика прослушиваний\n\n"
        f"💎 <b>Выберите действие:</b>"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="subscribe")],
        [InlineKeyboardButton("📋 Мои запросы", callback_data="my_requests_info")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def show_subscription_required_with_free_info_message(message, context: CallbackContext, requests_info):
    """Показать сообщение о необходимости подписки для обычного сообщения"""
    used = requests_info.get("used", 0)

    text = (
        f"🔒 <b>Бесплатные запросы закончились!</b>\n\n"
        f"📊 Вы использовали {used}/{FREE_REQUESTS_CONFIG['max_free_requests']} бесплатных запросов\n\n"
        f"✨ <b>Преимущества подписки:</b>\n"
        f"• 🔍 Неограниченный поиск музыки\n"
        f"• 🎵 Приоритетная загрузка треков\n"
        f"• ⚡ Быстрый доступ ко всем функциям\n"
        f"• 📈 Статистика прослушиваний\n\n"
        f"💎 <b>Выберите действие:</b>"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="subscribe")],
        [InlineKeyboardButton("📋 Мои запросы", callback_data="my_requests_info")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]

    message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

def check_user_subscription(query, context: CallbackContext):
    """Проверить статус подписки пользователя"""
    user_id = query.from_user.id

    if subscription_manager.is_subscribed(user_id):
        time_left = subscription_manager.get_time_left(user_id)
        if time_left:
            time_left_text = get_time_left_text(time_left)

            text = (
                f"✅ <b>Подписка активна!</b>\n\n"
                f"⏳ <b>Осталось:</b> {time_left_text}\n\n"
                f"Все функции поиска доступны."
            )
        else:
            text = "❌ <b>Подписка не активна</b>"
    else:
        # Показываем информацию о бесплатных запросах
        requests_info = subscription_manager.get_free_requests_info(user_id)

        text = (
            f"❌ <b>Подписка не активна</b>\n\n"
            f"📊 <b>Бесплатные запросы:</b>\n"
            f"• Использовано: {requests_info['used']}/10\n"
            f"• Осталось: {requests_info['remaining']}\n"
            f"• Сброс через: {requests_info['days_to_reset']} дней\n\n"
            f"Для доступа к неограниченному поиску оформите подписку."
        )

    keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="subscribe")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def show_subscription_info(query, context: CallbackContext):
    """Показать информацию о подписке"""
    text = (
        "💎 <b>Информация о подписке</b>\n\n"

        "✨ <b>Что дает подписка:</b>\n"
        "• 🔍 Неограниченный поиск музыки\n"
        "• 🎵 Приоритетная загрузка треков\n"
        "• ⚡ Быстрый доступ ко всем функциям\n"
        "• 🆕 Ранний доступ к новым функциям\n\n"

        "📊 <b>Бесплатные запросы:</b>\n"
        f"• {FREE_REQUESTS_CONFIG['max_free_requests']} запросов бесплатно\n"
        f"• Сброс каждые {FREE_REQUESTS_CONFIG['requests_reset_days']} дней\n\n"

        "💳 <b>Способы оплаты:</b>\n"
        "• ⭐ Telegram Stars (встроенная система)\n"
        "• 🏦 Банковский перевод\n\n"

        "📞 <b>Поддержка:</b>\n"
        f"По всем вопросам обращайтесь: {SUBSCRIPTION_CONFIG['support_link']}"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="subscribe")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def show_my_requests_info(query, context: CallbackContext):
    """Показать информацию о моих запросах"""
    user_id = query.from_user.id
    requests_info = subscription_manager.get_free_requests_info(user_id)
    is_subscribed = subscription_manager.is_subscribed(user_id)

    if is_subscribed:
        time_left = subscription_manager.get_time_left(user_id)
        time_left_text = get_time_left_text(time_left) if time_left else "не определено"

        text = (
            f"💎 <b>У вас активная подписка!</b>\n\n"
            f"✅ Доступ к поиску: <b>Неограниченный</b>\n"
            f"⏳ Подписка активна еще: <b>{time_left_text}</b>\n\n"
            f"✨ Все функции доступны без ограничений!"
        )
    else:
        days_to_reset = requests_info.get("days_to_reset", 30)

        text = (
            f"📊 <b>Статистика ваших запросов:</b>\n\n"
            f"🔢 Использовано запросов: <b>{requests_info['used']}/10</b>\n"
            f"🎯 Осталось запросов: <b>{requests_info['remaining']}</b>\n"
            f"🔄 Сброс через: <b>{days_to_reset} дней</b>\n\n"
        )

        if requests_info['remaining'] == 0:
            text += "❌ <b>Бесплатные запросы закончились</b>\n"
            text += "💎 Оформите подписку для неограниченного поиска"
        elif requests_info['remaining'] <= 3:
            text += f"⚠️ <b>Осталось мало запросов ({requests_info['remaining']})</b>\n"
            text += "💎 Рекомендуем оформить подписку"
        else:
            text += "✅ <b>Вы можете продолжать поиск бесплатно</b>"

    keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="subscribe")],
        [InlineKeyboardButton("🔍 Поиск музыки", callback_data="search_music")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

# Дополнительные функции для работы с подписками
def show_payment_methods(query, context: CallbackContext):
    """Показать методы оплаты для подписки"""
    text = "💳 <b>Выберите способ оплаты:</b>\n\n"

    # Получаем статус подписки пользователя
    user_id = query.from_user.id
    is_subscribed = subscription_manager.is_subscribed(user_id)

    if is_subscribed:
        time_left = subscription_manager.get_time_left(user_id)
        if time_left:
            time_left_text = get_time_left_text(time_left)
            text += f"✅ У вас уже есть активная подписка\n⏳ Осталось: {time_left_text}\n\n"

    keyboard = [
        [InlineKeyboardButton("⭐ Оплата звездами", callback_data="pay_stars")],
        [InlineKeyboardButton("🏦 Банковская карта", callback_data="pay_bank")],
        [InlineKeyboardButton("🔙 Назад", callback_data="subscription_required")]
    ]

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def show_stars_subscription(query, context: CallbackContext):
    """Показать варианты подписки за звезды"""
    prices = subscription_manager.get_prices_stars()
    durations = subscription_manager.get_subscription_durations()

    if not prices:
        try:
            query.edit_message_text(
                "❌ Извините, оплата звездами временно недоступна.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="subscribe")]
                ])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Извините, оплата звездами временно недоступна.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="subscribe")]
                ])
            )
        return

    text = "⭐ <b>Выберите период подписки (оплата звездами):</b>\n\n"

    keyboard = []
    for period, price in prices.items():
        days = durations.get(period, 30)
        button_text = format_subscription_period(days, price, "⭐")
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"stars_{period}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="subscribe")])

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def show_bank_subscription(query, context: CallbackContext):
    """Показать варианты подписки за банковский перевод"""
    prices = subscription_manager.get_prices_bank()
    durations = subscription_manager.get_subscription_durations()
    bank_details = subscription_manager.get_bank_details()

    if not prices:
        try:
            query.edit_message_text(
                "❌ Извините, оплата банковской картой временно недоступна.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="subscribe")]
                ])
            )
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Извините, оплата банковской картой временно недоступна.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="subscribe")]
                ])
            )
        return

    text = (
        "🏦 <b>Выберите период подписки (банковский перевод):</b>\n\n"
        "<b>Реквизиты для оплаты:</b>\n"
        f"Банк: {bank_details.get('bank', 'Не указан')}\n"
        f"Получатель: {bank_details.get('recipient', 'Не указан')}\n"
        f"Номер карты: <code>{bank_details.get('card', 'Не указан')}</code>\n\n"
        "После оплаты отправьте скриншот чека.\n"
    )

    keyboard = []
    for period, price in prices.items():
        days = durations.get(period, 30)
        button_text = format_subscription_period(days, price, "₽")
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"bank_{period}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="subscribe")])

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def process_stars_payment(query, context: CallbackContext, period):
    """Обработка выбора периода для оплаты звездами"""
    prices = subscription_manager.get_prices_stars()
    price = prices.get(period)

    if not price:
        query.answer("❌ Ошибка: неверный период подписки", show_alert=True)
        return

    durations = subscription_manager.get_subscription_durations()
    days = durations.get(period, 30)

    # Форматируем текст периода
    if days < 30:
        period_text = f"{days} дней"
    elif days < 365:
        months = days // 30
        if months == 1:
            period_text = "1 месяц"
        elif 2 <= months <= 4:
            period_text = f"{months} месяца"
        else:
            period_text = f"{months} месяцев"
    else:
        years = days // 365
        if years == 1:
            period_text = "1 год"
        elif 2 <= years <= 4:
            period_text = f"{years} года"
        else:
            period_text = f"{years} лет"

    # Сохраняем информацию о платеже в контексте
    context.user_data['pending_stars_payment'] = {
        'period': period,
        'price': price,
        'period_text': period_text,
        'days': days
    }

    text = (
        f"⭐ <b>Подтверждение оплаты звездами</b>\n\n"
        f"<b>Период:</b> {period_text}\n"
        f"<b>Стоимость:</b> {price} звезд\n\n"
        f"Для продолжения оплаты нажмите кнопку ниже."
    )

    keyboard = [
        [InlineKeyboardButton(f"💳 Оплатить {price} ⭐", callback_data="confirm_stars_payment")],
        [InlineKeyboardButton("✖️ Отмена", callback_data="pay_stars")]
    ]

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def process_bank_payment(query, context: CallbackContext, period):
    """Обработка выбора периода для оплаты банковским переводом"""
    prices = subscription_manager.get_prices_bank()
    price = prices.get(period)

    if not price:
        query.answer("❌ Ошибка: неверный период подписки", show_alert=True)
        return

    durations = subscription_manager.get_subscription_durations()
    days = durations.get(period, 30)
    bank_details = subscription_manager.get_bank_details()

    # Форматируем текст периода
    if days < 30:
        period_text = f"{days} дней"
    elif days < 365:
        months = days // 30
        if months == 1:
            period_text = "1 месяц"
        elif 2 <= months <= 4:
            period_text = f"{months} месяца"
        else:
            period_text = f"{months} месяцев"
    else:
        years = days // 365
        if years == 1:
            period_text = "1 год"
        elif 2 <= years <= 4:
            period_text = f"{years} года"
        else:
            period_text = f"{years} лет"

    # Сохраняем информацию о платеже в контексте
    context.user_data['pending_bank_payment'] = {
        'period': period,
        'price': price,
        'period_text': period_text,
        'days': days,
        'user_id': query.from_user.id,
        'username': query.from_user.username or 'без username'
    }

    text = (
        f"🏦 <b>Детали оплаты</b>\n\n"
        f"<b>Период:</b> {period_text}\n"
        f"<b>Стоимость:</b> {price}₽\n\n"
        f"<b>Реквизиты для оплаты:</b>\n"
        f"Банк: {bank_details.get('bank', 'Не указан')}\n"
        f"Получатель: {bank_details.get('recipient', 'Не указан')}\n"
        f"Номер карты: <code>{bank_details.get('card', 'Не указан')}</code>\n\n"
        f"<b>Инструкция:</b>\n"
        f"1. Переведите {price}₽ на указанные реквизиты\n"
        f"2. Сделайте скриншот чека об оплате\n"
        f"3. Отправьте скриншот в этот чат\n\n"
        f"После проверки платежа подписка будет активирована."
    )

    keyboard = [
        [InlineKeyboardButton("📸 Отправить скриншот", callback_data="send_screenshot")],
        [InlineKeyboardButton("✖️ Отмена", callback_data="pay_bank")]
    ]

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def handle_screenshot_submission(update: Update, context: CallbackContext):
    """Обработчик отправки скриншота оплаты"""
    if not update.message.photo:
        update.message.reply_text(
            "❌ Пожалуйста, отправьте скриншот (фото) чека об оплате.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✖️ Отмена", callback_data="pay_bank")]
            ])
        )
        return

    # Проверяем, есть ли ожидающий платеж
    if 'pending_bank_payment' not in context.user_data:
        update.message.reply_text(
            "❌ Нет активного запроса на оплату. Начните сначала.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Оформить подписку", callback_data="subscribe")]
            ])
        )
        return

    payment_data = context.user_data['pending_bank_payment']
    screenshot = update.message.photo[-1]

    # Добавляем платеж в ожидание
    payment_id = subscription_manager.add_pending_payment(
        user_id=payment_data['user_id'],
        period=payment_data['period'],
        amount=payment_data['price'],
        screenshot_id=screenshot.file_id,
        username=payment_data['username']
    )

    # Отправляем уведомление админам
    for admin_id in SUBSCRIPTION_CONFIG["admin_id"]:
        try:
            context.bot.send_photo(
                chat_id=admin_id,
                photo=screenshot.file_id,
                caption=(
                    f"📸 <b>Новый платеж на проверку</b>\n\n"
                    f"🧾 <b>ID платежа:</b> <code>{payment_id}</code>\n"
                    f"👤 <b>Пользователь:</b> {payment_data['user_id']}\n"
                    f"📝 <b>Username:</b> @{payment_data['username']}\n"
                    f"⏳ <b>Период:</b> {payment_data['period_text']}\n"
                    f"💰 <b>Сумма:</b> {payment_data['price']}₽\n"
                    f"📅 <b>Дней:</b> {payment_data['days']}\n\n"
                    f"Для подтверждения используйте команду:\n"
                    f"<code>/confirm {payment_id}</code>"
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_confirm_{payment_id}"),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{payment_id}")
                    ]
                ])
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")

    # Отправляем подтверждение пользователю
    text = (
        f"✅ <b>Скриншот получен!</b>\n\n"
        f"Платеж отправлен на проверку администратору.\n"
        f"Обычно проверка занимает несколько минут.\n\n"
        f"<b>Детали платежа:</b>\n"
        f"Период: {payment_data['period_text']}\n"
        f"Сумма: {payment_data['price']}₽\n"
        f"ID платежа: <code>{payment_id}</code>"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 В меню", callback_data="main_menu")],
        [InlineKeyboardButton("📋 Проверить статус", callback_data="check_subscription")]
    ]

    update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

    # Очищаем данные о платеже
    context.user_data.pop('pending_bank_payment', None)

def handle_admin_command(update: Update, context: CallbackContext):
    """Обработчик админских команд"""
    user_id = update.message.from_user.id
    if user_id not in SUBSCRIPTION_CONFIG["admin_id"]:
        update.message.reply_text("❌ У вас нет доступа к админ-командам.")
        return

    if not context.args:
        show_admin_menu(update.message)
        return

    command = context.args[0].lower()

    if command == "stats":
        show_admin_stats(update.message)

    elif command == "users":
        show_admin_users(update.message, context)

    elif command == "pending":
        show_admin_pending(update.message, context)

    elif command == "confirm":
        if len(context.args) < 2:
            update.message.reply_text("Использование: /confirm PAYMENT_ID")
            return
        payment_id = context.args[1]
        confirm_payment_admin(update.message, context, payment_id)

    elif command == "reject":
        if len(context.args) < 2:
            update.message.reply_text("Использование: /reject PAYMENT_ID")
            return
        payment_id = context.args[1]
        reject_payment_admin(update.message, context, payment_id)

    elif command == "add":
        if len(context.args) < 3:
            update.message.reply_text("Использование: /add USER_ID DAYS")
            return
        try:
            target_user_id = int(context.args[1])
            days = int(context.args[2])
            add_subscription_admin(update.message, target_user_id, days)
        except ValueError:
            update.message.reply_text("❌ Ошибка: USER_ID и DAYS должны быть числами")

    elif command == "prices":
        show_admin_prices(update.message)

    elif command == "reset_requests":
        if len(context.args) < 2:
            update.message.reply_text("Использование: /reset_requests USER_ID")
            return
        try:
            target_user_id = int(context.args[1])
            subscription_manager.reset_free_requests(target_user_id)
            update.message.reply_text(f"✅ Запросы сброшены для пользователя {target_user_id}")
        except ValueError:
            update.message.reply_text("❌ Ошибка: USER_ID должен быть числом")

    else:
        update.message.reply_text(
            "🔐 <b>Доступные команды:</b>\n\n"
            "/admin stats - Статистика\n"
            "/admin users - Список пользователей\n"
            "/admin pending - Ожидающие платежи\n"
            "/admin confirm ID - Подтвердить платеж\n"
            "/admin reject ID - Отклонить платеж\n"
            "/admin add USER_ID DAYS - Добавить подписку\n"
            "/admin prices - Управление ценами\n"
            "/admin reset_requests USER_ID - Сбросить запросы",
            parse_mode='HTML'
        )

def show_admin_menu(message):
    """Показать админ-меню"""
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("⏳ Ожидающие платежи", callback_data="admin_pending")],
        [InlineKeyboardButton("💰 Управление ценами", callback_data="admin_prices")],
        [InlineKeyboardButton("🏦 Реквизиты", callback_data="admin_bank_details")],
        [InlineKeyboardButton("🔄 Сброс запросов", callback_data="admin_reset_requests")]
    ]

    message.reply_text(
        "🔐 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

def show_admin_stats(message):
    """Показать статистику админу"""
    stats = subscription_manager.get_statistics()

    text = (
        "📊 <b>Статистика подписок</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total']}</b>\n"
        f"🟢 Активных подписок: <b>{stats['active']}</b>\n"
        f"🔴 Истекших подписок: <b>{stats['expired']}</b>\n"
        f"⏳ Ожидающих платежей: <b>{stats['pending']}</b>\n\n"
        f"🆓 Пользователей с бесплатными запросами: <b>{stats['free_users']}</b>\n"
        f"🔢 Всего бесплатных запросов: <b>{stats['total_free_requests']}</b>\n\n"
        f"💎 Доход (приблизительно): <b>{stats['active'] * 500}₽/месяц</b>"
    )

    message.reply_text(text, parse_mode='HTML')

def show_admin_users(message, context: CallbackContext):
    """Показать список пользователей админу"""
    users = subscription_manager.get_all_users()

    if not users:
        message.reply_text("👥 <b>Нет пользователей</b>", parse_mode='HTML')
        return

    text = "👥 <b>Список пользователей:</b>\n\n"
    now = datetime.now()

    active_count = 0
    expired_count = 0

    for user_id, user_data in list(users.items())[:20]:  # Ограничиваем показ
        status = "🟢" if user_data.get('active') else "🔴"

        try:
            until = datetime.fromisoformat(user_data['subscription_until'])
            if until > now:
                days_left = (until - now).days
                time_info = f"{days_left}д"
                active_count += 1
            else:
                time_info = "истекла"
                expired_count += 1
        except:
            time_info = "ошибка"

        # Получаем информацию о запросах
        requests_info = subscription_manager.get_free_requests_info(int(user_id))
        requests_text = f"📊 {requests_info['remaining']}/10"

        text += f"{status} ID: <code>{user_id}</code> ({time_info}) {requests_text}\n"

    if len(users) > 20:
        text += f"\n... и еще {len(users) - 20} пользователей"

    text += f"\n\n📈 <b>Итого:</b> {active_count} активных, {expired_count} истекших"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить подписку", callback_data="admin_add_sub")],
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin_users")]
    ]

    message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

def show_admin_pending(message, context: CallbackContext):
    """Показать ожидающие платежи админу"""
    pending = subscription_manager.data.get("pending_payments", {})

    if not pending:
        message.reply_text("⏳ <b>Нет ожидающих платежей</b>", parse_mode='HTML')
        return

    text = "⏳ <b>Ожидающие платежи:</b>\n\n"

    for payment_id, payment in list(pending.items())[:10]:  # Ограничиваем показ
        user_id = payment['user_id']
        period = payment['period']
        amount = payment['amount']
        username = payment.get('username', 'без username')
        timestamp = datetime.fromisoformat(payment['timestamp'])
        time_ago = (datetime.now() - timestamp).seconds // 60  # минут назад

        text += f"🧾 <b>ID:</b> <code>{payment_id}</code>\n"
        text += f"👤 Пользователь: <code>{user_id}</code> (@{username})\n"
        text += f"⏳ Период: {period}\n"
        text += f"💰 Сумма: {amount}₽\n"
        text += f"⏰ Отправлен: {time_ago} минут назад\n"
        text += "─" * 30 + "\n"

    if len(pending) > 10:
        text += f"\n... и еще {len(pending) - 10} платежей"

    keyboard = [
        [
            InlineKeyboardButton("🔄 Обновить", callback_data="admin_pending"),
            InlineKeyboardButton("✅ Подтвердить все", callback_data="admin_confirm_all")
        ]
    ]

    message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

def confirm_payment_admin(message, context: CallbackContext, payment_id):
    """Подтвердить платеж админом"""
    payment = subscription_manager.get_pending_payment(payment_id)

    if not payment:
        message.reply_text(f"❌ Платеж с ID {payment_id} не найден.")
        return

    user_id = payment['user_id']
    period = payment['period']

    # Получаем длительность подписки
    durations = subscription_manager.get_subscription_durations()
    days = durations.get(period, 30)

    # Активируем подписку
    subscription_until = subscription_manager.add_user(user_id, days)

    # Удаляем из ожидания
    subscription_manager.remove_pending_payment(payment_id)

    # Отправляем уведомление пользователю
    try:
        context.bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ <b>Ваш платеж подтвержден!</b>\n\n"
                f"Подписка активирована до: {subscription_until.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Теперь вы можете использовать поиск музыки без ограничений."
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления пользователя {user_id}: {e}")

    message.reply_text(
        f"✅ Платеж подтвержден!\n"
        f"Пользователь: {user_id}\n"
        f"Подписка до: {subscription_until.strftime('%d.%m.%Y %H:%M')}"
    )

def reject_payment_admin(message, context: CallbackContext, payment_id):
    """Отклонить платеж админом"""
    payment = subscription_manager.get_pending_payment(payment_id)

    if not payment:
        message.reply_text(f"❌ Платеж с ID {payment_id} не найден.")
        return

    user_id = payment['user_id']

    # Удаляем из ожидания
    subscription_manager.remove_pending_payment(payment_id)

    # Отправляем уведомление пользователю
    try:
        context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ <b>Ваш платеж отклонен</b>\n\n"
                f"Пожалуйста, проверьте реквизиты и попробуйте снова.\n"
                f"Если вы считаете это ошибкой, свяжитесь с поддержкой."
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления пользователя {user_id}: {e}")

    message.reply_text(f"❌ Платеж отклонен. Пользователь уведомлен.")

def add_subscription_admin(message, user_id, days):
    """Добавить подписку вручную админом"""
    try:
        subscription_until = subscription_manager.add_user(user_id, days)

        # Отправляем уведомление пользователю
        try:
            message._bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎁 <b>Вам добавлена подписка!</b>\n\n"
                    f"Администратор добавил вам подписку на {days} дней.\n"
                    f"Подписка активна до: {subscription_until.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Теперь вы можете использовать поиск музыки без ограничений."
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Поиск музыки", callback_data="search_music")]
                ])
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя {user_id}: {e}")

        message.reply_text(
            f"✅ Подписка добавлена!\n"
            f"Пользователь: {user_id}\n"
            f"Дней: {days}\n"
            f"Активна до: {subscription_until.strftime('%d.%m.%Y %H:%M')}"
        )
    except Exception as e:
        logger.error(f"Ошибка добавления подписки: {e}")
        message.reply_text(f"❌ Ошибка: {e}")

def show_admin_prices(message):
    """Показать и управлять ценами админу"""
    prices_stars = subscription_manager.get_prices_stars()
    prices_bank = subscription_manager.get_prices_bank()

    text = "💰 <b>Текущие цены:</b>\n\n"

    text += "<b>⭐ Звезды:</b>\n"
    for period, price in prices_stars.items():
        text += f"  {period}: {price} ⭐\n"

    text += "\n<b>🏦 Банковский перевод:</b>\n"
    for period, price in prices_bank.items():
        text += f"  {period}: {price}₽\n"

    keyboard = [
        [
            InlineKeyboardButton("⭐ Изменить звезды", callback_data="admin_edit_stars"),
            InlineKeyboardButton("🏦 Изменить банк", callback_data="admin_edit_bank")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin")]
    ]

    message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

# Функция для обработки успешных платежей звездами
def handle_successful_payment(update: Update, context: CallbackContext):
    """Обработчик успешной оплаты звездами"""
    payment = update.message.successful_payment
    payload = payment.invoice_payload

    # Парсим payload: должно быть в формате subscription_{period}_{user_id}
    if not payload.startswith("subscription_"):
        logger.error(f"Неверный формат payload: {payload}")
        return

    try:
        # Извлекаем данные
        parts = payload.split("_")
        if len(parts) < 3:
            logger.error(f"Неполный payload: {payload}")
            return

        period = parts[1]
        user_id = int(parts[2])

        # Проверяем, что оплатил тот же пользователь
        if user_id != update.message.from_user.id:
            logger.error(f"ID пользователя не совпадает: {user_id} != {update.message.from_user.id}")
            update.message.reply_text("❌ Ошибка: неверный пользователь.")
            return

        # Получаем длительность подписки
        durations = subscription_manager.get_subscription_durations()
        days = durations.get(period, 30)

        # Активируем подписку
        subscription_until = subscription_manager.add_user(user_id, days)

        # Отправляем подтверждение
        text = (
            f"✅ <b>Оплата подтверждена!</b>\n\n"
            f"<b>Подписка активирована до:</b> {subscription_until.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Теперь вы можете использовать поиск музыки без ограничений."
        )

        keyboard = [
            [InlineKeyboardButton("🔍 Поиск музыки", callback_data="search_music")],
            [InlineKeyboardButton("🔙 В меню", callback_data="main_menu")]
        ]

        update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

        logger.info(f"Подписка активирована для пользователя {user_id} на {days} дней")

    except Exception as e:
        logger.error(f"Ошибка обработки платежа: {e}")
        update.message.reply_text(
            "❌ Произошла ошибка при обработке платежа. "
            "Пожалуйста, свяжитесь с поддержкой.",
            parse_mode='HTML'
        )

# Функция для обработки предварительной проверки платежа
def handle_pre_checkout(update: Update, context: CallbackContext):
    """Обработчик предварительной проверки платежа"""
    query = update.pre_checkout_query

    # Всегда подтверждаем запрос
    query.answer(ok=True)

    logger.info(f"Предварительная проверка платежа: {query.invoice_payload}")

def handle_message(update: Update, context: CallbackContext):
    """Обработчик всех сообщений (для админских команд и ввода токена)"""
    user_id = update.message.from_user.id

    # Обработка админских команд через обычные сообщения
    if user_id in SUBSCRIPTION_CONFIG["admin_id"]:
        text = update.message.text

        # Обработка изменения цены
        if 'admin_price_edit' in context.user_data:
            try:
                new_price = int(text)
                edit_data = context.user_data['admin_price_edit']
                payment_type = edit_data['type']
                period = edit_data['period']

                if payment_type == "stars":
                    subscription_manager.data["prices"]["stars"][period] = new_price
                else:
                    subscription_manager.data["prices"]["bank"][period] = new_price

                subscription_manager.save()

                update.message.reply_text(
                    f"✅ Цена обновлена: {new_price} {'⭐' if payment_type == 'stars' else '₽'}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад", callback_data=f"admin_prices_{payment_type}")]
                    ])
                )

                context.user_data.pop('admin_price_edit', None)
                return
            except ValueError:
                update.message.reply_text("❌ Ошибка: введите целое число")
                return

        # Обработка добавления подписки
        elif context.user_data.get('admin_adding_sub'):
            try:
                parts = text.split()
                if len(parts) != 2:
                    update.message.reply_text("❌ Неверный формат. Используйте: USER_ID DAYS")
                    return

                target_user_id = int(parts[0])
                days = int(parts[1])

                subscription_until = subscription_manager.add_user(target_user_id, days)

                update.message.reply_text(
                    f"✅ Подписка добавлена!\n"
                    f"Пользователь: {target_user_id}\n"
                    f"Дней: {days}\n"
                    f"Активна до: {subscription_until.strftime('%d.%m.%Y %H:%M')}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
                    ])
                )

                context.user_data.pop('admin_adding_sub', None)
                return
            except ValueError:
                update.message.reply_text("❌ Ошибка: введите числа")
                return

        # Обработка изменения реквизитов
        elif 'admin_editing' in context.user_data:
            field = context.user_data['admin_editing']

            if field == 'card':
                subscription_manager.data["bank_details"]["card"] = text
            elif field == 'bank':
                subscription_manager.data["bank_details"]["bank"] = text
            elif field == 'recipient':
                subscription_manager.data["bank_details"]["recipient"] = text

            subscription_manager.save()

            update.message.reply_text(
                f"✅ {field} обновлен!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="admin_bank_details")]
                ])
            )

            context.user_data.pop('admin_editing', None)
            return

    # Обработка скриншотов оплаты
    if update.message.photo and ('pending_bank_payment' in context.user_data):
        handle_screenshot_submission(update, context)
        return

    # Обработка ввода токена
    if context.user_data.get('awaiting_token'):
        handle_token(update, context)
        context.user_data.pop('awaiting_token', None)
        return

    # Обработка поискового запроса
    if context.user_data.get('awaiting_search_query'):
        handle_search_query(update, context)
        return

    # Если не распознали команду, показываем помощь
    help_command(update, context)

# Функции для работы с подписками (дополнительные)
def request_screenshot(query, context: CallbackContext):
    """Запрос скриншота оплаты"""
    keyboard = [
        [InlineKeyboardButton("✖️ Отменить", callback_data="subscribe")]
    ]

    try:
        query.edit_message_text(
            "📸 <b>Отправьте скриншот чека об оплате:</b>\n\n"
            "Просто отправьте фото с квитанцией об оплате.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="📸 <b>Отправьте скриншот чека об оплате:</b>\n\nПросто отправьте фото с квитанцией об оплате.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def confirm_payment(query, context: CallbackContext):
    """Подтверждение оплаты (для внутреннего использования)"""
    payment_data = context.user_data.get('pending_payment')

    if not payment_data:
        query.answer("❌ Нет данных о платеже", show_alert=True)
        return

    user_id = payment_data['user_id']
    period = payment_data['period']
    durations = subscription_manager.get_subscription_durations()
    days = durations.get(period, 30)

    # Активируем подписку
    subscription_until = subscription_manager.add_user(user_id, days)

    # Очищаем данные
    context.user_data.pop('pending_payment', None)

    # Отправляем подтверждение пользователю
    text = (
        f"✅ <b>Подписка активирована!</b>\n\n"
        f"<b>Активна до:</b> {subscription_until.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Теперь вы можете использовать поиск музыки без ограничений."
    )

    keyboard = [
        [InlineKeyboardButton("🔍 Поиск музыки", callback_data="search_music")],
        [InlineKeyboardButton("🔙 В меню", callback_data="main_menu")]
    ]

    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def cancel_payment(query, context: CallbackContext):
    """Отмена оплаты"""
    try:
        query.edit_message_text(
            "❌ Оплата отменена.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="subscribe")]])
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Оплата отменена.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="subscribe")]])
        )

# Обработчики админ callback-ов
def admin_confirm_payment(query, context: CallbackContext, payment_id):
    """Админ подтверждает платеж"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    payment = subscription_manager.get_pending_payment(payment_id)

    if not payment:
        try:
            query.edit_message_text(f"❌ Платеж с ID {payment_id} не найден.")
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Платеж с ID {payment_id} не найден."
            )
        return

    user_id = payment['user_id']
    period = payment['period']

    # Получаем длительность подписки
    durations = subscription_manager.get_subscription_durations()
    days = durations.get(period, 30)

    # Активируем подписку
    subscription_until = subscription_manager.add_user(user_id, days)

    # Удаляем из ожидания
    subscription_manager.remove_pending_payment(payment_id)

    # Отправляем уведомление пользователю
    try:
        context.bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ <b>Ваш платеж подтвержден!</b>\n\n"
                f"Подписка активирована до: {subscription_until.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Теперь вы можете использовать поиск музыки без ограничений."
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления пользователя {user_id}: {e}")

    try:
        query.edit_message_text(
            f"✅ Платеж подтвержден!\n"
            f"Пользователь: {user_id}\n"
            f"Подписка до: {subscription_until.strftime('%d.%m.%Y %H:%M')}"
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"✅ Платеж подтвержден!\nПользователь: {user_id}\nПодписка до: {subscription_until.strftime('%d.%m.%Y %H:%M')}"
        )

def admin_reject_payment(query, context: CallbackContext, payment_id):
    """Админ отклоняет платеж"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    payment = subscription_manager.get_pending_payment(payment_id)

    if not payment:
        try:
            query.edit_message_text(f"❌ Платеж с ID {payment_id} не найден.")
        except:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Платеж с ID {payment_id} не найден."
            )
        return

    user_id = payment['user_id']

    # Удаляем из ожидания
    subscription_manager.remove_pending_payment(payment_id)

    # Отправляем уведомление пользователю
    try:
        context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ <b>Ваш платеж отклонен</b>\n\n"
                f"Пожалуйста, проверьте реквизиты и попробуйте снова.\n"
                f"Если вы считаете это ошибкой, свяжитесь с поддержкой."
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления пользователя {user_id}: {e}")

    try:
        query.edit_message_text(f"❌ Платеж отклонен. Пользователь уведомлен.")
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Платеж отклонен. Пользователь уведомлен."
        )

def admin_reset_requests(query, context: CallbackContext):
    """Админ сбрасывает запросы"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    context.user_data['admin_resetting_requests'] = True

    keyboard = [
        [InlineKeyboardButton("✖️ Отмена", callback_data="admin")]
    ]

    try:
        query.edit_message_text(
            "<b>🔄 Сброс бесплатных запросов:</b>\n\n"
            "Введите ID пользователя для сброса:\n"
            "Пример: <code>123456789</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="<b>🔄 Сброс бесплатных запросов:</b>\n\nВведите ID пользователя для сброса:\nПример: <code>123456789</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def admin_edit_stars(query, context: CallbackContext):
    """Админ редактирует цены звезд"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    query.answer("ℹ️ Выберите период из списка выше")

def admin_edit_bank(query, context: CallbackContext):
    """Админ редактирует банковские цены"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    query.answer("ℹ️ Выберите период из списка выше")

def admin_change_card(query, context: CallbackContext):
    """Админ меняет номер карты"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    context.user_data['admin_editing'] = 'card'

    keyboard = [
        [InlineKeyboardButton("✖️ Отмена", callback_data="admin_bank_details")]
    ]

    try:
        query.edit_message_text(
            "<b>💳 Изменение номера карты:</b>\n\n"
            "Введите новый номер карты:\n"
            "Пример: <code>2202 2006 1234 5678</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="<b>💳 Изменение номера карты:</b>\n\nВведите новый номер карты:\nПример: <code>2202 2006 1234 5678</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def admin_change_bank(query, context: CallbackContext):
    """Админ меняет название банка"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    context.user_data['admin_editing'] = 'bank'

    keyboard = [
        [InlineKeyboardButton("✖️ Отмена", callback_data="admin_bank_details")]
    ]

    try:
        query.edit_message_text(
            "<b>🏦 Изменение названия банка:</b>\n\n"
            "Введите новое название банка:\n"
            "Пример: <code>Сбербанк</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="<b>🏦 Изменение названия банка:</b>\n\nВведите новое название банка:\nПример: <code>Сбербанк</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def admin_change_recipient(query, context: CallbackContext):
    """Админ меняет получателя"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    context.user_data['admin_editing'] = 'recipient'

    keyboard = [
        [InlineKeyboardButton("✖️ Отмена", callback_data="admin_bank_details")]
    ]

    try:
        query.edit_message_text(
            "<b>👤 Изменение получателя:</b>\n\n"
            "Введите ФИО получателя:\n"
            "Пример: <code>Иван Иванович Иванов</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="<b>👤 Изменение получателя:</b>\n\nВведите ФИО получателя:\nПример: <code>Иван Иванович Иванов</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def admin_add_sub(query, context: CallbackContext):
    """Админ добавляет подписку"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    context.user_data['admin_adding_sub'] = True

    keyboard = [
        [InlineKeyboardButton("✖️ Отмена", callback_data="admin_users")]
    ]

    try:
        query.edit_message_text(
            "<b>➕ Добавление подписки:</b>\n\n"
            "Введите данные в формате:\n"
            "<code>USER_ID DAYS</code>\n\n"
            "Пример: <code>123456789 30</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    except:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="<b>➕ Добавление подписки:</b>\n\nВведите данные в формате:\n<code>USER_ID DAYS</code>\n\nПример: <code>123456789 30</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

def admin_confirm_all(query, context: CallbackContext):
    """Админ подтверждает все платежи"""
    if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
        query.answer("❌ Нет доступа", show_alert=True)
        return

    pending = subscription_manager.data.get("pending_payments", {}).copy()
    confirmed_count = 0

    for payment_id, payment in pending.items():
        try:
            user_id = payment['user_id']
            period = payment['period']

            durations = subscription_manager.get_subscription_durations()
            days = durations.get(period, 30)

            subscription_manager.add_user(user_id, days)
            subscription_manager.remove_pending_payment(payment_id)
            confirmed_count += 1
        except Exception as e:
            logger.error(f"Ошибка подтверждения платежа {payment_id}: {e}")

    query.answer(f"✅ Подтверждено {confirmed_count} платежей", show_alert=True)

    # Обновляем сообщение
    show_admin_pending(query.message, context)
