import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

BASE_URL = "https://ai-public.a101.ru/api"
MODEL_NAME = "google/gemini-3.1-pro-preview"

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

        input[type="text"], input[type="password"], textarea, select {
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
            font-size: 1em;
        }

        input:focus, textarea:focus, select:focus {
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

        .error-console {
            background: var(--dark-red);
            color: #ffcccc;
            padding: 20px;
            margin-top: 25px;
            border: 2px solid var(--gold);
            border-radius: 4px;
            display: none;
            font-family: 'Courier New', Courier, monospace;
            box-shadow: 0 0 15px rgba(93, 0, 0, 0.5);
        }
        .error-console h3 {
            margin-top: 0;
            color: var(--gold);
            border-bottom: 1px solid var(--gold);
            padding-bottom: 5px;
        }
    </style>
</head>
<body>
    <h1>Трактат о Свободном и Формальном Ответе</h1>
    
    <div class="connection-panel">
        <span>Статус Связи с Корпоративной Сетью (a101.ru):</span>
        <span id="conn-status-text" class="status-wait">Ожидание ввода ключа...</span>
        <button onclick="checkConnection()" style="width: auto; padding: 5px 15px; margin-left: 15px; margin-top: 0; font-size: 0.9em;">Проверить связь</button>
    </div>

    <div class="container">
        <!-- Левая панель: Ввод -->
        <div class="panel">
            <h2 class="panel-header">Перо и Пергамент (Ввод)</h2>
            
            <label>Корпоративный Ключ (a101 API Key):</label>
            <input type="password" id="apiKey" placeholder="Вставьте ваш личный ключ a101...">
            
            <label>Суть Вопрошания (Запрос):</label>
            <textarea id="basePrompt">Опиши устройство летательной машины Леонардо да Винчи. Расскажи об этом в двух абзацах.</textarea>
            
            <hr style="border: 0; border-top: 1px solid #d3c0a3; margin: 25px 0;">
            <h2 class="panel-header">Строгие Рамки (Только для Правого окна)</h2>
            
            <label>Желаемый формат:</label>
            <select id="responseFormat" onchange="updateFormatInstruction()">
                <option value="JSON">JSON</option>
                <option value="HTML">HTML</option>
                <option value="XML">XML</option>
                <option value="MARKDOWN">Markdown</option>
            </select>

            <label>Инструкция по формату:</label>
            <textarea id="formatInstruction">ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО В ФОРМАТЕ JSON. Ключи: "invention", "description", "year". Без Markdown форматирования.</textarea>
            
            <div class="controls">
                <label>Мера Многословия (Max Tokens):</label>
                <div class="slider-container">
                    <input type="range" id="maxTokens" min="10" max="800" value="100" oninput="document.getElementById('valTokens').innerText = this.value">
                    <span class="val-display" id="valTokens">100</span>
                </div>
                
                <label>Степень Воображения (Temperature):</label>
                <div class="slider-container">
                    <input type="range" id="temperature" min="0" max="2" step="0.1" value="0.2" oninput="document.getElementById('valTemp').innerText = this.value">
                    <span class="val-display" id="valTemp">0.2</span>
                </div>
            </div>

            <label>Граница Мысли (Stop Sequence - через запятую):</label>
            <input type="text" id="stopSequence" value="},],</p>,АМИНЬ">

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

    <div id="errorBox" class="error-console">
        <h3>[!] Внимание: Замечены Аномалии (Ошибки)</h3>
        <div id="errorText"></div>
    </div>

    <script>
        function updateFormatInstruction() {
            const format = document.getElementById('responseFormat').value;
            const inst = document.getElementById('formatInstruction');
            if (format === 'JSON') {
                inst.value = 'ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО В ФОРМАТЕ JSON. Ключи: "invention", "description", "year". Без Markdown форматирования (без ```json).';
            } else if (format === 'HTML') {
                inst.value = 'ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО В HTML. Используй теги <div>, <h2>, <p>. Не выводи ничего кроме HTML.';
            } else if (format === 'XML') {
                inst.value = 'ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО В XML. Корневой тег <response>. Внутри теги <invention>, <description>, <year>.';
            } else if (format === 'MARKDOWN') {
                inst.value = 'ОТВЕТ ДОЛЖЕН БЫТЬ В MARKDOWN. Используй заголовки (##), жирный шрифт (**) и списки (-).';
            }
        }

        function showError(message) {
            const errorBox = document.getElementById('errorBox');
            const errorText = document.getElementById('errorText');
            errorBox.style.display = 'block';
            errorText.innerHTML += `<div>- ${new Date().toLocaleTimeString()}: ${message}</div>`;
        }

        function clearErrors() {
            document.getElementById('errorBox').style.display = 'none';
            document.getElementById('errorText').innerHTML = '';
        }

        async function checkConnection() {
            const apiKey = document.getElementById('apiKey').value;
            const statusEl = document.getElementById('conn-status-text');
            
            if (!apiKey) {
                alert("Пожалуйста, введите ваш корпоративный ключ API.");
                return;
            }
            
            statusEl.className = 'status-wait';
            statusEl.innerText = "Гонцы отправлены в корпоративную сеть...";
            clearErrors();
            
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
                    showError("Check Connection API Error: " + data.message);
                }
            } catch (err) {
                statusEl.className = 'status-err';
                statusEl.innerText = "Ошибка сети";
                showError("Network Error on Check Connection: " + err.message);
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
                    el.innerHTML = `<span style="color: red;">[СМОТРИТЕ ОКНО ОШИБОК ВНИЗУ]</span>`;
                    statusEl.innerText = "Произошла ошибка";
                    showError(`Error in ${payload.isConstrained ? 'Constrained' : 'Unconstrained'} Request: ${data.error}`);
                } else {
                    el.innerText = data.text;
                    statusEl.innerText = `Написано слов (токенов): ${data.tokens || 'Неизвестно'}`;
                }
            } catch (err) {
                el.innerHTML = `<span style="color: red;">[ОШИБКА СЕТИ]</span>`;
                statusEl.innerText = "Связь потеряна";
                showError(`Fatal Request Error (${payload.isConstrained ? 'Constrained' : 'Unconstrained'}): ${err.message}`);
            }
        }

        async function runTest() {
            clearErrors();
            const apiKey = document.getElementById('apiKey').value;
            const basePrompt = document.getElementById('basePrompt').value;
            const format = document.getElementById('responseFormat').value;
            const formatInstruction = document.getElementById('formatInstruction').value;
            const maxTokens = parseInt(document.getElementById('maxTokens').value);
            const temperature = parseFloat(document.getElementById('temperature').value);
            const stopSeqRaw = document.getElementById('stopSequence').value;
            
            const stopSequences = stopSeqRaw.split(',').map(s => s.trim()).filter(s => s.length > 0);

            if (!apiKey) {
                alert("Необходим Корпоративный Ключ (API Key)!");
                return;
            }

            // 1. БЕЗ ограничений (Полная свобода)
            // Жестко задаем высокие параметры для генерации длинного и красивого текста
            const payloadUnconstrained = {
                apiKey: apiKey,
                prompt: basePrompt,
                temperature: 0.7, 
                maxTokens: 2000, // Снимаем ограничение! Пусть генерирует до 2000 токенов
                stopSequences: [], // Никаких стоп-слов!
                isConstrained: false
            };

            // 2. С ограничениями (Жесткий контроль)
            // Применяем настройки из ползунков
            const payloadConstrained = {
                apiKey: apiKey,
                prompt: basePrompt,
                temperature: temperature,
                maxTokens: maxTokens, // Тот самый лимит из ползунка (например, 100)
                stopSequences: stopSequences,
                isConstrained: true,
                formatInstruction: formatInstruction
            };

            Promise.all([
                sendRequest(payloadUnconstrained, 'result-unconstrained', 'status-unconstrained'),
                sendRequest(payloadConstrained, 'result-constrained', 'status-constrained')
            ]);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/check_connection', methods=['POST'])
def check_connection():
    data = request.json
    api_key = data.get('apiKey')
    
    if not api_key:
        return jsonify({"status": "error", "message": "Ключ не предоставлен."})

    url = f"{BASE_URL}/models"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return jsonify({"status": "ok", "message": "Доступ к a101.ru открыт!"})
        else:
            return jsonify({"status": "error", "message": f"Отказ API (Код {response.status_code}): {response.text}"}), response.status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    api_key = data.get('apiKey')
    
    if not api_key:
        return jsonify({"error": "API Key is missing."}), 400

    url = f"{BASE_URL}/chat/completions"
    
    user_prompt = data.get('prompt', '')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('maxTokens', 800)
    stop_sequences = data.get('stopSequences', [])
    is_constrained = data.get('isConstrained', False)

    # Системные промпты (очень важно для этой модели)
    if is_constrained:
        fmt_instruction = data.get('formatInstruction', '')
        system_content = (
            "Ты — строгий сервер обработки данных. Отвечай ТОЛЬКО в требуемом формате. "
            "Никакого приветствия. Никаких пояснений. Если просят HTML - только теги. Если JSON - только JSON."
        )
        # Добавляем инструкцию по формату прямо в начало запроса пользователя, чтобы модель не забыла
        user_content = f"{fmt_instruction}\n\nЗАПРОС: {user_prompt}"
    else:
        system_content = (
            "Ты — эрудированный, вежливый историк и эксперт по эпохе Возрождения. "
            "Напиши красивый, литературный и исчерпывающий ответ на русском языке на заданный вопрос. "
            "Используй богатый словарный запас. Пиши текст полностью и законченно."
        )
        user_content = user_prompt

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    if is_constrained and stop_sequences:
        payload["stop"] = stop_sequences

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        resp_data = response.json()
        
        try:
            text = resp_data['choices'][0]['message']['content']
            usage = resp_data.get('usage', {})
            tokens_generated = usage.get('completion_tokens', 'Неизвестно')
            
            return jsonify({"text": text, "tokens": tokens_generated})
        except (KeyError, IndexError):
            return jsonify({"error": "Неожиданный формат ответа от a101.ru", "details": str(resp_data)}), 500
            
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if response.content:
            try:
                error_msg += " | Ответил сервер: " + str(response.json())
            except:
                error_msg += " | Ответил сервер: " + response.text
        return jsonify({"error": error_msg}), int(response.status_code) if response.status_code else 500

if __name__ == '__main__':
    print(f">>> СЕРВЕР ВОЗРОЖДЕНИЯ ЗАПУЩЕН НА ПОРТУ 5000 <<<")
    print(f"Базовый URL: {BASE_URL}")
    print(f"Модель по умолчанию: {MODEL_NAME}")
    app.run(host='0.0.0.0', port=5000, debug=True)
