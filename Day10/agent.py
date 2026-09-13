import os
import json
import requests
import uuid
from typing import List, Dict, Any

class AdvancedContextAgent:
    """
    Агент с тремя стратегиями управления контекстом:
    1. Sliding Window (Окно)
    2. Sticky Facts (Факты)
    3. Branching (Ветвление)
    """
    def __init__(self, api_key: str, model_name: str = "openrouter/google/gemini-3.5-flash", memory_file: str = "memory_v10.json"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://ai-public.a101.ru/api/chat/completions"
        self.memory_file = memory_file
        
        self.window_size = 4 # Для Sliding Window и Facts
        
        # Общее состояние для всех стратегий (сохраняется в JSON)
        self.state = {
            "strategy": "window", # window, facts, branch
            "messages": [], # Общий массив сообщений (для window и facts)
            "facts": {}, # Для стратегии Facts
            "branches": {
                "main": [] # Для стратегии Branching (dict of message lists)
            },
            "active_branch": "main"
        }
        
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.state.update(data)
            except Exception:
                pass

    def _save_state(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def clear_memory(self):
        self.state = {
            "strategy": self.state["strategy"], # Сохраняем выбранную стратегию
            "messages": [],
            "facts": {},
            "branches": {"main": []},
            "active_branch": "main"
        }
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def set_strategy(self, strategy: str):
        self.state["strategy"] = strategy
        self._save_state()

    # --- СТРАТЕГИЯ 2: ИЗВЛЕЧЕНИЕ ФАКТОВ ---
    def _extract_facts(self, new_message: str):
        """
        Фоновый вызов LLM: парсит новое сообщение юзера и извлекает факты в JSON.
        """
        prompt = (
            "Проанализируй следующее сообщение пользователя и извлеки из него важные факты "
            "(имя, предпочтения, требования, ограничения, принятые решения). "
            "Если фактов нет, верни пустой JSON объект {}. "
            "Если есть, верни JSON в формате ключ-значение, например: {'user_name': 'Николай', 'project_budget': '1000$'}. "
            "Никакого текста кроме JSON.\n\n"
            f"Сообщение: {new_message}"
        )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 150
        }
        
        try:
            print(">>> Извлечение фактов...")
            resp = requests.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content']
            
            # Пытаемся вытащить JSON (иногда модель оборачивает в ```json ... ```)
            content = content.replace('```json', '').replace('```', '').strip()
            new_facts = json.loads(content)
            
            if new_facts:
                self.state["facts"].update(new_facts)
                print(f">>> Обновлены факты: {self.state['facts']}")
                
        except Exception as e:
            print(f"Ошибка извлечения фактов: {e}")

    # --- СТРАТЕГИЯ 3: BRANCHING (ВЕТВЛЕНИЕ) ---
    def create_branch(self, branch_name: str, from_index: int = None):
        """Создает новую ветку диалога. Если from_index указан, копирует историю до этого индекса."""
        if branch_name not in self.state["branches"]:
            if from_index is not None and self.state["active_branch"] in self.state["branches"]:
                # Копируем историю текущей ветки до нужного сообщения
                current_history = self.state["branches"][self.state["active_branch"]]
                self.state["branches"][branch_name] = current_history[:from_index+1].copy()
            else:
                self.state["branches"][branch_name] = []
            
            self.state["active_branch"] = branch_name
            self._save_state()
            return True
        return False

    def switch_branch(self, branch_name: str):
        if branch_name in self.state["branches"]:
            self.state["active_branch"] = branch_name
            self._save_state()
            return True
        return False

    # --- ОСНОВНАЯ ЛОГИКА ---
    def build_api_messages(self, user_prompt: str) -> List[Dict[str, str]]:
        strategy = self.state["strategy"]
        messages_to_send = []

        if strategy == "window":
            # Просто берем последние N сообщений
            sys_prompt = "Ты полезный ассистент."
            messages_to_send.append({"role": "system", "content": sys_prompt})
            
            # Добавляем историю (ограниченную окном)
            active_hist = self.state["messages"][-self.window_size:] if self.state["messages"] else []
            messages_to_send.extend(active_hist)
            messages_to_send.append({"role": "user", "content": user_prompt})

        elif strategy == "facts":
            # Извлекаем факты ДО того как сформировать финальный промпт
            self._extract_facts(user_prompt)
            
            sys_prompt = "Ты полезный ассистент."
            if self.state["facts"]:
                facts_str = "\n".join([f"- {k}: {v}" for k, v in self.state["facts"].items()])
                sys_prompt += f"\n\nВАЖНЫЕ ФАКТЫ О ПОЛЬЗОВАТЕЛЕ И ПРОЕКТЕ:\n{facts_str}"
            
            messages_to_send.append({"role": "system", "content": sys_prompt})
            
            active_hist = self.state["messages"][-self.window_size:] if self.state["messages"] else []
            messages_to_send.extend(active_hist)
            messages_to_send.append({"role": "user", "content": user_prompt})

        elif strategy == "branch":
            sys_prompt = f"Ты ассистент. Текущая ветка диалога: {self.state['active_branch']}"
            messages_to_send.append({"role": "system", "content": sys_prompt})
            
            active_hist = self.state["branches"].get(self.state["active_branch"], [])
            messages_to_send.extend(active_hist)
            messages_to_send.append({"role": "user", "content": user_prompt})

        return messages_to_send

    def process_request(self, user_prompt: str) -> Dict:
        if not self.api_key:
            return {"error": "API ключ не задан."}

        strategy = self.state["strategy"]
        
        # 1. Формируем контекст
        messages_to_send = self.build_api_messages(user_prompt)
        
        # Считаем отправленные токены (примерно, для UI)
        context_tokens = sum([len(m["content"]) // 4 for m in messages_to_send])

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
            resp = requests.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            agent_reply = resp.json()['choices'][0]['message']['content']
            
            # 2. Сохраняем в память в зависимости от стратегии
            if strategy in ["window", "facts"]:
                self.state["messages"].append({"role": "user", "content": user_prompt})
                self.state["messages"].append({"role": "assistant", "content": agent_reply})
            elif strategy == "branch":
                active_b = self.state["active_branch"]
                if active_b not in self.state["branches"]:
                    self.state["branches"][active_b] = []
                self.state["branches"][active_b].append({"role": "user", "content": user_prompt})
                self.state["branches"][active_b].append({"role": "assistant", "content": agent_reply})

            self._save_state()

            return {
                "reply": agent_reply,
                "stats": {
                    "strategy": strategy,
                    "context_tokens": context_tokens,
                    "facts_count": len(self.state["facts"]) if strategy == "facts" else 0,
                    "active_branch": self.state["active_branch"] if strategy == "branch" else None
                }
            }
            
        except Exception as e:
            return {"error": f"Сбой API: {str(e)}"}
