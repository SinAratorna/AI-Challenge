from flask import Flask, request, jsonify, render_template_string
from agent import CompressionAgent

app = Flask(__name__)

# Инициализируем агента (хранит максимум 4 сообщения как есть, остальное жмет)
agent = CompressionAgent(api_key="", max_history_len=4)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>День 9 - Сжатие контекста</title>
    <style>
        :root {
            --bg: #121212;
            --surface: #1e1e1e;
            --surface-light: #2d2d2d;
            --primary: #bb86fc;
            --secondary: #03dac6;
            --error: #cf6679;
            --text: #ffffff;
            --text-dim: #b3b3b3;
            --border: #333333;
        }
        body {
            background: var(--bg); color: var(--text);
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0; padding: 20px;
            display: flex; gap: 20px;
            height: 100vh; box-sizing: border-box;
        }
        
        .main-col { flex: 2; display: flex; flex-direction: column; max-width: 800px; }
        .side-col { flex: 1; min-width: 300px; max-width: 400px; display: flex; flex-direction: column; gap: 15px; }
        
        h1, h2, h3 { margin: 0 0 10px 0; color: var(--primary); }
        .desc { color: var(--text-dim); margin-bottom: 20px; font-size: 0.9em; }

        .chat-box {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 12px; display: flex; flex-direction: column; flex-grow: 1;
            overflow: hidden;
        }
        
        .chat-header {
            padding: 15px; background: var(--surface-light); border-bottom: 1px solid var(--border);
            display: flex; gap: 10px; align-items: center; justify-content: space-between;
        }
        
        .chat-history {
            flex-grow: 1; padding: 20px; overflow-y: auto;
            display: flex; flex-direction: column; gap: 12px;
        }
        
        .msg { max-width: 85%; padding: 12px 16px; border-radius: 12px; line-height: 1.5; white-space: pre-wrap; }
        .msg-user { align-self: flex-end; background: #3700b3; border: 1px solid #6200ea; border-bottom-right-radius: 2px; }
        .msg-agent { align-self: flex-start; background: var(--surface-light); border: 1px solid var(--border); border-bottom-left-radius: 2px; }
        
        .input-area {
            padding: 15px; background: var(--surface); border-top: 1px solid var(--border);
            display: flex; flex-direction: column; gap: 10px;
        }
        
        input, textarea {
            background: var(--bg); color: var(--text);
            border: 1px solid var(--border); padding: 10px; border-radius: 6px;
            font-family: inherit; font-size: 14px;
        }
        input:focus, textarea:focus { outline: none; border-color: var(--primary); }
        
        textarea { resize: none; height: 60px; }
        
        .btn {
            background: var(--primary); color: #000; border: none;
            padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;
        }
        .btn:hover { background: #9965f4; }
        
        .btn-outline { background: transparent; border: 1px solid var(--error); color: var(--error); padding: 8px 12px; }
        .btn-outline:hover { background: rgba(207, 102, 121, 0.1); }

        /* Панель памяти */
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
        
        .memory-block {
            background: var(--bg);
            border: 1px dashed var(--secondary);
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 0.9em;
            line-height: 1.5;
            color: var(--secondary);
        }

        .stat-row { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 0.9em; border-bottom: 1px solid var(--border); padding-bottom: 5px; }
        .stat-val { font-family: monospace; font-weight: bold; color: var(--primary); font-size: 1.1em; }
        
        .comp-alert {
            background: rgba(3, 218, 198, 0.1);
            color: var(--secondary);
            padding: 10px;
            border-radius: 6px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 15px;
            display: none;
        }

        .toggle-box {
            display: flex; align-items: center; gap: 10px;
            background: rgba(187, 134, 252, 0.1);
            padding: 10px; border-radius: 6px; border: 1px solid var(--primary);
        }
    </style>
</head>
<body>

    <div class="main-col">
        <h1>Сжатие Контекста (День 9)</h1>
        <div class="desc">Агент запоминает только 4 последних сообщения. Старые он архивирует в "Summary", экономя токены.</div>

        <div class="chat-box">
            <div class="chat-header">
                <input type="password" id="apiKey" placeholder="API Key (a101.ru)..." style="width: 200px;">
                
                <div class="toggle-box">
                    <input type="checkbox" id="compToggle" checked>
                    <label for="compToggle" style="font-size: 0.85em; font-weight: bold; color: var(--primary);">Включить Сжатие</label>
                </div>
                
                <button class="btn btn-outline" onclick="clearMemory()">Сброс</button>
            </div>
            
            <div class="chat-history" id="chatHistory"></div>

            <div class="input-area">
                <div style="display: flex; gap: 10px;">
                    <textarea id="userInput" style="flex-grow: 1;" placeholder="Рассказывай факты о себе (имя, город, хобби). После 4 сообщения агент сожмет их в архив!" onkeypress="handleEnter(event)"></textarea>
                    <button class="btn" onclick="sendMessage()">Отправить</button>
                </div>
            </div>
        </div>
    </div>

    <div class="side-col">
        <div class="card">
            <h2>🧠 Мозг Агента</h2>
            
            <div id="compAlert" class="comp-alert">
                ✨ Только что произошло сжатие истории!
            </div>
            
            <div class="stat-row">
                <span>Токенов отправлено (Контекст):</span>
                <span class="stat-val" id="st-tokens">0</span>
            </div>
            <div class="stat-row">
                <span>Несжатых сообщений (Лимит 4):</span>
                <span class="stat-val" id="st-raw">0</span>
            </div>

            <h3 style="margin-top: 25px; font-size: 1em;">Архив Памяти (Summary):</h3>
            <div class="memory-block" id="summaryBox">
                Сжатие еще не производилось. История пуста.
            </div>
            
            <p style="font-size: 0.8em; color: var(--text-dim); margin-top: 20px;">
                Если отключить галочку "Сжатие", агент будет копить все сообщения "как есть", и "Токены контекста" будут бесконечно расти. 
                Со сжатием — рост токенов стабилизируется!
            </p>
        </div>
    </div>

    <script>
        window.onload = async function() {
            try {
                const response = await fetch('/get_history');
                const data = await response.json();
                const historyDiv = document.getElementById('chatHistory');
                data.recent.forEach(msg => addMessage(msg.content, msg.role === 'user'));
                updateBrain(data.summary, data.recent.length, 0, false);
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
            const enableComp = document.getElementById('compToggle').checked;
            const userText = inputEl.value.trim();

            if (!userText) return;
            if (!apiKey) { alert("API Key!"); return; }

            addMessage(userText, true);
            inputEl.value = '';

            const thinkingMsg = addMessage("Обработка (возможно идет сжатие истории)...", false);
            thinkingMsg.style.opacity = '0.5';
            
            document.getElementById('compAlert').style.display = 'none';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ apiKey, message: userText, comp: enableComp })
                });
                const data = await response.json();
                
                thinkingMsg.remove();
                
                if (data.error) {
                    addMessage(`[Ошибка]: ${data.error}`, false);
                } else {
                    addMessage(data.reply, false);
                    updateBrain(data.stats.summary_text, data.stats.raw_msg_count, data.stats.context_tokens, data.stats.just_compressed);
                }
            } catch (err) {
                thinkingMsg.remove();
                addMessage(`[Система]: ${err.message}`, false);
            }
        }
        
        function updateBrain(summary, rawCount, tokens, justComp) {
            document.getElementById('st-tokens').innerText = tokens || '-';
            document.getElementById('st-raw').innerText = rawCount;
            
            const sb = document.getElementById('summaryBox');
            if(summary) {
                sb.innerText = summary;
                sb.style.color = 'var(--secondary)';
            } else {
                sb.innerText = 'Сжатие еще не производилось. История пуста.';
                sb.style.color = 'var(--text-dim)';
            }
            
            if (justComp) {
                const al = document.getElementById('compAlert');
                al.style.display = 'block';
                setTimeout(() => al.style.display = 'none', 4000);
            }
        }

        async function clearMemory() {
            if(!confirm("Стереть всю память (и архив, и текущие сообщения)?")) return;
            await fetch('/clear', { method: 'POST' });
            document.getElementById('chatHistory').innerHTML = '';
            updateBrain('', 0, 0, false);
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
    return jsonify({
        "recent": [msg for msg in agent.recent_messages if msg['role'] != 'system'],
        "summary": agent.summary
    })

@app.route('/clear', methods=['POST'])
def clear_memory():
    agent.clear_memory()
    return jsonify({"status": "ok"})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    agent.api_key = data.get('apiKey')
    user_message = data.get('message')
    comp_enabled = data.get('comp', True)

    if not agent.api_key:
        return jsonify({"error": "API Key is missing."}), 400

    # Обрабатываем сообщение
    result = agent.process_request(user_message, enable_compression=comp_enabled)

    if "error" in result:
        return jsonify({"error": result["error"]})

    return jsonify({
        "reply": result["reply"],
        "stats": result["stats"]
    })

if __name__ == '__main__':
    print(f">>> СЖАТИЕ КОНТЕКСТА (ДЕНЬ 9) ЗАПУЩЕНО НА ПОРТУ 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
