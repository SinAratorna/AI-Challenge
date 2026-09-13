from flask import Flask, request, jsonify, render_template_string
from agent import AdvancedContextAgent

app = Flask(__name__)

# Инициализация агента
agent = AdvancedContextAgent(api_key="")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>День 10 - Стратегии Контекста</title>
    <style>
        :root {
            --bg: #1e1e2f; --surface: #2a2a40; --text: #e0e0e0;
            --primary: #ff4757; --secondary: #2ed573; --accent: #1e90ff;
            --border: #3d3d5c;
        }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; display: flex; gap: 20px; height: 100vh; box-sizing: border-box; }
        
        .main-col { flex: 2; display: flex; flex-direction: column; min-width: 500px; }
        .side-col { flex: 1; display: flex; flex-direction: column; gap: 15px; min-width: 300px; }
        
        h1, h2, h3 { margin: 0 0 10px 0; }
        h1 { color: var(--primary); }
        .subtitle { color: #a4b0be; margin-bottom: 20px; font-size: 0.9em; }

        .panel { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; }
        
        /* Табы стратегий */
        .tabs { display: flex; gap: 10px; margin-bottom: 15px; }
        .tab { 
            flex: 1; padding: 10px; text-align: center; background: var(--bg); border: 1px solid var(--border); 
            border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.2s;
        }
        .tab.active[data-strat="window"] { background: var(--accent); color: white; border-color: var(--accent); }
        .tab.active[data-strat="facts"] { background: var(--secondary); color: white; border-color: var(--secondary); }
        .tab.active[data-strat="branch"] { background: var(--primary); color: white; border-color: var(--primary); }
        
        .chat-area { flex-grow: 1; border: 1px solid var(--border); border-radius: 6px; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: var(--bg); margin-bottom: 15px; }
        
        .msg { padding: 10px 15px; border-radius: 8px; max-width: 85%; line-height: 1.4; white-space: pre-wrap;}
        .msg-user { align-self: flex-end; background: #3742fa; }
        .msg-agent { align-self: flex-start; background: #2f3542; }

        .input-group { display: flex; gap: 10px; }
        input[type="text"], input[type="password"], textarea { 
            background: var(--bg); color: var(--text); border: 1px solid var(--border); 
            padding: 10px; border-radius: 4px; font-family: inherit; width: 100%; box-sizing: border-box;
        }
        textarea { resize: none; flex-grow: 1; height: 50px; }
        
        button { background: #57606f; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { filter: brightness(1.2); }
        button.btn-primary { background: var(--primary); }
        
        /* Блоки для стратегий (справа) */
        .info-block { display: none; }
        .info-block.active { display: block; }
        
        .facts-list { background: var(--bg); border: 1px dashed var(--secondary); padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.9em; color: var(--secondary); }
        
        .branch-list { display: flex; flex-direction: column; gap: 5px; }
        .branch-btn { background: var(--bg); border: 1px solid var(--border); text-align: left; padding: 8px; border-radius: 4px; }
        .branch-btn.active { border-color: var(--primary); color: var(--primary); background: rgba(255, 71, 87, 0.1); }
        
        .stat-badge { background: #2f3542; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; margin-bottom: 10px; display: inline-block; }
    </style>
</head>
<body>

    <div class="main-col panel">
        <h1>Стратегии Контекста</h1>
        <div class="subtitle">Переключайтесь между стратегиями, чтобы увидеть разницу в поведении памяти.</div>

        <div class="tabs">
            <div class="tab" data-strat="window" onclick="changeStrategy('window')">1. Sliding Window</div>
            <div class="tab" data-strat="facts" onclick="changeStrategy('facts')">2. Sticky Facts</div>
            <div class="tab" data-strat="branch" onclick="changeStrategy('branch')">3. Branching</div>
        </div>
        
        <div style="margin-bottom: 10px; display: flex; justify-content: space-between;">
            <input type="password" id="apiKey" placeholder="API Key (a101.ru)" style="width: 250px;">
            <button onclick="clearMem()">Очистить память</button>
        </div>

        <div class="chat-area" id="chatHistory"></div>

        <div class="input-group">
            <textarea id="userInput" placeholder="Напишите сообщение..."></textarea>
            <button class="btn-primary" onclick="sendMsg()">Отправить</button>
        </div>
    </div>

    <div class="side-col">
        <div class="panel">
            <h2>⚙️ Панель Управления</h2>
            <div id="statTokens" class="stat-badge">Токенов в запросе: 0</div>
            
            <!-- Инфо для Sliding Window -->
            <div id="info-window" class="info-block">
                <h3>🪟 Sliding Window</h3>
                <p style="font-size: 0.9em; color: #a4b0be;">
                    Агент помнит только последние 4 сообщения. Всё, что было сказано раньше — безвозвратно удаляется из контекста.
                    <br><br>
                    <b>Тест:</b> Скажите агенту свое имя, потом напишите 5-6 отвлеченных сообщений, а затем спросите, как вас зовут. Он забудет.
                </p>
            </div>
            
            <!-- Инфо для Facts -->
            <div id="info-facts" class="info-block">
                <h3>📌 Sticky Facts</h3>
                <p style="font-size: 0.9em; color: #a4b0be;">
                    В фоне работает вторая LLM, которая вытаскивает из ваших слов факты и закрепляет их в JSON.
                </p>
                <b>Сохраненные факты:</b>
                <div id="factsBox" class="facts-list">{}</div>
            </div>
            
            <!-- Инфо для Branching -->
            <div id="info-branch" class="info-block">
                <h3>🌳 Branching (Ветки)</h3>
                <p style="font-size: 0.9em; color: #a4b0be;">
                    Создавайте альтернативные ветки диалога. Идеально для ТЗ: в одной ветке делаем сайт на Python, в другой — на Node.js.
                </p>
                <div style="display: flex; gap: 5px; margin-bottom: 15px;">
                    <input type="text" id="newBranchName" placeholder="Имя новой ветки...">
                    <button onclick="createBranch()">Создать</button>
                </div>
                <b>Активные ветки:</b>
                <div id="branchList" class="branch-list"></div>
            </div>
            
            <div style="margin-top: 20px; font-size: 0.8em; color: #747d8c; border-top: 1px solid var(--border); padding-top: 15px;">
                <b>Выводы для видео:</b><br>
                1. <i>Window</i> - дешево, но теряет факты.<br>
                2. <i>Facts</i> - железобетонная память на имена и детали, но требует x2 запросов к API.<br>
                3. <i>Branching</i> - спасение для A/B тестов при написании ТЗ или кода.
            </div>
        </div>
    </div>

    <script>
        let currentStrategy = "window";

        window.onload = async function() {
            await loadState();
        };

        async function loadState() {
            const resp = await fetch('/get_state');
            const state = await resp.json();
            
            currentStrategy = state.strategy;
            updateTabs();
            
            // Отрисовка чата
            const hist = document.getElementById('chatHistory');
            hist.innerHTML = '';
            
            let messagesToDraw = [];
            if (currentStrategy === 'window' || currentStrategy === 'facts') {
                messagesToDraw = state.messages;
            } else if (currentStrategy === 'branch') {
                messagesToDraw = state.branches[state.active_branch] || [];
            }
            
            messagesToDraw.forEach(m => addMessage(m.content, m.role === 'user'));
            
            // Отрисовка панелей
            if(currentStrategy === 'facts') {
                document.getElementById('factsBox').innerText = JSON.stringify(state.facts, null, 2);
            }
            
            if(currentStrategy === 'branch') {
                const bList = document.getElementById('branchList');
                bList.innerHTML = '';
                Object.keys(state.branches).forEach(b => {
                    const btn = document.createElement('button');
                    btn.className = `branch-btn ${b === state.active_branch ? 'active' : ''}`;
                    btn.innerText = b;
                    btn.onclick = () => switchBranch(b);
                    bList.appendChild(btn);
                });
            }
        }

        async function changeStrategy(strat) {
            await fetch('/set_strategy', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({strategy: strat})
            });
            await loadState();
        }
        
        function updateTabs() {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`.tab[data-strat="${currentStrategy}"]`).classList.add('active');
            
            document.querySelectorAll('.info-block').forEach(b => b.classList.remove('active'));
            document.getElementById(`info-${currentStrategy}`).classList.add('active');
        }

        function addMessage(text, isUser) {
            const history = document.getElementById('chatHistory');
            const msgDiv = document.createElement('div');
            msgDiv.className = `msg ${isUser ? 'msg-user' : 'msg-agent'}`;
            msgDiv.innerText = text;
            history.appendChild(msgDiv);
            history.scrollTop = history.scrollHeight;
            return msgDiv;
        }

        async function sendMsg() {
            const apiKey = document.getElementById('apiKey').value;
            const inputEl = document.getElementById('userInput');
            const text = inputEl.value.trim();

            if (!text) return;
            if (!apiKey) { alert("API Key!"); return; }

            addMessage(text, true);
            inputEl.value = '';

            const loading = addMessage("Обработка...", false);
            loading.style.opacity = 0.5;

            try {
                const resp = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({apiKey, message: text})
                });
                const data = await resp.json();
                
                loading.remove();
                
                if(data.error) addMessage(data.error, false);
                else {
                    addMessage(data.reply, false);
                    document.getElementById('statTokens').innerText = `Токенов в запросе: ~${data.stats.context_tokens}`;
                    await loadState(); // Перерисовываем факты/ветки
                }
            } catch(e) {
                loading.remove();
                addMessage("Ошибка сети", false);
            }
        }
        
        async function createBranch() {
            const name = document.getElementById('newBranchName').value.trim();
            if(!name) return;
            
            // Создаем ветку и копируем в неё текущую историю!
            await fetch('/branch/create', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({name: name})
            });
            document.getElementById('newBranchName').value = '';
            await loadState();
        }
        
        async function switchBranch(name) {
            await fetch('/branch/switch', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({name: name})
            });
            await loadState();
        }

        async function clearMem() {
            await fetch('/clear', {method:'POST'});
            await loadState();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_state', methods=['GET'])
def get_state():
    return jsonify(agent.state)

@app.route('/set_strategy', methods=['POST'])
def set_strategy():
    strat = request.json.get('strategy')
    if strat in ['window', 'facts', 'branch']:
        agent.set_strategy(strat)
    return jsonify({"status": "ok"})

@app.route('/branch/create', methods=['POST'])
def create_branch():
    name = request.json.get('name')
    # Копируем всю историю текущей ветки в новую
    current_b = agent.state["active_branch"]
    hist_len = len(agent.state["branches"].get(current_b, []))
    agent.create_branch(name, from_index=hist_len-1 if hist_len > 0 else None)
    return jsonify({"status": "ok"})

@app.route('/branch/switch', methods=['POST'])
def switch_branch():
    agent.switch_branch(request.json.get('name'))
    return jsonify({"status": "ok"})

@app.route('/clear', methods=['POST'])
def clear_memory():
    agent.clear_memory()
    return jsonify({"status": "ok"})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    agent.api_key = data.get('apiKey')
    user_message = data.get('message')

    if not agent.api_key:
        return jsonify({"error": "API Key is missing."}), 400

    result = agent.process_request(user_message)
    return jsonify(result)

if __name__ == '__main__':
    print(f">>> СТРАТЕГИИ КОНТЕКСТА (ДЕНЬ 10) ЗАПУЩЕНЫ НА ПОРТУ 5000 <<<")
    app.run(host='0.0.0.0', port=5000, debug=True)
