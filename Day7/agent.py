import os
import json
import requests
from typing import List, Dict

class MemoryAgent:
    """
    Класс ИИ-агента с долгосрочной памятью (сохранением контекста в JSON).
    """
    def __init__(self, api_key: str, model_name: str = "openrouter/google/gemini-3.5-flash", memory_file: str = "history.json"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://ai-public.a101.ru/api/chat/completions"
        self.memory_file = memory_file
        
        # Системный промпт не сохраняется в историю, он подается при каждом запросе
        self.system_prompt = {"role": "system", "content": "Ты дружелюбный помощник. Обязательно учитывай историю переписки."}
        
        # При создании агента сразу пытаемся загрузить историю из файла
        self.history = self._load_history()

    def _load_history(self) -> List[Dict[str, str]]:
        """Загружает историю диалога из JSON файла."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка чтения файла истории: {e}")
                return []
        return []

    def _save_history(self):
        """Сохраняет текущую историю диалога в JSON файл."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения файла истории: {e}")

    def clear_memory(self):
        """Очищает память агента и удаляет файл истории."""
        self.history = []
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def get_history(self) -> List[Dict[str, str]]:
        """Возвращает текущую историю для отображения в UI."""
        return self.history

    def process_request(self, user_prompt: str) -> str:
        """
        Принимает новый запрос, добавляет в историю, отправляет ВЕСЬ контекст в LLM,
        получает ответ, добавляет его в историю и сохраняет на диск.
        """
        if not self.api_key:
            return "Ошибка Агента: API ключ не задан."

        # 1. Добавляем сообщение пользователя в память
        self.history.append({"role": "user", "content": user_prompt})

        # Формируем полный список сообщений для API: Система + Вся история
        messages_to_send = [self.system_prompt] + self.history

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": messages_to_send,
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            resp_data = response.json()
            
            # Извлекаем ответ модели
            agent_reply = resp_data['choices'][0]['message']['content']
            
            # 2. Добавляем ответ агента в память
            self.history.append({"role": "assistant", "content": agent_reply})
            
            # 3. Сохраняем обновленную историю на диск
            self._save_history()

            return agent_reply
            
        except requests.exceptions.RequestException as e:
            # В случае ошибки удаляем последнее сообщение пользователя из истории,
            # чтобы при следующей попытке не дублировать контекст
            self.history.pop()
            
            error_details = ""
            if response.content:
                try:
                    error_details = response.json()
                except:
                    error_details = response.text
            return f"Ошибка сети при обращении к LLM: {str(e)} | Детали: {error_details}"
        except (KeyError, IndexError):
            self.history.pop()
            return "Ошибка Агента: Получен неожиданный формат ответа от LLM."
