from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from config import logger, PAGE_SIZE, SUBSCRIPTION_CONFIG, FREE_REQUESTS_CONFIG
from subscription_manager import subscription_manager

def get_audio_info_text(audio_list, start_index=0, page_size=PAGE_SIZE):
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

def create_audio_keyboard(audio_list, start_index=0, page_size=PAGE_SIZE, prefix="play_audio"):
    """Создать клавиатуру для списка аудиозаписей с пагинацией"""
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

def format_subscription_period(days: int, price: int, currency: str) -> str:
    """Форматировать период подписки для отображения"""
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
    
    return f"{period_text} - {price} {currency}"

def get_time_left_text(time_left):
    """Получить текст с оставшимся временем"""
    if not time_left:
        return "не активно"
    
    days = time_left.days
    hours = time_left.seconds // 3600
    minutes = (time_left.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        if days == 1:
            parts.append("1 день")
        elif 2 <= days <= 4:
            parts.append(f"{days} дня")
        else:
            parts.append(f"{days} дней")
    
    if hours > 0:
        if hours == 1:
            parts.append("1 час")
        elif 2 <= hours <= 4:
            parts.append(f"{hours} часа")
        else:
            parts.append(f"{hours} часов")
    
    if minutes > 0 or not parts:
        if minutes == 1:
            parts.append("1 минута")
        elif 2 <= minutes <= 4:
            parts.append(f"{minutes} минуты")
        else:
            parts.append(f"{minutes} минут")
    
    return ", ".join(parts)

async def create_invoice(bot, chat_id: int, period: str, price: int):
    """Создать инвойс для оплаты звездами"""
    durations = subscription_manager.get_subscription_durations()
    days = durations.get(period, 30)
    
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
    
    title = f"Подписка на {period_text}"
    description = f"Доступ к поиску музыки на {period_text}"
    
    try:
        await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=f"subscription_{period}_{chat_id}",
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=title, amount=price)],
            provider_token=SUBSCRIPTION_CONFIG.get("payment_provider_token", "TEST"),
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка создания инвойса: {e}")
        return False

def get_admin_keyboard():
    """Клавиатура админ-панели"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("💰 Цены (Звезды)", callback_data="admin_prices_stars")],
        [InlineKeyboardButton("💳 Цены (Банк)", callback_data="admin_prices_bank")],
        [InlineKeyboardButton("🏦 Реквизиты", callback_data="admin_bank_details")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("⏳ Ожидающие платежи", callback_data="admin_pending")],
        [InlineKeyboardButton("🔄 Сброс запросов", callback_data="admin_reset_requests")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ])

def get_price_periods_keyboard(payment_type: str):
    """Клавиатура выбора периода для изменения цены"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1 месяц", callback_data=f"price_{payment_type}_1_month")],
        [InlineKeyboardButton("3 месяца", callback_data=f"price_{payment_type}_3_months")],
        [InlineKeyboardButton("6 месяцев", callback_data=f"price_{payment_type}_6_months")],
        [InlineKeyboardButton("1 год", callback_data=f"price_{payment_type}_1_year")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin")]
    ])

def get_requests_status_text(user_id: int) -> str:
    """Получить текст со статусом запросов"""
    if subscription_manager.is_subscribed(user_id):
        return "✅ <b>Подписка активна</b> - неограниченный поиск"
    
    requests_info = subscription_manager.get_free_requests_info(user_id)
    
    if requests_info["remaining"] == 0:
        return f"❌ <b>Запросы закончились</b> (использовано {requests_info['used']}/10)"
    else:
        return (
            f"📊 <b>Бесплатные запросы:</b> {requests_info['remaining']}/10\n"
            f"🔄 <b>Сброс через:</b> {requests_info['days_to_reset']} дней"
        )
