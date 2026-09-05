import os
import time
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

BASE_URL = "https://ai-public.a101.ru/api"

# Выбираем 3 модели из доступных в конфиге a101.ru (от "слабой/быстрой" до "сильной")
MODELS = {
    "weak": {
        "id": "openrouter/google/gemini-3.5-flash",
        "name": "Gemini 3.5 Flash",
        "tier": "Слабая / Быстрая",
        "price_per_1k": 0.0001 # Условная цена за 1к токенов в $
    },
    "medium": {
        "id": "openrouter/claude-sonnet-5",
        "name": "Claude Sonnet 5",
        "tier": "Средняя / Баланс",
        "price_per_1k": 0.003
    },
    "strong": {
        "id": "openai/gpt-5.6-luna", # Берем сильную модель из конфига
        "name": "GPT-5.6 Luna",
        "tier": "Сильная / Дорогая",
        "price_per_1k": 0.015
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>День 5 - Битва Интеллектов (API)</title>
    <style>
        :root {
            --bg-color: #f8fafc;
            --text-color: #334155;
            --panel-bg: #ffffff;
            --border: #e2e8f0;
            --primary: #4f46e5;
            
            --color-weak: #10b981;   /* Зеленый */
            --color-mid: #f59e0b;    /* Оранжевый */
            --color-strong: #ef4444; /* Красный */
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
        }

        h1 {
            text-align: center;
            color: var(--text-color);
            margin-bottom: 5px;
            font-weight: 800;
        }
        
        .subtitle {
            text-align: center;
            color: #64748b;
            margin-bottom: 30px;
        }

        .control-panel {
            background: var(--panel-bg);
            border: 1px solid var(--border);
            padding: 20px;
            border-radius: 12px;
            max-width: 800px;
            margin: 0 auto 30px auto;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 0.9em;
        }

        input[type="text"], input[type="password"], textarea {
            width: 100%;
            border: 1px solid var(--border);
            padding: 12px;
            border-radius: 6px;
            box-sizing: border-box;
            font-family: inherit;
            margin-bottom: 15px;
            font-size: 1em;
        }

        .btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
            font-size: 1.1em;
            transition: background 0.2s;
        }

        .btn:hover { background: #4338ca; }

        .models-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .model-card {
            background: var(--panel-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        .model-header {
            padding: 15px;
            color: white;
            text-align: center;
        }
        
        .header-weak { background: var(--color-weak); }
        .header-mid { background: var(--color-mid); }
        .header-strong { background: var(--color-strong); }

        .model-title { font-weight: bold; font-size: 1.2em; }
        .model-tier { font-size: 0.85em; opacity: 0.9; }

        .stats-panel {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            background: #f1f5f9;
            border-bottom: 1px solid var(--border);
            text-align: center;
        }

        .stat-box { padding: 10px 5px; border-right: 1px solid var(--border); }
        .stat-box:last-child { border-right: none; }
        
        .stat-value { font-weight: bold; font-size: 1.1em; color: var(--text-color); }
        .stat-label { font-size: 0.7em; color: #64748b; text-transform: uppercase; }

        .result-box {
            padding: 20px;
            flex-grow: 1;
            min-height: 250px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.6;
            font-size: 0.95em;
        }

        .conclusions {
            max-width: 1400px;
            margin: 30px auto;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }

        .conclusion-box {
            background: white;
            border: 1px solid var(--border);
            padding: 20px;
            border-radius: 8px;
            font-size: 0.9em;
        }
        .conclusion-box h4 { margin-top: 0; color: var(--primary); }
    </style>
</head>
<body>
    <h1>Битва Интеллектов (День 5)</h1>
    <div class="subtitle">Сравнение версий моделей: Быстро и дешево vs Долго и дорого</div>

    <div class="control-panel">
        <label>API Key (a101.ru):</label>
        <input type="password" id="apiKey" placeholder="Введите ключ a101...">

        <label>Сложный аналитический запрос:</label>
        <textarea id="taskInput">Объясни квантовую запутанность так, чтобы это понял 10-летний ребенок, и приведи один пример из реальной жизни, который работает по схожему принципу.</textarea>

        <button class="btn" onclick="startTest()">СТРАВИТЬ МОДЕЛИ</button>
    </div>

    <div class="models-grid">
        <!-- Модель 1: Слабая -->
        <div class="model-card">
            <div class="model-header header-weak">
                <div class="model-title">{{ models.weak.name }}</div>
                <div class="model-tier">{{ models.weak.tier }}</div>
            </div>
            <div class="stats-panel">
                <div class="stat-box">
                    <div class="stat-value" id="time-weak">--</div>
                    <div class="stat-label">Время (сек)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="tokens-weak">--</div>
                    <div class="stat-label">Токенов</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="cost-weak">--</div>
                    <div class="stat-label">Цена ($)</div>
                </div>
            </div>
            <div class="result-box" id="res-weak">Ожидание...</div>
        </div>

        <!-- Модель 2: Средняя -->
        <div class="model-card">
            <div class="model-header header-mid">
                <div class="model-title">{{ models.medium.name }}</div>
                <div class="model-tier">{{ models.medium.tier }}</div>
            </div>
            <div class="stats-panel">
                <div class="stat-box">
                    <div class="stat-value" id="time-mid">--</div>
                    <div class="stat-label">Время (сек)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="tokens-mid">--</div>
                    <div class="stat-label">Токенов</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="cost-mid">--</div>
                    <div class="stat-label">Цена ($)</div>
                </div>
            </div>
            <div class="result-box" id="res-mid">Ожидание...</div>
        </div>

        <!-- Модель 3: Сильная -->
        <div class="model-card">
            <div class="model-header header-strong">
                <div class="model-title">{{ models.strong.name }}</div>
                <div class="model-tier">{{ models.strong.tier }}</div>
            </div>
            <div class="stats-panel">
                <div class="stat-box">
                    <div class="stat-value" id="time-strong">--</div>
                    <div class="stat-label">Время (сек)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="tokens-strong">--</div>
                    <div class="stat-label">Токенов</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="cost-strong">--</div>
                    <div class="stat-label">Цена ($)</div>
                </div>
            </div>
            <div class="result-box" id="res-strong">Ожидание...</div>
        </div>
    </div>

    <div class="conclusions">
        <div class="conclusion-box">
            <h4>💡 Выводы: Слабая модель</h4>
            <p>Идеально для простых задач, где важна скорость. Отвечает почти мгновенно, тратит мало ресурсов. Качество текста может быть поверхностным, но для парсинга, переводов и простых вопросов — это лучший выбор по соотношению цена/качество.</p>
        </div>
        <div class="conclusion-box">
            <h4>💡 Выводы: Средняя модель</h4>
            <p>Баланс. Хорошо справляется с логикой, пишет связный и качественный текст. Скорость ответа приемлемая. Подходит для 80% задач бизнеса (чат-боты, написание статей, анализ текста).</p>
        </div>
        <div class="conclusion-box">
            <h4>💡 Выводы: Сильная модель</h4>
            <p>Для самых тяжелых задач (программирование, сложная математика, глубокий анализ). Отвечает дольше всех, стоит в 10-50 раз дороже слабой модели, но выдает самый проработанный, логичный и точный результат.</p>
        </div>
    </div>

    <script>
        async function fetchAPI(apiKey, prompt, type) {
            const resBox = document.getElementById(`res-${type}`);
            const timeBox = document.getElementById(`time-${type}`);
            const tokensBox = document.getElementById(`tokens-${type}`);
            const costBox = document.getElementById(`cost-${type}`);
            
            resBox.innerHTML = '<span style="color: #64748b;">Генерация...</span>';
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ apiKey, prompt, type })
                });
                const data = await response.json();
                
                if (data.error) {
                    resBox.innerHTML = `<span style="color: red;">[Ошибка] ${data.error}</span>`;
                } else {
                    resBox.innerText = data.text;
                    timeBox.innerText = data.time.toFixed(1);
                    tokensBox.innerText = data.tokens;
                    // Округляем цену до 5 знаков
                    costBox.innerText = "$" + data.cost.toFixed(5); 
                }
            } catch (err) {
                resBox.innerHTML = `<span style="color: red;">[Сбой] ${err.message}</span>`;
            }
        }

        function startTest() {
            const apiKey = document.getElementById('apiKey').value;
            const prompt = document.getElementById('taskInput').value;
            
            if (!apiKey) {
                alert("Необходим ключ API!"); return;
            }

            // Запускаем три запроса параллельно
            fetchAPI(apiKey, prompt, 'weak');
            fetchAPI(apiKey, prompt, 'mid');
            fetchAPI(apiKey, prompt, 'strong');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, models=MODELS)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    api_key = data.get('apiKey')
    prompt = data.get('prompt')
    model_type = data.get('type') # weak, mid, strong

    if not api_key:
        return jsonify({"error": "API Key is missing."}), 400
        
    model_info = MODELS.get(model_type, MODELS["weak"])
    model_id = model_info["id"]
    price_per_1k = model_info["price_per_1k"]

    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "Ты ИИ-ассистент. Отвечай подробно и понятно."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        resp_data = response.json()
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        try:
            text = resp_data['choices'][0]['message']['content']
            
            # Считаем токены и стоимость
            usage = resp_data.get('usage', {})
            tokens_generated = usage.get('completion_tokens', len(text.split()) * 1.5) # Fallback если нет usage
            
            # Примерный расчет стоимости
            cost = (tokens_generated / 1000) * price_per_1k
            
            return jsonify({
                "text": text,
                "time": time_taken,
                "tokens": int(tokens_generated),
                "cost": cost
            })
        except (KeyError, IndexError):
            return jsonify({"error": "Неожиданный ответ API"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f">>> СЕРВЕР ДНЯ 5 ЗАПУЩЕН НА ПОРТУ 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
