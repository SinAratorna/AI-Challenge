import os
import json
import requests
import tiktoken
from typing import List, Dict

class CompressionAgent:
    """
    Агент со сжатием контекста.
    Если количество сообщений превышает max_history_len,
    старые сообщения (сверх лимита) сжимаются в одно системное 'summary',
    которое закрепляется за историей.
    """
    def __init__(self, api_key: str, model_name: str = "openrouter/google/gemini-3.5-flash", memory_file: str = "history_comp.json", max_history_len: int = 4):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://ai-public.a101.ru/api/chat/completions"
        self.memory_file = memory_file
        
        # Сколько полных сообщений хранить "как есть" (парами: user+assistant)
        # 4 означает 2 реплики юзера и 2 ответа агента.
        self.max_history_len = max_history_len
        
        self.system_prompt = "Ты полезный ассистент. Отвечай кратко и дружелюбно."
        
        # Состояние памяти
        self.recent_messages: List[Dict[str, str]] = []
        self.summary: str = ""
        
        self._load_history()

        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except:
            self.encoding = None

    def _load_history(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recent_messages = data.get("recent_messages", [])
                    self.summary = data.get("summary", "")
            except Exception:
                pass

    def _save_history(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "recent_messages": self.recent_messages,
                    "summary": self.summary
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def clear_memory(self):
        self.recent_messages = []
        self.summary = ""
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def count_tokens(self, text: str) -> int:
        if self.encoding:
            return len(self.encoding.encode(text))
        return len(text) // 4

    def _compress_history(self):
        """
        Берет текущее summary и старейшую пару сообщений (user + assistant),
        и просит LLM сгенерировать новое, обновленное summary.
        """
        if len(self.recent_messages) <= self.max_history_len:
            return

        # Берем старейшие сообщения, выходящие за лимит.
        # Чтобы не разбивать пару, берем по 2.
        # Например, если max_history_len = 4, а у нас 6 сообщений, мы берем первые 2 (индексы 0 и 1).
        msgs_to_compress = self.recent_messages[:-self.max_history_len]
        
        # Удаляем их из активной истории
        self.recent_messages = self.recent_messages[-self.max_history_len:]

        # Формируем текст для суммаризации
        dialogue_text = ""
        for msg in msgs_to_compress:
            dialogue_text += f"{msg['role'].upper()}: {msg['content']}\n"

        prompt_for_compression = (
            f"Текущее краткое содержание нашего прошлого диалога: {self.summary if self.summary else 'Его пока нет.'}\n\n"
            f"Вот новый кусок диалога:\n{dialogue_text}\n"
            "Сгенерируй новое, очень сжатое, но информативное summary всего разговора в одном абзаце, объединив старое summary и новые детали. "
            "Выдели только главные факты, которые нужно запомнить о пользователе и контексте."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Для суммаризации используем ту же модель
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "Ты эксперт по сжатию текста. Выдавай только сжатый результат."},
                {"role": "user", "content": prompt_for_compression}
            ],
            "temperature": 0.3, # Низкая темп для точности фактов
            "max_tokens": 500
        }

        try:
            print(">>> Агент сжимает историю...")
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            new_summary = response.json()['choices'][0]['message']['content']
            self.summary = new_summary
            print(f">>> Новое summary создано: {self.summary}")
        except Exception as e:
            print(f"Ошибка при сжатии истории: {e}")
            # Возвращаем сообщения обратно, если сжать не вышло
            self.recent_messages = msgs_to_compress + self.recent_messages

    def build_api_messages(self) -> List[Dict[str, str]]:
        """Собирает массив сообщений для отправки в API."""
        messages = []
        
        # 1. Системный промпт (базовый)
        sys_content = self.system_prompt
        
        # 2. Если есть Summary, вшиваем его в систему
        if self.summary:
            sys_content += f"\n\nКраткое содержание нашего прошлого диалога (ПАМЯТЬ):\n{self.summary}"
            
        messages.append({"role": "system", "content": sys_content})
        
        # 3. Добавляем недавние (не сжатые) сообщения
        messages.extend(self.recent_messages)
        return messages

    def process_request(self, user_prompt: str, enable_compression: bool = True) -> Dict:
        """
        Обрабатывает запрос. enable_compression можно отключить для сравнения (Day 9).
        """
        if not self.api_key:
            return {"error": "API ключ не задан."}

        self.recent_messages.append({"role": "user", "content": user_prompt})
        
        # Если сжатие включено, проверяем и сжимаем историю ПЕРЕД отправкой запроса
        was_compressed = False
        if enable_compression and len(self.recent_messages) > self.max_history_len:
            self._compress_history()
            was_compressed = True

        messages_to_send = self.build_api_messages()
        
        # Считаем токены, которые отправляем в этот раз
        context_tokens = sum([self.count_tokens(m["content"]) for m in messages_to_send])

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
            
            agent_reply = resp_data['choices'][0]['message']['content']
            
            self.recent_messages.append({"role": "assistant", "content": agent_reply})
            self._save_history()

            return {
                "reply": agent_reply,
                "stats": {
                    "context_tokens": context_tokens,
                    "summary_active": bool(self.summary),
                    "summary_text": self.summary,
                    "raw_msg_count": len(self.recent_messages),
                    "just_compressed": was_compressed
                }
            }
            
        except Exception as e:
            self.recent_messages.pop() # Откат
            return {"error": f"Сбой API: {str(e)}"}
