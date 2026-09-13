from flask import Flask, request, jsonify, render_template_string
from agent import SimpleAgent

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>День 6 - Первый Агент</title>
    <style>
        :root {
            --primary: #6366f1;
            --bg: #f8fafc;
            --surface: #ffffff;
            --text: #334155;
            --border: #e2e8f0;
            --agent-msg: #eff6ff;
            --user-msg: #f1f5f9;
        }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
            box-sizing: border-box;
        }
        h1 {
            color: var(--text);
            margin-bottom: 5px;
        }
        .subtitle {
            color: #64748b;
            margin-bottom: 20px;
        }
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
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .chat-header {
            padding: 15px 20px;
            background: #f1f5f9;
            border-bottom: 1px solid var(--border);
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .api-input {
            flex-grow: 1;
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.9em;
        }
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
        }
        .msg-user {
            align-self: flex-end;
            background: var(--user-msg);
            border: 1px solid var(--border);
            border-bottom-right-radius: 2px;
        }
        .msg-agent {
            align-self: flex-start;
            background: var(--agent-msg);
            border: 1px solid #bfdbfe;
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
            font-family: inherit;
            font-size: 1em;
            resize: none;
            height: 24px;
        }
        .chat-input:focus {
            outline: none;
            border-color: var(--primary);
        }
        .btn-send {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.2s;
        }
        .btn-send:hover {
            background: #4f46e5;
        }
        .thinking {
            color: #64748b;
            font-style: italic;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>Первый Агент (День 6)</h1>
    <div class="subtitle">Инкапсуляция логики LLM в отдельный класс (сущность)</div>

    <div class="chat-container">
        <div class="chat-header">
            <span style="font-weight: 600;">Настройки Агента:</span>
            <input type="password" id="apiKey" class="api-input" placeholder="Введите ваш API Key (a101.ru)...">
        </div>
        
        <div class="chat-history" id="chatHistory">
            <div class="msg msg-agent">Привет! Я ИИ-Агент. Введи ключ API сверху, напиши мне сообщение, и я обращусь к LLM, чтобы ответить тебе!</div>
        </div>

        <div class="chat-input-area">
            <textarea class="chat-input" id="userInput" placeholder="Напиши сообщение агенту..." onkeypress="handleEnter(event)"></textarea>
            <button class="btn-send" onclick="sendMessage()">Отправить</button>
        </div>
    </div>

    <script>
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

            // Добавляем сообщение юзера в UI
            addMessage(userText, true);
            inputEl.value = '';

            // Показываем статус "Агент думает"
            const thinkingMsg = addMessage("Агент обращается к LLM...", false);
            thinkingMsg.classList.add('thinking');

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ apiKey: apiKey, message: userText })
                });
                const data = await response.json();
                
                // Удаляем статус "думает"
                thinkingMsg.remove();
                
                if (data.error) {
                    addMessage(`[Ошибка Агента]: ${data.error}`, false);
                } else {
                    addMessage(data.reply, false);
                }
            } catch (err) {
                thinkingMsg.remove();
                addMessage(`[Системная Ошибка]: ${err.message}`, false);
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

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    api_key = data.get('apiKey')
    user_message = data.get('message')

    if not api_key:
        return jsonify({"error": "API Key is missing."}), 400

    # Создаем экземпляр нашего Агента!
    # Вся логика запросов к LLM скрыта внутри этого класса.
    agent = SimpleAgent(api_key=api_key)
    
    # Делегируем задачу агенту
    reply = agent.process_request(user_message)

    return jsonify({"reply": reply})

if __name__ == '__main__':
    print(f">>> ЧАТ С АГЕНТОМ (ДЕНЬ 6) ЗАПУЩЕН НА ПОРТУ 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
