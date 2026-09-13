import os
import requests

class SimpleAgent:
    """
    Класс простого ИИ-агента. 
    Инкапсулирует логику общения с LLM через API a101.ru.
    """
    def __init__(self, api_key: str, model_name: str = "openrouter/google/gemini-3.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://ai-public.a101.ru/api/chat/completions"
        self.system_prompt = "Ты — дружелюбный и умный ИИ-ассистент. Отвечай кратко, четко и по делу."

    def process_request(self, user_prompt: str) -> str:
        """
        Принимает запрос пользователя, формирует payload, отправляет в LLM и возвращает текст ответа.
        """
        if not self.api_key:
            return "Ошибка Агента: API ключ не задан."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            resp_data = response.json()
            
            # Извлекаем текст из ответа OpenAI-совместимого API
            text = resp_data['choices'][0]['message']['content']
            return text
            
        except requests.exceptions.RequestException as e:
            error_details = ""
            if response.content:
                try:
                    error_details = response.json()
                except:
                    error_details = response.text
            return f"Ошибка сети при обращении к LLM: {str(e)} | Детали: {error_details}"
        except (KeyError, IndexError):
            return "Ошибка Агента: Получен неожиданный формат ответа от LLM."
