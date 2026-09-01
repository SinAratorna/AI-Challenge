import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

def get_api_key():
    try:
        secret_path = os.path.expanduser("~/.secrets/ai-private")
        with open(secret_path, 'r') as f:
            return f.read().strip()
    except Exception:
        return os.environ.get("GEMINI_API_KEY", "")

GEMINI_API_KEY = get_api_key()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>День 2 - Эпоха Возрождения (API)</title>
    <style>
        :root {
            --parchment: #fdf5e6;
            --ink: #3e2723;
            --gold: #b8860b;
            --dark-red: #5d0000;
            --panel-bg: #fffbf0;
        }

        body {
            background-color: var(--parchment);
            /* Текстура старой бумаги */
            background-image: url('data:image/svg+xml;utf8,<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><filter id="noise"><feTurbulence type="fractalNoise" baseFrequency="0.01" numOctaves="3" stitchTiles="stitch"/></filter><rect width="200" height="200" filter="url(#noise)" opacity="0.04"/></svg>');
            color: var(--ink);
            font-family: 'Palatino Linotype', 'Book Antiqua', Palatino, serif;
            margin: 0;
            padding: 20px;
        }

        h1 {
            text-align: center;
            color: var(--dark-red);
            text-transform: uppercase;
            letter-spacing: 3px;
            border-bottom: 2px solid var(--gold);
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-weight: normal;
        }

        .container {
            display: flex;
            gap: 25px;
            max-width: 1400px;
            margin: 0 auto;
            flex-wrap: wrap;
        }

        .panel {
            background: var(--panel-bg);
            border: 2px solid #d3c0a3;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.05), 4px 4px 10px rgba(0,0,0,0.1);
            padding: 25px;
            border-radius: 4px;
            flex: 1;
            min-width: 320px;
            position: relative;
        }
        
        .panel::before {
            content: '';
            position: absolute;
            top: 5px; left: 5px; right: 5px; bottom: 5px;
            border: 1px solid rgba(184, 134, 11, 0.3);
            pointer-events: none;
        }

        .panel-header {
            color: var(--dark-red);
            margin-top: 0;
            font-size: 1.4em;
            text-align: center;
            border-bottom: 1px solid #d3c0a3;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-style: italic;
        }

        label {
            display: block;
            margin-top: 15px;
            color: var(--ink);
            font-weight: bold;
        }

        input[type="text"], input[type="password"], textarea {
            width: 100%;
            background: #fffdf8;
            border: 1px solid #c7b49a;
            color: var(--ink);
            padding: 10px;
            font-family: 'Palatino Linotype', serif;
            box-sizing: border-box;
            margin-top: 5px;
            outline: none;
            transition: all 0.3s;
        }

        input:focus, textarea:focus {
            box-shadow: 0 0 8px rgba(184, 134, 11, 0.4);
            border-color: var(--gold);
        }

        textarea {
            resize: vertical;
            min-height: 90px;
        }

        .controls {
            margin-top: 20px;
            padding: 15px;
            background: rgba(211, 192, 163, 0.15);
            border: 1px dashed #c7b49a;
        }

        .slider-container {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 10px;
        }

        input[type="range"] {
            flex: 1;
            accent-color: var(--dark-red);
        }

        .val-display {
            font-weight: bold;
            color: var(--gold);
            min-width: 40px;
            text-align: right;
        }

        button {
            width: 100%;
            background: var(--dark-red);
            color: var(--parchment);
            border: 2px solid var(--gold);
            padding: 12px;
            font-family: 'Palatino Linotype', serif;
            font-size: 1.1em;
            cursor: pointer;
            margin-top: 20px;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: all 0.3s;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        }

        button:hover {
            background: var(--gold);
            color: var(--dark-red);
            border-color: var(--dark-red);
        }

        .result-box {
            background: #fffdf8;
            border: 1px solid #c7b49a;
            padding: 15px;
            margin-top: 15px;
            min-height: 250px;
            white-space: pre-wrap;
            overflow-y: auto;
            max-height: 450px;
            color: var(--ink);
            line-height: 1.6;
        }

        .status {
            font-size: 0.9em;
            margin-top: 10px;
            color: #795548;
            text-align: right;
            height: 20px;
            font-style: italic;
        }

        .connection-panel {
            background: rgba(184, 134, 11, 0.1);
            border: 1px solid var(--gold);
            padding: 15px;
            margin-bottom: 25px;
            text-align: center;
            border-radius: 4px;
        }

        #conn-status-text {
            font-weight: bold;
            margin-left: 10px;
        }
        .status-ok { color: green; }
        .status-err { color: red; }
        .status-wait { color: #b8860b; }
    </style>
</head>
<body>
    <h1>Трактат о Свободном и Формальном Ответе</h1>
    
    <div class="connection-panel">
        <span>Статус Связи с Музами (API):</span>
        <span id="conn-status-text" class="status-wait">Ожидание проверки...</span>
        <button onclick="checkConnection()" style="width: auto; padding: 5px 15px; margin-left: 15px; margin-top: 0; font-size: 0.9em;">Проверить связь</button>
    </div>

    <div class="container">
        <!-- Левая панель: Ввод -->
        <div class="panel">
            <h2 class="panel-header">Перо и Пергамент (Ввод)</h2>
            
            <label>Тайный Ключ (API Key):</label>
            <input type="password" id="apiKey" placeholder="Секретный шифр..." value="{{ api_key_preview }}">
            
            <label>Суть Вопрошания (Запрос):</label>
            <textarea id="basePrompt">Опиши устройство летательной машины Леонардо да Винчи. Два абзаца.</textarea>
            
            <hr style="border: 0; border-top: 1px solid #d3c0a3; margin: 25px 0;">
            <h2 class="panel-header">Строгие Рамки (Контроль)</h2>
            
            <label>Форма изложения (Явное описание формата):</label>
            <textarea id="formatInstruction">ОТВЕТ ДОЛЖЕН БЫТЬ В ФОРМАТЕ JSON. Ключи: "invention", "description", "year".</textarea>
            
            <div class="controls">
                <label>Мера Многословия (Max Tokens):</label>
                <div class="slider-container">
                    <input type="range" id="maxTokens" min="10" max="2000" value="150" oninput="document.getElementById('valTokens').innerText = this.value">
                    <span class="val-display" id="valTokens">150</span>
                </div>
                
                <label>Степень Воображения (Temperature):</label>
                <div class="slider-container">
                    <input type="range" id="temperature" min="0" max="2" step="0.1" value="0.2" oninput="document.getElementById('valTemp').innerText = this.value">
                    <span class="val-display" id="valTemp">0.2</span>
                </div>
            </div>

            <label>Граница Мысли (Stop Sequence - через запятую):</label>
            <input type="text" id="stopSequence" value="АМИНЬ,STOP,},]">

            <button onclick="runTest()">Начать Творение</button>
        </div>

        <!-- Правая панель 1: Без ограничений -->
        <div class="panel">
            <h2 class="panel-header">Полет Фантазии (Без ограничений)</h2>
            <div class="status" id="status-unconstrained">Ожидает вашего слова...</div>
            <div class="result-box" id="result-unconstrained"></div>
        </div>

        <!-- Правая панель 2: С ограничениями -->
        <div class="panel">
            <h2 class="panel-header" style="color: #4a148c;">Чеканная Форма (С ограничениями)</h2>
            <div class="status" id="status-constrained">Ожидает вашего слова...</div>
            <div class="result-box" id="result-constrained" style="border-left: 4px solid var(--dark-red);"></div>
        </div>
    </div>

    <script>
        async function checkConnection() {
            const apiKey = document.getElementById('apiKey').value;
            const statusEl = document.getElementById('conn-status-text');
            
            statusEl.className = 'status-wait';
            statusEl.innerText = "Гонцы отправлены...";
            
            try {
                const response = await fetch('/check_connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ apiKey: apiKey })
                });
                const data = await response.json();
                
                if (data.status === 'ok') {
                    statusEl.className = 'status-ok';
                    statusEl.innerText = "Успешно! " + data.message;
                } else {
                    statusEl.className = 'status-err';
                    statusEl.innerText = "Провал: " + data.message;
                }
            } catch (err) {
                statusEl.className = 'status-err';
                statusEl.innerText = "Ошибка: " + err.message;
            }
        }

        async function sendRequest(payload, targetElement, statusElement) {
            const el = document.getElementById(targetElement);
            const statusEl = document.getElementById(statusElement);
            el.innerHTML = '<span style="color: #b8860b;">[Творим...]</span>';
            statusEl.innerText = "Музы трудятся...";
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                
                if (data.error) {
                    el.innerHTML = `<span style="color: red;">[ОШИБКА] ${data.error}</span>`;
                    statusEl.innerText = "Произошел конфуз";
                } else {
                    el.innerText = data.text;
                    statusEl.innerText = `Написано слов (токенов): ${data.tokens || 'Неизвестно'}`;
                }
            } catch (err) {
                el.innerHTML = `<span style="color: red;">[КРИТИЧЕСКАЯ ОШИБКА] ${err.message}</span>`;
                statusEl.innerText = "Связь потеряна";
            }
        }

        async function runTest() {
            const apiKey = document.getElementById('apiKey').value;
            const basePrompt = document.getElementById('basePrompt').value;
            const formatInstruction = document.getElementById('formatInstruction').value;
            const maxTokens = parseInt(document.getElementById('maxTokens').value);
            const temperature = parseFloat(document.getElementById('temperature').value);
            const stopSeqRaw = document.getElementById('stopSequence').value;
            
            const stopSequences = stopSeqRaw.split(',').map(s => s.trim()).filter(s => s.length > 0);

            if (!apiKey) {
                alert("Необходим Тайный Ключ (API Key)!");
                return;
            }

            const payloadUnconstrained = {
                apiKey: apiKey,
                prompt: basePrompt,
                temperature: 0.7, 
                maxTokens: 800    
            };

            const combinedPrompt = `${basePrompt}\n\nИНСТРУКЦИЯ ПО ФОРМАТУ:\n${formatInstruction}`;
            const payloadConstrained = {
                apiKey: apiKey,
                prompt: combinedPrompt,
                temperature: temperature,
                maxTokens: maxTokens,
                stopSequences: stopSequences
            };

            Promise.all([
                sendRequest(payloadUnconstrained, 'result-unconstrained', 'status-unconstrained'),
                sendRequest(payloadConstrained, 'result-constrained', 'status-constrained')
            ]);
        }
        
        // Проверяем связь при загрузке
        window.onload = () => {
            if(document.getElementById('apiKey').value) {
                checkConnection();
            }
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    key_preview = "***" if GEMINI_API_KEY else "" 
    return render_template_string(HTML_TEMPLATE, api_key_preview=key_preview)

@app.route('/check_connection', methods=['POST'])
def check_connection():
    data = request.json
    api_key = data.get('apiKey', GEMINI_API_KEY)
    
    if not api_key or api_key == "***":
        api_key = GEMINI_API_KEY
        
    if not api_key:
        return jsonify({"status": "error", "message": "Ключ не предоставлен."})

    # Легкий запрос для проверки ключа: получение информации о модели
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify({"status": "ok", "message": "Доступ к ИИ открыт!"})
        else:
            return jsonify({"status": "error", "message": f"Отказ API (Код {response.status_code})"}), response.status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    api_key = data.get('apiKey', GEMINI_API_KEY)
    
    if not api_key or api_key == "***":
        api_key = GEMINI_API_KEY
    
    if not api_key:
        return jsonify({"error": "API Key is missing."}), 400

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={api_key}"
    
    prompt = data.get('prompt', '')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('maxTokens', 800)
    stop_sequences = data.get('stopSequences', [])

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }
    
    if stop_sequences:
        payload["generationConfig"]["stopSequences"] = stop_sequences

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        resp_data = response.json()
        
        try:
            text = resp_data['candidates'][0]['content']['parts'][0]['text']
            usage = resp_data.get('usageMetadata', {})
            tokens_generated = usage.get('candidatesTokenCount', len(text.split()))
            
            return jsonify({"text": text, "tokens": tokens_generated})
        except KeyError:
            return jsonify({"error": "Неожиданный формат ответа API", "details": resp_data}), 500
            
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if response.content:
            try:
                error_msg += " " + str(response.json())
            except:
                pass
        return jsonify({"error": error_msg}), int(response.status_code) if response.status_code else 500

if __name__ == '__main__':
    print(">>> СЕРВЕР ВОЗРОЖДЕНИЯ ЗАПУЩЕН НА ПОРТУ 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
