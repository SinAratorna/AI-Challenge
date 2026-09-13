from flask import Flask, request, jsonify, render_template_string
from agent import MemoryAgent

app = Flask(__name__)

# Инициализируем агента глобально, чтобы при старте сервера он сразу загрузил историю из файла
# API ключ передадим позже при первом запросе
agent = MemoryAgent(api_key="")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>День 7 - Агент с Памятью</title>
    <style>
        :root {
            --primary: #10b981;
            --bg: #1e293b;
            --surface: #0f172a;
            --text: #f8fafc;
            --border: #334155;
            --agent-msg: #1e293b;
            --user-msg: #064e3b;
        }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Inter', -apple-system, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
            box-sizing: border-box;
        }
        h1 { margin-bottom: 5px; color: var(--primary); }
        .subtitle { color: #94a3b8; margin-bottom: 20px; }
        
        .chat-container {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            width: 100%;
            max-width: 800px;
            display: flex;
            flex-direction: column;
            flex-grow: 1;
            max-height: 800px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            overflow: hidden;
        }
        .chat-header {
            padding: 15px 20px;
            background: #1e293b;
            border-bottom: 1px solid var(--border);
            display: flex;
            gap: 15px;
            align-items: center;
            justify-content: space-between;
        }
        .api-input {
            flex-grow: 1;
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg);
            color: var(--text);
        }
        .btn-clear {
            background: transparent;
            color: #ef4444;
            border: 1px solid #ef4444;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-clear:hover { background: #ef4444; color: white; }
        
        .chat-history {
            flex-grow: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .msg {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.5;
            white-space: pre-wrap;
        }
        .msg-user {
            align-self: flex-end;
            background: var(--user-msg);
            border: 1px solid #047857;
            border-bottom-right-radius: 2px;
        }
        .msg-agent {
            align-self: flex-start;
            background: var(--agent-msg);
            border: 1px solid var(--border);
            border-bottom-left-radius: 2px;
        }
        
        .chat-input-area {
            padding: 20px;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 10px;
            background: var(--surface);
        }
        .chat-input {
            flex-grow: 1;
            padding: 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg);
            color: var(--text);
            font-family: inherit;
            resize: none;
            height: 24px;
        }
        .chat-input:focus { outline: none; border-color: var(--primary); }
        .btn-send {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn-send:hover { background: #059669; }
        
        .sys-msg {
            text-align: center;
            color: #94a3b8;
            font-size: 0.85em;
            margin: 10px 0;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>Агент с Памятью (День 7)</h1>
    <div class="subtitle">Сохранение контекста между перезапусками сервера (JSON)</div>

    <div class="chat-container">
        <div class="chat-header">
            <input type="password" id="apiKey" class="api-input" placeholder="API Key (a101.ru)...">
            <button class="btn-clear" onclick="clearMemory()">Очистить память</button>
        </div>
        
        <div class="chat-history" id="chatHistory">
            <!-- История загрузится сюда при старте страницы -->
        </div>

        <div class="chat-input-area">
            <textarea class="chat-input" id="userInput" placeholder="Напиши что-нибудь (например: 'Меня зовут Николай, я учусь программировать')" onkeypress="handleEnter(event)"></textarea>
            <button class="btn-send" onclick="sendMessage()">Отправить</button>
        </div>
    </div>

    <script>
        // Загрузка истории при старте страницы
        window.onload = async function() {
            try {
                const response = await fetch('/get_history');
                const history = await response.json();
                
                const historyDiv = document.getElementById('chatHistory');
                
                if (history.length > 0) {
                    const sysDiv = document.createElement('div');
                    sysDiv.className = 'sys-msg';
                    sysDiv.innerText = `--- Восстановлено ${history.length} сообщений из памяти ---`;
                    historyDiv.appendChild(sysDiv);
                    
                    history.forEach(msg => {
                        addMessage(msg.content, msg.role === 'user');
                    });
                } else {
                    addMessage("Привет! Я Агент с долгосрочной памятью. Все, что ты здесь напишешь, сохранится в файл. Если ты перезапустишь сервер, я все равно буду помнить наш разговор.", false);
                }
            } catch (e) {
                console.error("Ошибка загрузки истории", e);
            }
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
            const userText = inputEl.value.trim();

            if (!userText) return;
            if (!apiKey) {
                alert("Пожалуйста, введите API Key!");
                return;
            }

            addMessage(userText, true);
            inputEl.value = '';

            const thinkingMsg = addMessage("Запись в память и обращение к LLM...", false);
            thinkingMsg.style.opacity = '0.5';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ apiKey: apiKey, message: userText })
                });
                const data = await response.json();
                
                thinkingMsg.remove();
                
                if (data.error) {
                    addMessage(`[Ошибка]: ${data.error}`, false);
                } else {
                    addMessage(data.reply, false);
                }
            } catch (err) {
                thinkingMsg.remove();
                addMessage(`[Системная Ошибка]: ${err.message}`, false);
            }
        }

        async function clearMemory() {
            if(!confirm("Уверен, что хочешь стереть агенту память? Файл истории будет удален.")) return;
            
            try {
                await fetch('/clear', { method: 'POST' });
                document.getElementById('chatHistory').innerHTML = '';
                const sysDiv = document.createElement('div');
                sysDiv.className = 'sys-msg';
                sysDiv.innerText = "--- Память очищена ---";
                document.getElementById('chatHistory').appendChild(sysDiv);
            } catch (e) {
                alert("Ошибка при очистке памяти");
            }
        }

        function handleEnter(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
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
    # Отдаем текущую загруженную историю на фронтенд
    return jsonify(agent.get_history())

@app.route('/clear', methods=['POST'])
def clear_memory():
    agent.clear_memory()
    return jsonify({"status": "ok"})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    # Обновляем ключ агента из формы
    agent.api_key = data.get('apiKey')
    user_message = data.get('message')

    if not agent.api_key:
        return jsonify({"error": "API Key is missing."}), 400

    # Передаем запрос агенту.
    # Внутри process_request он добавит сообщение в историю, отправит запрос с контекстом
    # и запишет ответ в файл history.json
    reply = agent.process_request(user_message)

    return jsonify({"reply": reply})

if __name__ == '__main__':
    print(f">>> АГЕНТ С ПАМЯТЬЮ (ДЕНЬ 7) ЗАПУЩЕН НА ПОРТУ 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
