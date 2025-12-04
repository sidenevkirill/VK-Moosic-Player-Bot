# utils.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import logger, PAGE_SIZE
from vk_manager import vk_manager

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