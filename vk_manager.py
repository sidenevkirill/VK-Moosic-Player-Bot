import os
import requests
import random
from config import logger, VK_API_VERSION, KATE_USER_AGENT, TOKEN_FILE

class VKMusicManager:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.user_info = None
        self.headers = {
            'User-Agent': KATE_USER_AGENT,
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

    def load_token_from_file(self, filename=TOKEN_FILE):
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

    def save_token_to_file(self, filename=TOKEN_FILE):
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
            "v": VK_API_VERSION,
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
            "v": VK_API_VERSION,
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
            "v": VK_API_VERSION,
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
            "v": VK_API_VERSION,
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
            "v": VK_API_VERSION,
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
            "v": VK_API_VERSION,
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
            "v": VK_API_VERSION,
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
            "v": VK_API_VERSION,
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
            "v": VK_API_VERSION,
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
            "v": VK_API_VERSION,
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

    def search_audio(self, query, use_fallback=True):
        """Поиск музыки с fallback методами"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
        
        # Основной метод поиска
        url = "https://api.vk.com/method/audio.search"
        params = {
            "access_token": self.token,
            "v": VK_API_VERSION,
            "q": query,
            "count": 50,
            "auto_complete": 1,
            "sort": 2
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            logger.info(f"Поиск запроса '{query}': статус {response.status_code}")
            
            if "response" in data:
                items = data["response"].get("items", [])
                return {
                    "success": True, 
                    "results": items,
                    "total_count": data["response"].get("count", len(items)),
                    "method": "direct_search"
                }
            else:
                error_code = data.get("error", {}).get("error_code", 0)
                error_msg = data.get("error", {}).get("error_msg", "Неизвестная ошибка")
                
                logger.warning(f"Ошибка поиска (код {error_code}): {error_msg}")
                
                # Если ошибка связана с правами доступа и разрешено использовать fallback
                if error_code == 15 or any(keyword in error_msg.lower() for keyword in ['access_token', 'invalid', 'permission', 'authorization']):
                    if use_fallback:
                        logger.warning("Использую fallback метод поиска")
                        return self.search_audio_fallback(query)
                    else:
                        return {
                            "success": False, 
                            "error": f"Поиск недоступен: {error_msg}",
                            "error_code": error_code,
                            "solution": "Получите новый токен с правами 'audio'"
                        }
                else:
                    return {
                        "success": False, 
                        "error": error_msg,
                        "error_code": error_code
                    }
                    
        except Exception as e:
            logger.error(f"Исключение при поиске: {e}")
            if use_fallback:
                return self.search_audio_fallback(query)
            else:
                return {"success": False, "error": f"Ошибка запроса: {e}"}

    def search_audio_fallback(self, query):
        """Альтернативный поиск музыки через другие методы"""
        logger.info(f"Fallback поиск: {query}")
        
        # Сначала попробуем получить популярную музыку по запросу
        popular_result = self._search_via_popular(query)
        if popular_result["success"] and popular_result["results"]:
            return popular_result
        
        # Если не получилось, используем рекомендации
        return self._search_via_recommendations(query)

    def _search_via_popular(self, query):
        """Поиск через популярную музыку"""
        try:
            url = "https://api.vk.com/method/audio.search"
            params = {
                "access_token": self.token,
                "v": VK_API_VERSION,
                "q": query,
                "count": 30,
                "auto_complete": 0,
                "sort": 0  # Сортировка по популярности
            }
            
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data and data["response"]["items"]:
                return {
                    "success": True,
                    "results": data["response"]["items"],
                    "total_count": len(data["response"]["items"]),
                    "method": "fallback_popular"
                }
        except Exception as e:
            logger.debug(f"Ошибка в fallback популярном поиске: {e}")
        
        return {"success": False, "results": []}

    def _search_via_recommendations(self, query):
        """Поиск через фильтрацию рекомендаций"""
        # Получаем рекомендации
        result = self.get_recommendations()
        if not result["success"]:
            return result
        
        audio_list = result.get("audio_list", [])
        if not audio_list:
            return {"success": False, "error": "Нет данных для поиска"}
        
        # Фильтруем по запросу
        query_lower = query.lower()
        filtered_results = []
        
        for track in audio_list:
            artist = track.get('artist', '').lower()
            title = track.get('title', '').lower()
            
            if query_lower in artist or query_lower in title:
                filtered_results.append(track)
        
        if filtered_results:
            return {
                "success": True,
                "results": filtered_results[:30],
                "total_count": len(filtered_results),
                "method": "fallback_filtered",
                "note": "Использован фильтр рекомендаций"
            }
        
        # Если ничего не найдено, вернем просто рекомендации
        return {
            "success": True,
            "results": audio_list[:30],
            "total_count": len(audio_list),
            "method": "fallback_recommendations",
            "note": f"Показаны рекомендации (запрос '{query}' не найден)"
        }

    def check_token_permissions(self):
        """Проверить разрешения токена"""
        if not self.token:
            return {"success": False, "error": "Токен не установлен"}
        
        # Проверяем через метод users.get с дополнительными полями
        url = "https://api.vk.com/method/users.get"
        params = {
            "access_token": self.token,
            "v": VK_API_VERSION,
            "fields": "can_access_audio,can_see_audio"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if "response" in data:
                user_info = data["response"][0]
                has_audio_access = user_info.get('can_access_audio', 0) == 1
                can_see_audio = user_info.get('can_see_audio', 0) == 1
                
                # Тестовый запрос для проверки прав на поиск
                test_search = self.search_audio("test", use_fallback=False)
                search_available = test_search["success"]
                
                return {
                    "success": True,
                    "permissions": {
                        "has_audio_access": has_audio_access,
                        "can_see_audio": can_see_audio,
                        "search_available": search_available
                    },
                    "user_info": user_info
                }
            else:
                return {"success": False, "error": "Не удалось проверить разрешения"}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка запроса: {e}"}

    def get_music_by_mood(self, mood="happy"):
        """Получить музыку по настроению"""
        mood_queries = {
            "happy": ["веселая музыка", "позитив", "танцевальная музыка", "летние хиты"],
            "sad": ["грустная музыка", "лирика", "меланхолия", "осенняя музыка"],
            "calm": ["спокойная музыка", "релакс", "инструментал", "лофи"],
            "energetic": ["энергичная музыка", "тренировка", "спорт", "драйв"],
            "romantic": ["романтическая музыка", "любовь", "нежная музыка"]
        }
        
        queries = mood_queries.get(mood.lower(), ["популярная музыка"])
        query = random.choice(queries)
        
        return self.search_audio(query)

    def download_audio(self, audio_url, filename):
        """Скачать аудиозапись"""
        try:
            headers = self.headers.copy()
            headers.update({
                'Referer': 'https://vk.com/',
                'Origin': 'https://vk.com'
            })
            
            response = requests.get(audio_url, stream=True, headers=headers, 
                                 timeout=(10, 30))
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Аудио успешно скачано: {filename}")
                return True
            else:
                logger.error(f"Ошибка скачивания: статус {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            logger.error("Таймаут при скачивании аудио")
            return False
        except Exception as e:
            logger.error(f"Ошибка при скачивании: {e}")
            return False

# Глобальный экземпляр менеджера
vk_manager = VKMusicManager()
