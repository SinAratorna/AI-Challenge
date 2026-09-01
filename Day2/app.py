import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# Чтение ключа из файла (согласно opencode.jsonc настройкам ai-private)
# Обрати внимание: в opencode.jsonc указан путь ~/.secrets/ai-private. 
# В Windows это обычно C:\Users\<User>\.secrets\ai-private
# Если его там нет, мы сделаем fallback на локальный .env файл или хардкод (небезопасно, но для тестов сойдет).

def get_api_key():
    try:
        secret_path = os.path.expanduser("~/.secrets/ai-private")
        with open(secret_path, 'r') as f:
            return f.read().strip()
    except Exception:
        print("Warning: Could not read ~/.secrets/ai-private")
        # Для теста: если ключа нет в файле, можно задать его как переменную окружения
        return os.environ.get("GEMINI_API_KEY", "")

# Настройки API из твоего конфига. 
# Запрос ты хотел к модели gemini-3.1-pro-preview.
# ВАЖНО: opencode.jsonc указывает на ai-private (a101.ru) с моделями Qwen.
# Так как ты просил gemini-3.1-pro-preview, я буду использовать стандартный Gemini API Endpoint 
# (или если у тебя есть кастомный прокси, его можно поменять здесь).
# Я сделаю стандартный вызов Google AI API. Если у тебя OpenAI-compatible endpoint, скажи, я переделаю.

GEMINI_API_KEY = get_api_key()
# Стандартный URL для Google Gemini API (v1beta)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={GEMINI_API_KEY}"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Day 2 - AI Cyberpunk Console</title>
    <style>
        :root {
            --neon-green: #39ff14;
            --neon-pink: #ff00ff;
            --neon-blue: #00ffff;
            --dark-bg: #0d0d12;
            --panel-bg: rgba(20, 20, 25, 0.9);
            --border-glitch: #ff003c;
        }

        body {
            background-color: var(--dark-bg);
            color: var(--neon-green);
            font-family: 'Courier New', Courier, monospace;
            margin: 0;
            padding: 20px;
            background-image: 
                linear-gradient(rgba(0, 255, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 255, 255, 0.05) 1px, transparent 1px);
            background-size: 20px 20px;
            overflow-x: hidden;
        }

        h1 {
            text-align: center;
            color: var(--neon-pink);
            text-transform: uppercase;
            letter-spacing: 5px;
            text-shadow: 0 0 10px var(--neon-pink), 0 0 20px var(--neon-pink);
            border-bottom: 2px solid var(--neon-blue);
            padding-bottom: 10px;
            margin-bottom: 30px;
        }

        .container {
            display: flex;
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
            flex-wrap: wrap;
        }

        .panel {
            background: var(--panel-bg);
            border: 1px solid var(--neon-blue);
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
            padding: 20px;
            border-radius: 5px;
            flex: 1;
            min-width: 300px;
            position: relative;
        }
        
        .panel::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: var(--neon-blue);
            box-shadow: 0 0 10px var(--neon-blue);
        }

        .panel-header {
            color: var(--neon-blue);
            margin-top: 0;
            font-size: 1.2em;
            text-shadow: 0 0 5px var(--neon-blue);
            border-bottom: 1px dashed var(--neon-green);
            padding-bottom: 10px;
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-top: 15px;
            color: var(--neon-pink);
            font-weight: bold;
        }

        input[type="text"], input[type="number"], textarea, select {
            width: 100%;
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid var(--neon-green);
            color: var(--neon-blue);
            padding: 10px;
            font-family: 'Courier New', Courier, monospace;
            box-sizing: border-box;
            margin-top: 5px;
            outline: none;
            transition: all 0.3s;
        }

        input:focus, textarea:focus {
            box-shadow: 0 0 10px var(--neon-green);
            border-color: var(--neon-blue);
        }

        textarea {
            resize: vertical;
            min-height: 100px;
        }

        .controls {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .control-group {
            flex: 1;
        }

        button {
            width: 100%;
            background: transparent;
            color: var(--neon-pink);
            border: 1px solid var(--neon-pink);
            padding: 15px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            margin-top: 20px;
            text-transform: uppercase;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }

        button:hover {
            background: var(--neon-pink);
            color: var(--dark-bg);
            box-shadow: 0 0 20px var(--neon-pink);
        }

        .result-box {
            background: #000;
            border: 1px solid var(--neon-blue);
            padding: 15px;
            margin-top: 15px;
            min-height: 200px;
            white-space: pre-wrap;
            overflow-y: auto;
            max-height: 400px;
            color: #ddd;
        }

        .status {
            font-size: 0.9em;
            margin-top: 10px;
            color: var(--neon-pink);
            text-align: right;
            height: 20px;
        }

        /* Сканирующая линия аля киберпанк */
        .scanline {
            width: 100%;
            height: 100px;
            z-index: 9999;
            position: absolute;
            pointer-events: none;
            background: linear-gradient(to bottom, transparent, rgba(0, 255, 255, 0.1), transparent);
            animation: scan 6s linear infinite;
        }
        @keyframes scan {
            0% { top: -100px; }
            100% { top: 100%; }
        }
    </style>
</head>
<body>
    <div class="scanline"></div>
    <h1>[ DAY 2: Response Format Control ]</h1>
    
    <div class="container">
        <!-- Левая панель: Ввод -->
        <div class="panel">
            <h2 class="panel-header">>> INIT_SEQUENCE</h2>
            
            <label>API Key (Gemini):</label>
            <input type="password" id="apiKey" placeholder="Вставь ключ, если его нет в .secrets..." value="{{ api_key_preview }}">
            
            <label>Base Prompt (Запрос):</label>
            <textarea id="basePrompt">Расскажи мне о киберпанке как о жанре. Напиши 2 абзаца.</textarea>
            
            <hr style="border: 0; border-top: 1px dashed var(--neon-green); margin: 20px 0;">
            <h2 class="panel-header" style="color: var(--neon-pink);">> CONSTRAINTS_MODULE</h2>
            
            <label>Format Instruction (Явное описание формата):</label>
            <textarea id="formatInstruction">ОТВЕТ ДОЛЖЕН БЫТЬ В ФОРМАТЕ JSON. Ключи: "title", "paragraph1", "paragraph2".</textarea>
            
            <div class="controls">
                <div class="control-group">
                    <label>Max Tokens:</label>
                    <input type="number" id="maxTokens" value="150" min="10" max="2000">
                </div>
                <div class="control-group">
                    <label>Temperature:</label>
                    <input type="number" id="temperature" value="0.2" min="0" max="2" step="0.1">
                </div>
            </div>

            <label>Stop Sequence (Условие завершения - через запятую):</label>
            <input type="text" id="stopSequence" value="КОНЕЦ,STOP,},]">

            <button onclick="runTest()">EXECUTE_COMPARISON()</button>
        </div>

        <!-- Правая панель 1: Без ограничений -->
        <div class="panel">
            <h2 class="panel-header">>> OUTPUT: NO_CONSTRAINTS</h2>
            <div class="status" id="status-unconstrained">Awaiting Execution...</div>
            <div class="result-box" id="result-unconstrained"></div>
        </div>

        <!-- Правая панель 2: С ограничениями -->
        <div class="panel">
            <h2 class="panel-header" style="color: var(--neon-pink);">>> OUTPUT: CONSTRAINED</h2>
            <div class="status" id="status-constrained">Awaiting Execution...</div>
            <div class="result-box" id="result-constrained" style="border-color: var(--neon-pink);"></div>
        </div>
    </div>

    <script>
        async function sendRequest(payload, targetElement, statusElement) {
            const el = document.getElementById(targetElement);
            const statusEl = document.getElementById(statusElement);
            el.innerHTML = '<span style="color: yellow;">[PROCESSING...]</span>';
            statusEl.innerText = "System working...";
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                
                if (data.error) {
                    el.innerHTML = `<span style="color: red;">[ERROR] ${data.error}</span>`;
                    statusEl.innerText = "Execution Failed";
                } else {
                    el.innerText = data.text;
                    statusEl.innerText = `Tokens generated: ${data.tokens || 'N/A'}`;
                }
            } catch (err) {
                el.innerHTML = `<span style="color: red;">[CRITICAL ERROR] ${err.message}</span>`;
                statusEl.innerText = "Connection Lost";
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
                alert("[SYSTEM ERROR] API Key Required");
                return;
            }

            // 1. Запрос БЕЗ ограничений (только базовый промпт, стандартные параметры)
            const payloadUnconstrained = {
                apiKey: apiKey,
                prompt: basePrompt,
                temperature: 0.7, // Стандартная температура
                maxTokens: 800    // Достаточно большой лимит
            };

            // 2. Запрос С ограничениями
            // Объединяем базовый промпт и инструкцию по формату
            const combinedPrompt = `${basePrompt}\n\nИНСТРУКЦИЯ ПО ФОРМАТУ:\n${formatInstruction}`;
            const payloadConstrained = {
                apiKey: apiKey,
                prompt: combinedPrompt,
                temperature: temperature,
                maxTokens: maxTokens,
                stopSequences: stopSequences
            };

            // Запускаем оба параллельно
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
    # Показываем заглушку, если ключ найден, чтобы не светить его в UI
    key_preview = "***" if GEMINI_API_KEY else "" 
    return render_template_string(HTML_TEMPLATE, api_key_preview=key_preview)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    api_key = data.get('apiKey', GEMINI_API_KEY)
    
    if not api_key or api_key == "***":
        # Если пришел "***", используем системный ключ
        api_key = GEMINI_API_KEY
    
    if not api_key:
        return jsonify({"error": "API Key is missing."}), 400

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={api_key}"
    
    prompt = data.get('prompt', '')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('maxTokens', 800)
    stop_sequences = data.get('stopSequences', [])

    # Формируем тело запроса для Gemini API
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
        
        # Извлекаем текст ответа
        try:
            text = resp_data['candidates'][0]['content']['parts'][0]['text']
            # Примерный подсчет токенов (в реальности Gemini возвращает usageMetadata)
            usage = resp_data.get('usageMetadata', {})
            tokens_generated = usage.get('candidatesTokenCount', len(text.split()))
            
            return jsonify({"text": text, "tokens": tokens_generated})
        except KeyError:
            return jsonify({"error": "Unexpected API response format", "details": resp_data}), 500
            
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if response.content:
            try:
                error_msg += " " + str(response.json())
            except:
                pass
        return jsonify({"error": error_msg}), int(response.status_code) if response.status_code else 500

if __name__ == '__main__':
    print(">>> SYSTEM INITIATED. NEON SERVER RUNNING ON PORT 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
