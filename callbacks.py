# callbacks.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import logger
from vk_manager import vk_manager
from handlers import (
    show_main_menu_from_query, show_info, show_program_info, 
    show_token_management, show_my_music, show_friends_list,
    show_groups_list, show_playlists, show_recommendations,
    show_algorithmic_mixes, handle_search_request,
    play_audio_track
)
from utils import get_audio_info_text, create_audio_keyboard

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
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
            
            text = get_audio_info_text(audio_list)
            keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
            
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
            
            text = get_audio_info_text(audio_list)
            keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
            
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
            
            text = get_audio_info_text(audio_list)
            keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
            
            await query.edit_message_text(text, reply_markup=keyboard)
        
        elif data.startswith("play_audio_page_"):
            # ПЕРЕКЛЮЧЕНИЕ СТРАНИЦ
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
                    from config import PAGE_SIZE
                    last_page_start = (len(audio_list) - 1) // PAGE_SIZE * PAGE_SIZE
                    page_index = last_page_start
                    logger.info(f"Скорректированный индекс: {page_index}")
                
                # Обновляем сообщение
                text = get_audio_info_text(audio_list, page_index)
                keyboard = create_audio_keyboard(audio_list, page_index, prefix="play_audio")
                
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