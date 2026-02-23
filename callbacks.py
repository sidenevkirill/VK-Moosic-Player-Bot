# callbacks.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import CallbackContext
from config import logger, SUBSCRIPTION_CONFIG, SUBSCRIPTION_REQUIRED_FEATURES
from vk_manager import vk_manager
from handlers import (
    show_main_menu_from_query, show_info, show_program_info, 
    show_token_management, show_my_music, show_friends_list,
    show_groups_list, show_playlists, show_recommendations,
    show_algorithmic_mixes, handle_search_request,
    play_audio_track, show_subscription_menu, show_subscription_required,
    check_user_subscription, show_subscription_info,
    show_payment_methods, show_stars_subscription, show_bank_subscription,
    process_stars_payment, process_bank_payment, request_screenshot,
    confirm_payment, cancel_payment, show_my_requests_info,
    admin_confirm_payment, admin_reject_payment, admin_reset_requests,
    admin_edit_stars, admin_edit_bank, admin_change_card,
    admin_change_bank, admin_change_recipient, admin_add_sub,
    admin_confirm_all
)
from utils import get_audio_info_text, create_audio_keyboard, format_subscription_period, get_admin_keyboard, get_price_periods_keyboard
from subscription_manager import subscription_manager
from datetime import datetime

def handle_callback_query(update: Update, context: CallbackContext):
    """Обработчик callback запросов"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    logger.info(f"Получен callback: {data}")
    
    try:
        # АДМИН КОМАНДЫ
        if data == "admin":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ У вас нет доступа к админ-панели", show_alert=True)
                return
            
            query.edit_message_text(
                "🔐 <b>Админ-панель подписок</b>",
                reply_markup=get_admin_keyboard(),
                parse_mode='HTML'
            )
            return
        
        elif data == "admin_stats":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            stats = subscription_manager.get_statistics()
            text = (
                "📊 <b>Статистика подписок:</b>\n\n"
                f"👥 Всего пользователей: {stats['total']}\n"
                f"🟢 Активных подписок: {stats['active']}\n"
                f"🔴 Истекших подписок: {stats['expired']}\n"
                f"⏳ Ожидающих платежей: {stats['pending']}"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="admin")]
            ]
            
            query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif data == "admin_prices_stars":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            query.edit_message_text(
                "<b>💰 Изменение цен (Звезды):</b>\n\nВыберите период:",
                reply_markup=get_price_periods_keyboard("stars"),
                parse_mode='HTML'
            )
            return
        
        elif data == "admin_prices_bank":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            query.edit_message_text(
                "<b>💰 Изменение цен (Банк):</b>\n\nВыберите период:",
                reply_markup=get_price_periods_keyboard("bank"),
                parse_mode='HTML'
            )
            return
        
        elif data.startswith("price_"):
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            parts = data.replace("price_", "").split("_", 1)
            payment_type = parts[0]
            period = parts[1]
            
            if payment_type == "stars":
                current_price = subscription_manager.get_prices_stars()[period]
                currency = "⭐"
            else:
                current_price = subscription_manager.get_prices_bank()[period]
                currency = "₽"
            
            # Сохраняем в контекст
            context.user_data['admin_price_edit'] = {
                'type': payment_type,
                'period': period
            }
            
            keyboard = [
                [InlineKeyboardButton("✖️ Отмена", callback_data=f"admin_prices_{payment_type}")]
            ]
            
            query.edit_message_text(
                f"<b>Текущая цена:</b> {current_price} {currency}\n\n"
                f"Введите новую цену (целое число):",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif data == "admin_bank_details":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            bank_details = subscription_manager.get_bank_details()
            
            keyboard = [
                [InlineKeyboardButton("💳 Изменить номер карты", callback_data="admin_change_card")],
                [InlineKeyboardButton("🏦 Изменить банк", callback_data="admin_change_bank")],
                [InlineKeyboardButton("👤 Изменить получателя", callback_data="admin_change_recipient")],
                [InlineKeyboardButton("🔙 Назад", callback_data="admin")]
            ]
            
            text = (
                "<b>🏦 Текущие реквизиты:</b>\n\n"
                f"<b>Банк:</b> {bank_details.get('bank', 'Не указан')}\n"
                f"<b>Получатель:</b> {bank_details.get('recipient', 'Не указан')}\n"
                f"<b>Номер карты:</b> <code>{bank_details.get('card', 'Не указан')}</code>"
            )
            
            query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif data == "admin_users":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            users = subscription_manager.get_all_users()
            now = datetime.now()
            
            if not users:
                text = "👥 <b>Нет пользователей</b>"
            else:
                text = "👥 <b>Список пользователей:</b>\n\n"
                for i, (user_id, user_data) in enumerate(list(users.items())[:20]):
                    status = "🟢" if user_data.get('active') else "🔴"
                    until = datetime.fromisoformat(user_data['subscription_until'])
                    if until > now:
                        days_left = (until - now).days
                        time_info = f"{days_left}д"
                    else:
                        time_info = "истекла"
                    
                    text += f"{i+1}. {status} ID: {user_id} ({time_info})\n"
                
                if len(users) > 20:
                    text += f"\n... и еще {len(users) - 20} пользователей"
            
            keyboard = [
                [InlineKeyboardButton("➕ Добавить подписку", callback_data="admin_add_sub")],
                [InlineKeyboardButton("🔙 Назад", callback_data="admin")]
            ]
            
            query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif data == "admin_pending":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            pending = subscription_manager.data.get("pending_payments", {})
            
            if not pending:
                text = "⏳ <b>Нет ожидающих платежей</b>"
            else:
                text = "⏳ <b>Ожидающие платежи:</b>\n\n"
                for payment_id, payment in list(pending.items())[:10]:
                    user_id = payment['user_id']
                    period = payment['period']
                    amount = payment['amount']
                    username = payment.get('username', 'без username')
                    
                    text += f"🧾 <b>ID:</b> {payment_id[:8]}...\n"
                    text += f"👤 Пользователь: {user_id} (@{username})\n"
                    text += f"⏳ Период: {period}\n"
                    text += f"💰 Сумма: {amount}\n"
                    text += "─" * 20 + "\n"
                
                if len(pending) > 10:
                    text += f"\n... и еще {len(pending) - 10} платежей"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_pending")],
                [InlineKeyboardButton("🔙 Назад", callback_data="admin")]
            ]
            
            query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif data == "admin_add_sub":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            context.user_data['admin_adding_sub'] = True
            
            keyboard = [
                [InlineKeyboardButton("✖️ Отмена", callback_data="admin_users")]
            ]
            
            query.edit_message_text(
                "<b>➕ Добавление подписки:</b>\n\n"
                "Введите данные в формате:\n"
                "<code>USER_ID DAYS</code>\n\n"
                "Пример: <code>123456789 30</code>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        # АДМИН ИЗМЕНЕНИЕ РЕКВИЗИТОВ
        elif data == "admin_change_card":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            context.user_data['admin_editing'] = 'card'
            
            keyboard = [
                [InlineKeyboardButton("✖️ Отмена", callback_data="admin_bank_details")]
            ]
            
            query.edit_message_text(
                "<b>💳 Изменение номера карты:</b>\n\n"
                "Введите новый номер карты:\n"
                "Пример: <code>2202 2006 1234 5678</code>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif data == "admin_change_bank":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            context.user_data['admin_editing'] = 'bank'
            
            keyboard = [
                [InlineKeyboardButton("✖️ Отмена", callback_data="admin_bank_details")]
            ]
            
            query.edit_message_text(
                "<b>🏦 Изменение названия банка:</b>\n\n"
                "Введите новое название банка:\n"
                "Пример: <code>Сбербанк</code>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif data == "admin_change_recipient":
            if query.from_user.id not in SUBSCRIPTION_CONFIG["admin_id"]:
                query.answer("❌ Нет доступа", show_alert=True)
                return
            
            context.user_data['admin_editing'] = 'recipient'
            
            keyboard = [
                [InlineKeyboardButton("✖️ Отмена", callback_data="admin_bank_details")]
            ]
            
            query.edit_message_text(
                "<b>👤 Изменение получателя:</b>\n\n"
                "Введите ФИО получателя:\n"
                "Пример: <code>Иван Иванович Иванов</code>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif data.startswith("admin_confirm_"):
            payment_id = data.replace("admin_confirm_", "")
            admin_confirm_payment(query, context, payment_id)
            return
        
        elif data.startswith("admin_reject_"):
            payment_id = data.replace("admin_reject_", "")
            admin_reject_payment(query, context, payment_id)
            return
        
        elif data == "admin_reset_requests":
            admin_reset_requests(query, context)
            return
        
        elif data == "admin_edit_stars":
            admin_edit_stars(query, context)
            return
        
        elif data == "admin_edit_bank":
            admin_edit_bank(query, context)
            return
        
        elif data == "admin_confirm_all":
            admin_confirm_all(query, context)
            return
        
        # ОБЫЧНЫЕ КОМАНДЫ ПОЛЬЗОВАТЕЛЯ
        if data == "main_menu":
            show_main_menu_from_query(query, context)
        
        elif data == "noop":
            # Пустой callback (кнопка с номером страницы)
            return
        
        elif data == "set_token":
            query.edit_message_text(
                "🔑 Пожалуйста, отправьте ваш VK токен. "
                "Вы можете получить его здесь: https://vkhost.github.io/\n\n"
                "⚠️ Никому не передавайте ваш токен!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
            context.user_data['awaiting_token'] = True
        
        elif data == "info":
            show_info(query)
        
        elif data == "program_info":
            show_program_info(query)
        
        elif data == "token_management":
            show_token_management(query)
        
        elif data == "check_token":
            validity = vk_manager.check_token_validity()
            if validity["valid"]:
                user_info = validity["user_info"]
                first_name = user_info.get('first_name', '')
                last_name = user_info.get('last_name', '')
                query.edit_message_text(
                    f"✅ Токен валиден!\n👤 Пользователь: {first_name} {last_name}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="token_management")]])
                )
            else:
                query.edit_message_text(
                    f"❌ Токен невалиден: {validity.get('error_msg')}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="token_management")]])
                )
        
        # ПОДПИСКИ
        elif data == "subscription_required":
            show_subscription_required(query, context)
        
        elif data == "my_requests_info":
            show_my_requests_info(query, context)
        
        elif data == "subscribe":
            show_payment_methods(query, context)
        
        elif data == "pay_stars":
            show_stars_subscription(query, context)
        
        elif data == "pay_bank":
            show_bank_subscription(query, context)
        
        elif data == "check_subscription":
            check_user_subscription(query, context)
        
        elif data == "subscription_info":
            show_subscription_info(query, context)
        
        elif data.startswith("stars_"):
            period = data.replace("stars_", "")
            process_stars_payment(query, context, period)
        
        elif data.startswith("bank_"):
            period = data.replace("bank_", "")
            process_bank_payment(query, context, period)
        
        elif data == "send_screenshot":
            request_screenshot(query, context)
        
        elif data == "confirm_payment":
            confirm_payment(query, context)
        
        elif data == "cancel_payment":
            query.edit_message_text(
                "❌ Оплата отменена.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="subscribe")]])
            )
        
        # Обработка возврата к разным источникам музыки
        elif data in ["my_music", "friends_music", "groups_music", 
                     "playlists", "recommendations", "algorithmic_mixes", 
                     "search_music"]:
            
            # Проверяем подписку для поиска
            if data == "search_music" and data in SUBSCRIPTION_REQUIRED_FEATURES:
                user_id = query.from_user.id
                if not subscription_manager.is_subscribed(user_id):
                    show_subscription_required(query, context)
                    return
            
            if data == "my_music":
                show_my_music(query, context)
            elif data == "friends_music":
                show_friends_list(query, context)
            elif data == "groups_music":
                show_groups_list(query, context)
            elif data == "playlists":
                show_playlists(query, context)
            elif data == "recommendations":
                show_recommendations(query, context)
            elif data == "algorithmic_mixes":
                show_algorithmic_mixes(query, context)
            elif data == "search_music":
                handle_search_request(query, context)
        
        elif data.startswith("friend_"):
            friend_id = data.split("_")[1]
            result = vk_manager.get_friend_audio_list(friend_id)
            if not result["success"]:
                query.edit_message_text(
                    f"❌ Ошибка: {result.get('error')}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="friends_music")]])
                )
                return
            
            audio_list = result["audio_list"]
            if not audio_list:
                query.edit_message_text(
                    "🎵 У друга нет аудиозаписей или доступ ограничен",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="friends_music")]])
                )
                return
            
            # Сохраняем список аудиозаписей и источник в контексте
            context.user_data['current_audio_list'] = audio_list
            context.user_data['audio_source'] = 'friends_music'
            
            text = get_audio_info_text(audio_list)
            keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
            
            query.edit_message_text(text, reply_markup=keyboard)
        
        elif data.startswith("group_"):
            group_id = data.split("_")[1]
            result = vk_manager.get_group_audio_list(group_id)
            if not result["success"]:
                query.edit_message_text(
                    f"❌ Ошибка: {result.get('error')}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="groups_music")]])
                )
                return
            
            audio_list = result["audio_list"]
            if not audio_list:
                query.edit_message_text(
                    "🎵 В группе нет аудиозаписей или доступ ограничен",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="groups_music")]])
                )
                return
            
            # Сохраняем список аудиозаписей и источник в контексте
            context.user_data['current_audio_list'] = audio_list
            context.user_data['audio_source'] = 'groups_music'
            
            text = get_audio_info_text(audio_list)
            keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
            
            query.edit_message_text(text, reply_markup=keyboard)
        
        elif data.startswith("playlist_"):
            playlist_id = data.split("_")[1]
            result = vk_manager.get_playlist_tracks(playlist_id)
            if not result["success"]:
                query.edit_message_text(
                    f"❌ Ошибка: {result.get('error')}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="playlists")]])
                )
                return
            
            audio_list = result["audio_list"]
            if not audio_list:
                query.edit_message_text(
                    "🎵 Плейлист пуст",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="playlists")]])
                )
                return
            
            # Сохраняем список аудиозаписей и источник в контексте
            context.user_data['current_audio_list'] = audio_list
            context.user_data['audio_source'] = 'playlists'
            
            text = get_audio_info_text(audio_list)
            keyboard = create_audio_keyboard(audio_list, prefix="play_audio")
            
            query.edit_message_text(text, reply_markup=keyboard)
        
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
                    query.answer("❌ Список треков не найден")
                    query.edit_message_text(
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
                
                query.edit_message_text(text, reply_markup=keyboard)
                logger.info(f"Страница успешно переключена на индекс {page_index}")
                
            except ValueError as e:
                logger.error(f"Ошибка ValueError при пагинации: {e}, data: {data}")
                query.answer("❌ Ошибка: неверный номер страницы")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при пагинации: {e}")
                query.answer("❌ Ошибка при переключении страницы")
        
        elif data.startswith("play_audio_"):
            # Воспроизведение конкретного трека (но не пагинация!)
            try:
                # Проверяем, что это не пагинация
                parts = data.split("_")
                if len(parts) == 3 and parts[0] == "play" and parts[1] == "audio":
                    # Формат: play_audio_0
                    audio_index = int(parts[2])
                    play_audio_track(query, context, audio_index)
                else:
                    logger.error(f"Неверный формат callback_data: {data}")
                    query.answer("❌ Ошибка: неверный формат команды")
                    
            except (ValueError, IndexError) as e:
                logger.error(f"Ошибка при обработке play_audio: {e}, data: {data}")
                query.answer("❌ Ошибка: неверный индекс трека")
        
        else:
            query.edit_message_text(
                "❌ Неизвестная команда",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
            )
    
    except Exception as e:
        logger.error(f"Ошибка в обработчике callback: {e}")
        query.edit_message_text(
            f"❌ Произошла ошибка: {e}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]])
        )
