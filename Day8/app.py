from flask import Flask, request, jsonify, render_template_string
from agent import TokenAwareAgent

app = Flask(__name__)

# Инициализация агента. 
# Используем дешевую модель по умолчанию.
agent = TokenAwareAgent(api_key="")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>День 8 - Экономика Токенов</title>
    <style>
        :root {
            --primary: #3b82f6;
            --danger: #ef4444;
            --warning: #f59e0b;
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --text: #f8fafc;
            --text-dim: #94a3b8;
            --border: #334155;
        }
        body {
            background: var(--bg); color: var(--text);
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0; padding: 20px;
            display: flex; gap: 20px;
            height: 100vh; box-sizing: border-box;
        }
        
        .main-col { flex: 2; display: flex; flex-direction: column; max-width: 800px; }
        .stats-col { flex: 1; min-width: 300px; max-width: 400px; display: flex; flex-direction: column; gap: 15px; }
        
        h1, h2 { margin: 0 0 10px 0; color: var(--text); }
        .desc { color: var(--text-dim); margin-bottom: 20px; font-size: 0.9em; }

        .chat-box {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 12px; display: flex; flex-direction: column; flex-grow: 1;
            overflow: hidden;
        }
        
        .chat-header {
            padding: 15px; background: #0f172a; border-bottom: 1px solid var(--border);
            display: flex; gap: 10px; align-items: center;
        }
        .chat-header input { flex-grow: 1; }
        
        .chat-history {
            flex-grow: 1; padding: 20px; overflow-y: auto;
            display: flex; flex-direction: column; gap: 12px;
        }
        
        .msg { max-width: 85%; padding: 12px 16px; border-radius: 12px; line-height: 1.5; white-space: pre-wrap; }
        .msg-user { align-self: flex-end; background: #1e3a8a; border: 1px solid #1e40af; border-bottom-right-radius: 2px; }
        .msg-agent { align-self: flex-start; background: #334155; border: 1px solid var(--border); border-bottom-left-radius: 2px; }
        
        .input-area {
            padding: 15px; background: var(--surface); border-top: 1px solid var(--border);
            display: flex; flex-direction: column; gap: 10px;
        }
        
        input, textarea, select {
            background: var(--bg); color: var(--text);
            border: 1px solid var(--border); padding: 10px; border-radius: 6px;
            font-family: inherit; font-size: 14px;
        }
        input:focus, textarea:focus { outline: none; border-color: var(--primary); }
        
        textarea { resize: none; height: 60px; }
        
        .btn {
            background: var(--primary); color: white; border: none;
            padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;
        }
        .btn:hover { opacity: 0.9; }
        .btn-danger { background: transparent; border: 1px solid var(--danger); color: var(--danger); }
        .btn-danger:hover { background: var(--danger); color: white; }

        /* Панель статистики */
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
        
        .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border); }
        .stat-row:last-child { border-bottom: none; }
        .stat-val { font-family: monospace; font-weight: bold; font-size: 1.1em; color: var(--primary); }
        
        .alert { background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: #fca5a5; padding: 15px; border-radius: 8px; font-size: 0.9em; display: none; margin-top: 15px; }
        .alert-title { font-weight: bold; color: var(--danger); margin-bottom: 5px; }
    </style>
</head>
<body>

    <div class="main-col">
        <h1>Экономика Токенов (День 8)</h1>
        <div class="desc">Агент считает токены до и после запроса. Следите за правой панелью.</div>

        <div class="chat-box">
            <div class="chat-header">
                <input type="password" id="apiKey" placeholder="API Key (a101.ru)...">
                <button class="btn btn-danger" onclick="clearMemory()">Очистить историю</button>
            </div>
            
            <div class="chat-history" id="chatHistory"></div>

            <div class="input-area">
                <div style="display: flex; gap: 10px; align-items: center;">
                    <label style="font-size: 0.85em; color: var(--text-dim);">Искусственный лимит модели (max_tokens):</label>
                    <select id="limitSelect" style="width: 150px;">
                        <option value="1000">1000 (Нормально)</option>
                        <option value="50">50 (Сломать ответ)</option>
                        <option value="10">10 (Жесткая нехватка)</option>
                    </select>
                    <span style="font-size: 0.75em; color: var(--warning);">*Уменьшите лимит, чтобы вызвать переполнение (finish_reason: length)</span>
                </div>
                <div style="display: flex; gap: 10px;">
                    <textarea id="userInput" style="flex-grow: 1;" placeholder="Отправь короткое сообщение, а потом попроси написать длинную историю..." onkeypress="handleEnter(event)"></textarea>
                    <button class="btn" onclick="sendMessage()">Отправить</button>
                </div>
            </div>
        </div>
    </div>

    <div class="stats-col">
        <div class="card">
            <h2>📊 Аналитика текущего хода</h2>
            
            <div class="stat-row">
                <span title="Только текст вашего текущего сообщения">Токены запроса:</span>
                <span class="stat-val" id="st-req">0</span>
            </div>
            
            <div class="stat-row">
                <span title="Вся сохраненная история ДО этого запроса">Токены истории:</span>
                <span class="stat-val" id="st-hist">0</span>
            </div>
            
            <div class="stat-row" style="background: rgba(59, 130, 246, 0.1); padding: 10px 5px; margin: 10px 0; border-radius: 4px;">
                <span title="История + Система + Текущий запрос"><b>Отправлено в API:</b></span>
                <span class="stat-val" id="st-sent" style="color: #60a5fa;">0</span>
            </div>
            
            <div class="stat-row">
                <span title="Сколько текста сгенерировала модель">Токены ответа:</span>
                <span class="stat-val" id="st-resp">0</span>
            </div>
            
            <div class="stat-row" style="border-top: 2px solid var(--border); margin-top: 10px; padding-top: 15px;">
                <span title="За что мы в итоге платим"><b>ИТОГО (Total Usage):</b></span>
                <span class="stat-val" id="st-total" style="color: #10b981;">0</span>
            </div>
            
            <div class="stat-row" style="margin-top: 15px; font-size: 0.85em;">
                <span style="color: var(--text-dim);">Причина остановки:</span>
                <span class="stat-val" id="st-reason" style="font-size: 1em; color: var(--text-dim);">-</span>
            </div>

            <div id="truncAlert" class="alert">
                <div class="alert-title">⚠ ПЕРЕПОЛНЕНИЕ ЛИМИТА!</div>
                Генерация оборвана (finish_reason: length). 
                Модели не хватило <b>max_tokens</b>, чтобы дописать мысль до конца. Это ломает JSON и логику.
            </div>
        </div>
        
        <div class="card">
            <h3 style="margin-top: 0; font-size: 1.1em; color: var(--warning);">💸 Как растет цена?</h3>
            <p style="font-size: 0.85em; color: var(--text-dim); line-height: 1.5; margin-bottom: 0;">
                Обратите внимание на поле <b>"Отправлено в API"</b>. 
                С каждым новым сообщением туда летит вся прошлая история.<br><br>
                Если диалог станет длинным (например, 5000 токенов истории), то <b>КАЖДЫЙ</b> ваш "Привет" будет обходиться вам в стоимость отправки 5001 токена.
            </p>
        </div>
    </div>

    <script>
        // Загрузка начальной истории
        window.onload = async function() {
            try {
                const response = await fetch('/get_history');
                const history = await response.json();
                const historyDiv = document.getElementById('chatHistory');
                history.forEach(msg => addMessage(msg.content, msg.role === 'user'));
            } catch (e) { console.error(e); }
        };

        function addMessage(text, isUser) {
            const history = document.getElementById('chatHistory');
            const msgDiv = document.createElement('div');
            msgDiv.className = `msg ${isUser ? 'msg-user' : 'msg-agent'}`;
            msgDiv.innerText = text;
            history.appendChild(msgDiv);
            history.scrollTop = history.scrollHeight;
            return msgDiv;
        }

        async function sendMessage() {
            const apiKey = document.getElementById('apiKey').value;
            const inputEl = document.getElementById('userInput');
            const limit = parseInt(document.getElementById('limitSelect').value);
            const userText = inputEl.value.trim();

            if (!userText) return;
            if (!apiKey) { alert("API Key!"); return; }

            addMessage(userText, true);
            inputEl.value = '';

            const thinkingMsg = addMessage("Считаю токены и жду ответ...", false);
            thinkingMsg.style.opacity = '0.5';
            
            // Прячем алерт перед новым запросом
            document.getElementById('truncAlert').style.display = 'none';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ apiKey, message: userText, forceMaxTokens: limit })
                });
                const data = await response.json();
                
                thinkingMsg.remove();
                
                if (data.error) {
                    addMessage(`[Ошибка]: ${data.error}`, false);
                } else {
                    addMessage(data.reply, false);
                    updateStats(data.stats);
                }
            } catch (err) {
                thinkingMsg.remove();
                addMessage(`[Система]: ${err.message}`, false);
            }
        }
        
        function updateStats(stats) {
            document.getElementById('st-req').innerText = stats.request_tokens;
            document.getElementById('st-hist').innerText = stats.history_tokens_before;
            document.getElementById('st-sent').innerText = stats.context_sent_tokens;
            document.getElementById('st-resp').innerText = stats.response_tokens;
            document.getElementById('st-total').innerText = stats.total_tokens;
            
            const reasonEl = document.getElementById('st-reason');
            reasonEl.innerText = stats.finish_reason;
            
            if (stats.is_truncated) {
                reasonEl.style.color = 'var(--danger)';
                document.getElementById('truncAlert').style.display = 'block';
            } else {
                reasonEl.style.color = 'var(--text-dim)';
            }
        }

        async function clearMemory() {
            if(!confirm("Стереть память?")) return;
            await fetch('/clear', { method: 'POST' });
            document.getElementById('chatHistory').innerHTML = '';
            
            // Сброс статы
            document.getElementById('st-req').innerText = '0';
            document.getElementById('st-hist').innerText = '0';
            document.getElementById('st-sent').innerText = '0';
            document.getElementById('st-resp').innerText = '0';
            document.getElementById('st-total').innerText = '0';
            document.getElementById('st-reason').innerText = '-';
            document.getElementById('truncAlert').style.display = 'none';
        }

        function handleEnter(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault(); sendMessage();
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_history', methods=['GET'])
def get_history():
    return jsonify([msg for msg in agent.history if msg['role'] != 'system'])

@app.route('/clear', methods=['POST'])
def clear_memory():
    agent.clear_memory()
    return jsonify({"status": "ok"})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    agent.api_key = data.get('apiKey')
    user_message = data.get('message')
    force_max = data.get('forceMaxTokens', 1000)

    if not agent.api_key:
        return jsonify({"error": "API Key is missing."}), 400

    # Агент теперь возвращает не просто строку, а словарь: {"reply": text, "stats": {...}}
    result = agent.process_request(user_message, force_max_tokens=force_max)

    if "error" in result:
        return jsonify({"error": result["error"]})

    return jsonify({
        "reply": result["reply"],
        "stats": result["stats"]
    })

if __name__ == '__main__':
    print(f">>> ЭКОНОМИКА ТОКЕНОВ (ДЕНЬ 8) ЗАПУЩЕНА НА ПОРТУ 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
