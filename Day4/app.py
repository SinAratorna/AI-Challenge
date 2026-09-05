import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

BASE_URL = "https://ai-public.a101.ru/api"
MODEL_NAME = "openrouter/google/gemini-3.5-flash"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>День 4 - Температура (API)</title>
    <style>
        :root {
            --bg-color: #1a1a2e;
            --text-color: #e2e8f0;
            --panel-bg: #16213e;
            --border: #0f3460;
            --primary: #e94560;
            --secondary: #533483;
            
            --t-cold: #00b4d8;  /* Синий для 0.0 */
            --t-mid: #fca311;   /* Желтый для 0.7 */
            --t-hot: #e63946;   /* Красный для 1.2 */
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 20px;
        }

        h1 {
            text-align: center;
            color: var(--primary);
            margin-bottom: 5px;
        }
        
        .subtitle {
            text-align: center;
            color: #8892b0;
            margin-bottom: 30px;
            font-size: 0.9em;
        }

        .control-panel {
            background: var(--panel-bg);
            border: 1px solid var(--border);
            padding: 20px;
            border-radius: 8px;
            max-width: 800px;
            margin: 0 auto 30px auto;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #8892b0;
            font-size: 0.9em;
        }

        input[type="text"], input[type="password"], textarea {
            width: 100%;
            background: var(--bg-color);
            border: 1px solid var(--border);
            color: var(--text-color);
            padding: 12px;
            border-radius: 4px;
            box-sizing: border-box;
            font-family: inherit;
            margin-bottom: 15px;
        }
        
        textarea {
            resize: vertical;
            min-height: 100px;
        }

        .btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
            font-size: 1.1em;
            transition: opacity 0.2s;
        }

        .btn:hover { opacity: 0.9; }

        .columns {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .temp-card {
            background: var(--panel-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .temp-header {
            padding: 15px;
            text-align: center;
            border-bottom: 2px solid;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .temp-val {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .temp-desc {
            font-size: 0.8em;
            opacity: 0.8;
        }

        #header-cold { border-color: var(--t-cold); }
        #header-mid { border-color: var(--t-mid); }
        #header-hot { border-color: var(--t-hot); }

        #val-cold { color: var(--t-cold); }
        #val-mid { color: var(--t-mid); }
        #val-hot { color: var(--t-hot); }

        .result-box {
            padding: 15px;
            flex-grow: 1;
            min-height: 300px;
            max-height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.6;
            font-size: 0.95em;
            background: rgba(0,0,0,0.2);
        }

        .conclusions {
            max-width: 1400px;
            margin: 30px auto;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }

        .conclusion-box {
            background: rgba(22, 33, 62, 0.5);
            border: 1px dashed var(--border);
            padding: 15px;
            border-radius: 4px;
            font-size: 0.9em;
            color: #a6b2c0;
        }
        
        .conclusion-box h4 {
            margin-top: 0;
            color: #fff;
        }

    </style>
</head>
<body>
    <h1>Тепловизор ИИ (День 4)</h1>
    <div class="subtitle">Влияние параметра Temperature на генерацию текста</div>

    <div class="control-panel">
        <label>API Key (a101.ru):</label>
        <input type="password" id="apiKey" placeholder="Введите ключ a101...">

        <label>Запрос (Креативный, чтобы увидеть разницу):</label>
        <textarea id="taskInput">Придумай название и короткое описание (2 предложения) для нового стартапа, который занимается доставкой кофе с помощью радиоуправляемых дронов.</textarea>

        <button class="btn" onclick="startTest()">СГЕНЕРИРОВАТЬ 3 ВАРИАНТА</button>
    </div>

    <div class="columns">
        <!-- Т = 0.0 -->
        <div class="temp-card">
            <div class="temp-header" id="header-cold">
                <div>
                    <div class="temp-val" id="val-cold">T = 0.0</div>
                    <div class="temp-desc">Абсолютный ноль</div>
                </div>
            </div>
            <div class="result-box" id="res-0">Ожидание запуска...</div>
        </div>

        <!-- Т = 0.7 -->
        <div class="temp-card">
            <div class="temp-header" id="header-mid">
                <div>
                    <div class="temp-val" id="val-mid">T = 0.7</div>
                    <div class="temp-desc">Баланс (Стандарт)</div>
                </div>
            </div>
            <div class="result-box" id="res-07">Ожидание запуска...</div>
        </div>

        <!-- Т = 1.2 -->
        <div class="temp-card">
            <div class="temp-header" id="header-hot">
                <div>
                    <div class="temp-val" id="val-hot">T = 1.2</div>
                    <div class="temp-desc">Горячка (Хаос)</div>
                </div>
            </div>
            <div class="result-box" id="res-12">Ожидание запуска...</div>
        </div>
    </div>

    <div class="conclusions">
        <div class="conclusion-box">
            <h4>💡 Выводы для T = 0.0</h4>
            <ul>
                <li><b>Точность:</b> Максимальная. Всегда выбирает наиболее вероятный следующий токен.</li>
                <li><b>Креативность:</b> Нулевая. Ответы сухие и предсказуемые.</li>
                <li><b>Разнообразие:</b> Отсутствует. Если отправить этот же запрос 10 раз, ответ будет идентичным до буквы.</li>
                <li style="color: var(--t-cold);"><b>Для чего:</b> Код, парсинг данных (JSON/XML), математика, строгий анализ, юридические документы.</li>
            </ul>
        </div>
        <div class="conclusion-box">
            <h4>💡 Выводы для T = 0.7</h4>
            <ul>
                <li><b>Точность:</b> Хорошая. Сохраняет контекст и логику.</li>
                <li><b>Креативность:</b> Умеренная. Использует синонимы и строит интересные предложения.</li>
                <li><b>Разнообразие:</b> Приемлемое. При повторном запросе текст будет немного отличаться.</li>
                <li style="color: var(--t-mid);"><b>Для чего:</b> Написание статей, email, чат-боты, генерация контента (стандарт по умолчанию).</li>
            </ul>
        </div>
        <div class="conclusion-box">
            <h4>💡 Выводы для T = 1.2</h4>
            <ul>
                <li><b>Точность:</b> Низкая. Возможны галлюцинации и потеря логики (бред).</li>
                <li><b>Креативность:</b> Максимальная (вплоть до абсурда).</li>
                <li><b>Разнообразие:</b> Огромное. Выбирает редкие и неожиданные слова.</li>
                <li style="color: var(--t-hot);"><b>Для чего:</b> Брейншторминг безумных идей, поэзия, придумывание фантастических имен (требует ручной фильтрации человеком).</li>
            </ul>
        </div>
    </div>

    <script>
        async function fetchAPI(apiKey, prompt, temp, targetId) {
            const resBox = document.getElementById(`res-${targetId}`);
            resBox.innerHTML = '<span style="color: #8892b0;">Генерация...</span>';
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ apiKey, prompt, temp })
                });
                const data = await response.json();
                
                if (data.error) {
                    resBox.innerHTML = `<span style="color: var(--error);">[Ошибка] ${data.error}</span>`;
                } else {
                    resBox.innerText = data.text;
                }
            } catch (err) {
                resBox.innerHTML = `<span style="color: var(--error);">[Сбой] ${err.message}</span>`;
            }
        }

        function startTest() {
            const apiKey = document.getElementById('apiKey').value;
            const prompt = document.getElementById('taskInput').value;
            
            if (!apiKey) {
                alert("Необходим ключ API!"); return;
            }

            // Запускаем три запроса параллельно с разной температурой
            fetchAPI(apiKey, prompt, 0.0, '0');
            fetchAPI(apiKey, prompt, 0.7, '07');
            fetchAPI(apiKey, prompt, 1.2, '12');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    api_key = data.get('apiKey')
    prompt = data.get('prompt')
    temperature = data.get('temp', 0.7)

    if not api_key:
        return jsonify({"error": "API Key is missing."}), 400

    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Для высоких температур снижаем вероятность бессмыслицы и обрыва,
    # добавляя системный промпт, чтобы ИИ держал структуру.
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Ты - генератор идей. Отвечай полно, красиво и всегда заканчивай свою мысль до конца, не обрывая текст на середине предложения."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1500
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        resp_data = response.json()
        
        try:
            text = resp_data['choices'][0]['message']['content']
            return jsonify({"text": text})
        except (KeyError, IndexError):
            return jsonify({"error": "Неожиданный ответ API"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f">>> СЕРВЕР ДНЯ 4 ЗАПУЩЕН НА ПОРТУ 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
