import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# URL компании a101
BASE_URL = "https://ai-public.a101.ru/api"
# Самая быстрая и дешевая модель из твоего списка (обычно модели Flash - самые доступные)
MODEL_NAME = "openrouter/google/gemini-3.5-flash"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>День 3 - Лаборатория Рассуждений (API)</title>
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --success: #10b981;
            --error: #ef4444;
        }

        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
        }

        h1 {
            text-align: center;
            color: var(--primary);
            font-weight: 300;
            letter-spacing: 2px;
            margin-bottom: 30px;
        }

        .header-panel {
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }

        .input-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            color: var(--text-muted);
            font-size: 0.9em;
        }

        input[type="text"], input[type="password"], textarea {
            width: 100%;
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px;
            border-radius: 4px;
            box-sizing: border-box;
            font-family: inherit;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }

        textarea {
            resize: vertical;
            min-height: 80px;
        }

        .btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
            width: 100%;
            font-size: 1em;
            margin-top: 10px;
        }

        .btn:hover {
            background: var(--primary-hover);
        }
        
        .btn-check {
            width: auto;
            margin-top: 0;
            padding: 5px 15px;
            font-size: 0.9em;
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
        }
        .btn-check:hover { background: var(--border); }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
            font-size: 0.9em;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .method-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .method-header {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-bottom: 1px solid var(--border);
        }

        .method-header h3 {
            margin: 0 0 5px 0;
            color: var(--primary);
            font-size: 1.1em;
        }

        .method-desc {
            font-size: 0.85em;
            color: var(--text-muted);
            margin: 0;
        }

        .method-content {
            padding: 15px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }

        .result-box {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 15px;
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 0.95em;
            line-height: 1.5;
            flex-grow: 1;
        }

        .status-bar {
            margin-top: 10px;
            font-size: 0.85em;
            color: var(--text-muted);
            text-align: right;
            display: flex;
            justify-content: space-between;
        }
        
        /* Цвета статусов */
        .color-wait { color: var(--text-muted); }
        .color-process { color: var(--primary); }
        .color-success { color: var(--success); }
        .color-error { color: var(--error); }

    </style>
</head>
<body>
    <h1>Лаборатория Рассуждений (День 3)</h1>

    <div class="header-panel">
        <div class="input-group">
            <label>API Key (a101.ru):</label>
            <div style="display: flex; gap: 10px;">
                <input type="password" id="apiKey" placeholder="Введите ключ..." style="flex-grow: 1;">
                <button class="btn-check" onclick="checkConnection()">Проверить</button>
            </div>
            <div class="connection-status">
                <span id="conn-text" class="color-wait">Ожидание ключа...</span>
            </div>
        </div>

        <div class="input-group">
            <label>Задача (Аналитическая/Логическая):</label>
            <textarea id="taskInput">У меня есть 5 ведер. В каждом ведре лежит по 3 яблока. Сколько всего яблок в ведрах? Но учти, что одно ведро дырявое и все яблоки из него выпали по дороге.</textarea>
        </div>
        
        <button class="btn" onclick="startExperiment()">ЗАПУСТИТЬ ВСЕ 4 МЕТОДА</button>
    </div>

    <div class="grid">
        <!-- Метод 1: Прямой ответ -->
        <div class="method-card">
            <div class="method-header">
                <h3>1. Прямой ответ</h3>
                <p class="method-desc">Без дополнительных инструкций. Как есть.</p>
            </div>
            <div class="method-content">
                <div class="result-box" id="res-direct">Ожидание запуска...</div>
                <div class="status-bar">
                    <span id="time-direct">--</span>
                    <span id="status-direct" class="color-wait">Готов</span>
                </div>
            </div>
        </div>

        <!-- Метод 2: Пошагово (Chain of Thought) -->
        <div class="method-card">
            <div class="method-header">
                <h3>2. Пошаговое рассуждение</h3>
                <p class="method-desc">Инструкция: «Думай шаг за шагом (step-by-step)»</p>
            </div>
            <div class="method-content">
                <div class="result-box" id="res-step">Ожидание запуска...</div>
                <div class="status-bar">
                    <span id="time-step">--</span>
                    <span id="status-step" class="color-wait">Готов</span>
                </div>
            </div>
        </div>

        <!-- Метод 3: Сначала промпт, потом решение -->
        <div class="method-card">
            <div class="method-header">
                <h3>3. Мета-промптинг (2 этапа)</h3>
                <p class="method-desc">Модель сначала пишет промпт для решения, а затем сама же его исполняет.</p>
            </div>
            <div class="method-content">
                <div class="result-box" id="res-meta">Ожидание запуска...</div>
                <div class="status-bar">
                    <span id="time-meta">--</span>
                    <span id="status-meta" class="color-wait">Готов</span>
                </div>
            </div>
        </div>

        <!-- Метод 4: Группа экспертов -->
        <div class="method-card">
            <div class="method-header">
                <h3>4. Консилиум экспертов</h3>
                <p class="method-desc">Роли: Математик, Скептик и Финальный судья.</p>
            </div>
            <div class="method-content">
                <div class="result-box" id="res-experts">Ожидание запуска...</div>
                <div class="status-bar">
                    <span id="time-experts">--</span>
                    <span id="status-experts" class="color-wait">Готов</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function checkConnection() {
            const apiKey = document.getElementById('apiKey').value;
            const statusEl = document.getElementById('conn-text');
            
            if (!apiKey) {
                alert("Введите ключ!"); return;
            }
            
            statusEl.className = 'color-process';
            statusEl.innerText = "Проверка...";
            
            try {
                const response = await fetch('/check_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ apiKey: apiKey })
                });
                const data = await response.json();
                
                if (data.status === 'ok') {
                    statusEl.className = 'color-success';
                    statusEl.innerText = "Связь установлена (Модель: {{ model_name }})";
                } else {
                    statusEl.className = 'color-error';
                    statusEl.innerText = "Ошибка: " + data.message;
                }
            } catch (err) {
                statusEl.className = 'color-error';
                statusEl.innerText = "Ошибка сети.";
            }
        }

        async function fetchAPI(payload, targetId) {
            const resBox = document.getElementById(`res-${targetId}`);
            const statusEl = document.getElementById(`status-${targetId}`);
            const timeEl = document.getElementById(`time-${targetId}`);
            
            resBox.innerHTML = '<span style="color: var(--primary);">Генерация ответа...</span>';
            statusEl.className = 'color-process';
            statusEl.innerText = 'В процессе';
            
            const startTime = Date.now();

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                
                const timeTaken = ((Date.now() - startTime) / 1000).toFixed(1);
                timeEl.innerText = `${timeTaken} сек.`;

                if (data.error) {
                    resBox.innerHTML = `<span class="color-error">[Ошибка] ${data.error}</span>`;
                    statusEl.className = 'color-error';
                    statusEl.innerText = 'Ошибка';
                } else {
                    resBox.innerText = data.text;
                    statusEl.className = 'color-success';
                    statusEl.innerText = `Токенов: ${data.tokens}`;
                }
            } catch (err) {
                resBox.innerHTML = `<span class="color-error">[Сбой] ${err.message}</span>`;
                statusEl.className = 'color-error';
                statusEl.innerText = 'Сбой';
            }
        }

        function startExperiment() {
            const apiKey = document.getElementById('apiKey').value;
            const task = document.getElementById('taskInput').value;
            
            if (!apiKey) {
                alert("Необходим ключ API!"); return;
            }

            // 1. Прямой ответ
            const req1 = {
                apiKey: apiKey,
                method: "direct",
                prompt: task
            };

            // 2. Пошаговое
            const req2 = {
                apiKey: apiKey,
                method: "step",
                prompt: task
            };

            // 3. Мета-промпт (Реализуется на бэкенде в 2 этапа)
            const req3 = {
                apiKey: apiKey,
                method: "meta",
                prompt: task
            };

            // 4. Эксперты
            const req4 = {
                apiKey: apiKey,
                method: "experts",
                prompt: task
            };

            // Запускаем все параллельно
            fetchAPI(req1, 'direct');
            fetchAPI(req2, 'step');
            fetchAPI(req3, 'meta');
            fetchAPI(req4, 'experts');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, model_name=MODEL_NAME.split('/')[-1])

@app.route('/check_connection', methods=['POST'])
def check_connection():
    api_key = request.json.get('apiKey')
    if not api_key:
        return jsonify({"status": "error", "message": "Ключ не предоставлен."})
    url = f"{BASE_URL}/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return jsonify({"status": "ok", "message": "OK"})
        return jsonify({"status": "error", "message": f"Код {response.status_code}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def call_ai(api_key, system_prompt, user_prompt):
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content'], data.get('usage', {}).get('completion_tokens', 0)


@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    api_key = data.get('apiKey')
    method = data.get('method')
    user_task = data.get('prompt')

    try:
        if method == "direct":
            sys_prompt = "Ты ИИ-помощник. Отвечай прямо на вопрос пользователя."
            text, tokens = call_ai(api_key, sys_prompt, user_task)
            return jsonify({"text": text, "tokens": tokens})

        elif method == "step":
            sys_prompt = "Ты аналитический ИИ. Твоя главная задача — решать проблемы шаг за шагом (Chain of Thought). Опиши каждый шаг своих рассуждений перед выдачей финального ответа."
            text, tokens = call_ai(api_key, sys_prompt, user_task)
            return jsonify({"text": text, "tokens": tokens})

        elif method == "meta":
            # ЭТАП 1: Просим модель создать идеальный промпт для этой задачи
            meta_sys = "Ты — инженер промптов. Твоя задача — создать идеальный промпт для решения переданной задачи. Не решай задачу! Просто напиши инструкцию для другой ИИ, как её решить."
            prompt_generated, t1 = call_ai(api_key, meta_sys, f"Задача: {user_task}")
            
            # ЭТАП 2: Отдаем сгенерированный промпт модели для решения
            sys_prompt2 = "Реши задачу, строго следуя переданной инструкции."
            final_text, t2 = call_ai(api_key, sys_prompt2, f"Инструкция:\n{prompt_generated}\n\nЗадача:\n{user_task}")
            
            result = f"--- ЭТАП 1: СГЕНЕРИРОВАННЫЙ ПРОМПТ ---\n{prompt_generated}\n\n--- ЭТАП 2: РЕШЕНИЕ ---\n{final_text}"
            return jsonify({"text": result, "tokens": t1 + t2})

        elif method == "experts":
            sys_prompt = (
                "Ты — группа экспертов: Математик, Скептик-Логик и Финальный Судья. "
                "1. Математик предлагает первоначальное решение. "
                "2. Скептик ищет подвохи, ошибки и крайние случаи в словах Математика. "
                "3. Финальный судья анализирует доводы обоих и выносит окончательный правильный ответ. "
                "Оформи ответ как диалог этих трех ролей."
            )
            text, tokens = call_ai(api_key, sys_prompt, user_task)
            return jsonify({"text": text, "tokens": tokens})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(">>> СЕРВЕР ДНЯ 3 ЗАПУЩЕН НА ПОРТУ 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
