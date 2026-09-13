import os
import json
import requests
import tiktoken
from typing import List, Dict, Tuple

class TokenAwareAgent:
    """
    Класс ИИ-агента с памятью и глубокой аналитикой токенов.
    """
    def __init__(self, api_key: str, model_name: str = "openrouter/google/gemini-3.5-flash", memory_file: str = "history.json"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://ai-public.a101.ru/api/chat/completions"
        self.memory_file = memory_file
        
        self.system_prompt = {"role": "system", "content": "Ты дружелюбный помощник. Пиши коротко, но информативно."}
        self.history = self._load_history()

        # Инициализируем локальный энкодер для точного подсчета токенов ДО отправки в API
        # Используем стандартный cl100k_base (используется GPT-4 и многими совместимыми API)
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except:
            self.encoding = None

    def _load_history(self) -> List[Dict[str, str]]:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def clear_memory(self):
        self.history = []
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def count_tokens(self, text: str) -> int:
        """Локальный подсчет токенов строки."""
        if self.encoding:
            return len(self.encoding.encode(text))
        # Резервный метод, если tiktoken не сработает (примерно 4 символа на токен)
        return len(text) // 4

    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Подсчет токенов массива сообщений (истории)."""
        # Учитываем, что каждое сообщение в API требует дополнительных токенов на спец. форматирование (role, content)
        tokens = 0
        for msg in messages:
            tokens += self.count_tokens(msg.get("content", ""))
            tokens += 4 # Базовые накладные расходы на сообщение
        tokens += 3 # Завершающий токен массива
        return tokens

    def process_request(self, user_prompt: str, force_max_tokens: int = 1000) -> Dict:
        """
        Принимает запрос, считает токены, отправляет в LLM, возвращает ответ + аналитику.
        force_max_tokens нужен для искусственной демонстрации переполнения.
        """
        if not self.api_key:
            return {"error": "API ключ не задан."}

        # 1. Аналитика ДО отправки запроса
        request_tokens = self.count_tokens(user_prompt)
        history_tokens = self.count_messages_tokens(self.history)
        
        # Добавляем в историю
        self.history.append({"role": "user", "content": user_prompt})
        messages_to_send = [self.system_prompt] + self.history
        
        # Считаем тотальный контекст, который мы сейчас пошлем в API (Система + История + Текущий)
        prompt_tokens_sent = self.count_messages_tokens(messages_to_send)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Искусственно ограничиваем модель, чтобы показать "переполнение" (Day 8 requirement)
        payload = {
            "model": self.model_name,
            "messages": messages_to_send,
            "temperature": 0.7,
            "max_tokens": force_max_tokens 
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            resp_data = response.json()
            
            agent_reply = resp_data['choices'][0]['message']['content']
            
            # Аналитика ПОСЛЕ ответа (берем точные данные из API, если они есть)
            usage = resp_data.get('usage', {})
            # Если API не вернуло usage, считаем локально
            api_prompt_tokens = usage.get('prompt_tokens', prompt_tokens_sent) 
            api_completion_tokens = usage.get('completion_tokens', self.count_tokens(agent_reply))
            total_tokens = usage.get('total_tokens', api_prompt_tokens + api_completion_tokens)

            # Проверка причины остановки (чтобы показать, что сломалось при переполнении)
            finish_reason = resp_data['choices'][0].get('finish_reason', 'unknown')
            is_truncated = finish_reason == 'length'

            self.history.append({"role": "assistant", "content": agent_reply})
            self._save_history()

            return {
                "reply": agent_reply,
                "stats": {
                    "request_tokens": request_tokens,         # Только текущий запрос
                    "history_tokens_before": history_tokens,  # История ДО добавления запроса
                    "context_sent_tokens": api_prompt_tokens, # Сколько токенов сожрал ВЕСЬ контекст
                    "response_tokens": api_completion_tokens, # Сколько сгенерировала модель
                    "total_tokens": total_tokens,             # Итого (Контекст + Ответ)
                    "finish_reason": finish_reason,           # stop (ок) или length (переполнение)
                    "is_truncated": is_truncated
                }
            }
            
        except requests.exceptions.RequestException as e:
            self.history.pop() # Откат
            error_details = response.text if response.content else ""
            return {"error": f"Сбой API: {str(e)}. {error_details}"}
        except Exception as e:
            self.history.pop() # Откат
            return {"error": f"Внутренняя ошибка: {str(e)}"}
