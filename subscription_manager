import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SubscriptionManager:
    def __init__(self, db_file: str = "subscriptions.json"):
        self.db_file = db_file
        self.data = self.load_data()
    
    def load_data(self) -> dict:
        """Загрузка данных о подписках"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки подписок: {e}")
                return self._default_data()
        return self._default_data()
    
    def _default_data(self) -> dict:
        """Структура данных по умолчанию"""
        return {
            "users": {},
            "prices": {
                "stars": {
                    "1_month": 100,
                    "3_months": 250,
                    "6_months": 450,
                    "1_year": 800,
                },
                "bank": {
                    "1_month": 500,
                    "3_months": 1200,
                    "6_months": 2200,
                    "1_year": 4000,
                }
            },
            "bank_details": {
                "card": "2202 2006 1234 5678",
                "bank": "Сбербанк",
                "recipient": "Иван Иванов",
            },
            "pending_payments": {},
            "subscription_durations": {
                "1_month": 30,
                "3_months": 90,
                "6_months": 180,
                "1_year": 365,
            },
            "free_requests": {}
        }
    
    def save(self):
        """Сохранение данных"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения подписок: {e}")
    
    def get_user(self, user_id: int) -> Optional[dict]:
        """Получить данные пользователя"""
        return self.data["users"].get(str(user_id))
    
    def add_user(self, user_id: int, days: int) -> datetime:
        """Добавить/продлить подписку"""
        user_id_str = str(user_id)
        current_time = datetime.now()
        
        if user_id_str in self.data["users"]:
            existing_until = datetime.fromisoformat(
                self.data["users"][user_id_str]["subscription_until"]
            )
            if existing_until > current_time:
                new_until = existing_until + timedelta(days=days)
            else:
                new_until = current_time + timedelta(days=days)
        else:
            new_until = current_time + timedelta(days=days)
        
        self.data["users"][user_id_str] = {
            "subscription_until": new_until.isoformat(),
            "active": True,
            "notified_24h": False,
            "notified_2h": False,
        }
        self.save()
        return new_until
    
    def is_subscribed(self, user_id: int) -> bool:
        """Проверить активность подписки"""
        user = self.get_user(user_id)
        if not user or not user.get("active"):
            return False
        
        subscription_until = datetime.fromisoformat(user["subscription_until"])
        if subscription_until < datetime.now():
            self.data["users"][str(user_id)]["active"] = False
            self.save()
            return False
        return True
    
    def get_time_left(self, user_id: int) -> Optional[timedelta]:
        """Получить оставшееся время подписки"""
        user = self.get_user(user_id)
        if not user or not user.get("active"):
            return None
        
        subscription_until = datetime.fromisoformat(user["subscription_until"])
        now = datetime.now()
        
        if subscription_until <= now:
            self.data["users"][str(user_id)]["active"] = False
            self.save()
            return None
        
        return subscription_until - now
    
    def get_prices_stars(self) -> dict:
        """Получить цены в звездах"""
        return self.data["prices"]["stars"]
    
    def get_prices_bank(self) -> dict:
        """Получить цены в рублях"""
        return self.data["prices"]["bank"]
    
    def get_bank_details(self) -> dict:
        """Получить реквизиты"""
        return self.data.get("bank_details", {})
    
    def get_subscription_durations(self) -> dict:
        """Получить длительности подписок"""
        return self.data["subscription_durations"]
    
    def add_pending_payment(self, user_id: int, period: str, amount: int, 
                           screenshot_id: str = None, username: str = None) -> str:
        """Добавить ожидающий платеж"""
        import uuid
        payment_id = str(uuid.uuid4())
        
        if "pending_payments" not in self.data:
            self.data["pending_payments"] = {}
        
        self.data["pending_payments"][payment_id] = {
            "user_id": user_id,
            "period": period,
            "amount": amount,
            "screenshot_id": screenshot_id,
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        self.save()
        return payment_id
    
    def get_pending_payment(self, payment_id: str) -> Optional[dict]:
        """Получить ожидающий платеж"""
        return self.data.get("pending_payments", {}).get(payment_id)
    
    def remove_pending_payment(self, payment_id: str):
        """Удалить ожидающий платеж"""
        if payment_id in self.data.get("pending_payments", {}):
            del self.data["pending_payments"][payment_id]
            self.save()
    
    def get_all_users(self) -> dict:
        """Получить всех пользователей"""
        return self.data.get("users", {})
    
    def get_statistics(self) -> dict:
        """Получить статистику"""
        users = self.data.get("users", {})
        now = datetime.now()
        
        total = len(users)
        active = 0
        expired = 0
        
        for user_data in users.values():
            if user_data.get("active"):
                subscription_until = datetime.fromisoformat(user_data["subscription_until"])
                if subscription_until > now:
                    active += 1
                else:
                    expired += 1
            else:
                expired += 1
        
        pending = len(self.data.get("pending_payments", {}))
        
        # Статистика по бесплатным запросам
        free_users = len(self.data.get("free_requests", {}))
        total_free_requests = sum(
            user_data.get("used", 0) 
            for user_data in self.data.get("free_requests", {}).values()
        )
        
        return {
            "total": total,
            "active": active,
            "expired": expired,
            "pending": pending,
            "free_users": free_users,
            "total_free_requests": total_free_requests
        }
    
    def can_make_free_request(self, user_id: int, max_free_requests: int = 10, reset_days: int = 30) -> dict:
        """Проверить, может ли пользователь сделать бесплатный запрос"""
        user_id_str = str(user_id)
        
        # Если есть подписка - всегда разрешаем
        if self.is_subscribed(user_id):
            return {
                "can_search": True,
                "reason": "subscribed",
                "remaining": "∞",
                "total_used": 0
            }
        
        # Инициализируем данные пользователя если нужно
        if "free_requests" not in self.data:
            self.data["free_requests"] = {}
            
        if user_id_str not in self.data["free_requests"]:
            self.data["free_requests"][user_id_str] = {
                "used": 0,
                "first_request": datetime.now().isoformat(),
                "last_reset": datetime.now().isoformat()
            }
            self.save()
        
        user_data = self.data["free_requests"][user_id_str]
        last_reset = datetime.fromisoformat(user_data["last_reset"])
        now = datetime.now()
        
        # Проверяем, нужно ли сбросить счетчик
        days_since_reset = (now - last_reset).days
        if days_since_reset >= reset_days:
            user_data["used"] = 0
            user_data["last_reset"] = now.isoformat()
            self.save()
        
        used = user_data["used"]
        remaining = max_free_requests - used
        
        if remaining <= 0:
            return {
                "can_search": False,
                "reason": "no_free_requests",
                "remaining": 0,
                "total_used": used,
                "message": "Бесплатные запросы закончились"
            }
        
        return {
            "can_search": True,
            "reason": "free_requests_available",
            "remaining": remaining,
            "total_used": used
        }
    
    def use_free_request(self, user_id: int) -> dict:
        """Использовать один бесплатный запрос"""
        user_id_str = str(user_id)
        
        # Инициализируем если нужно
        if "free_requests" not in self.data:
            self.data["free_requests"] = {}
            
        if user_id_str not in self.data["free_requests"]:
            self.data["free_requests"][user_id_str] = {
                "used": 1,
                "first_request": datetime.now().isoformat(),
                "last_reset": datetime.now().isoformat()
            }
        else:
            self.data["free_requests"][user_id_str]["used"] += 1
        
        self.save()
        
        return self.can_make_free_request(user_id)
    
    def get_free_requests_info(self, user_id: int) -> dict:
        """Получить информацию о бесплатных запросах"""
        user_id_str = str(user_id)
        
        if "free_requests" not in self.data or user_id_str not in self.data["free_requests"]:
            return {
                "used": 0,
                "remaining": 10,
                "last_reset": datetime.now(),
                "days_to_reset": 30,
                "has_subscription": self.is_subscribed(user_id)
            }
        
        user_data = self.data["free_requests"][user_id_str]
        last_reset = datetime.fromisoformat(user_data["last_reset"])
        now = datetime.now()
        days_since_reset = (now - last_reset).days
        
        days_to_reset = max(0, 30 - days_since_reset)
        
        return {
            "used": user_data["used"],
            "remaining": max(0, 10 - user_data["used"]),
            "last_reset": last_reset,
            "days_to_reset": days_to_reset,
            "has_subscription": self.is_subscribed(user_id)
        }
    
    def reset_free_requests(self, user_id: int):
        """Сбросить счетчик бесплатных запросов (админ)"""
        user_id_str = str(user_id)
        
        if "free_requests" not in self.data:
            self.data["free_requests"] = {}
        
        if user_id_str in self.data["free_requests"]:
            self.data["free_requests"][user_id_str] = {
                "used": 0,
                "first_request": datetime.now().isoformat(),
                "last_reset": datetime.now().isoformat()
            }
            self.save()
            return True
        
        # Если записей не было, создаем
        self.data["free_requests"][user_id_str] = {
            "used": 0,
            "first_request": datetime.now().isoformat(),
            "last_reset": datetime.now().isoformat()
        }
        self.save()
        return True

# Глобальный экземпляр
subscription_manager = SubscriptionManager()
