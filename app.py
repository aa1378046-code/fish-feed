import uvicorn
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import uuid
import random
import string
from contextlib import contextmanager

# ---------- База данных ----------
Base = declarative_base()


class QRCode(Base):
    __tablename__ = "qr_codes"
    id = Column(Integer, primary_key=True)
    code = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default="active")
    scanned_at = Column(DateTime, nullable=True)
    tokens_value = Column(Integer, default=10)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    qr_code_id = Column(Integer, ForeignKey("qr_codes.id"))
    user_session = Column(String(255))
    tokens_awarded = Column(Integer)
    scanned_at = Column(DateTime, default=datetime.utcnow)


class UserToken(Base):
    __tablename__ = "user_tokens"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True)
    total_tokens = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)


engine = create_engine('sqlite:///fish_feed.db', connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- FastAPI ----------
app = FastAPI(title="Fish Feed Tokens")


# ---------- Генератор кодов ----------
def generate_unique_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


# ========== ГЛАВНАЯ СТРАНИЦА ==========
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    with get_db() as db:
        user_tokens = db.query(UserToken).filter_by(session_id=session_id).first()
        if not user_tokens:
            user_tokens = UserToken(session_id=session_id, total_tokens=0)
            db.add(user_tokens)
            db.commit()
        tokens = user_tokens.total_tokens

    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes, viewport-fit=cover">
    <title>Fish Feed — расти рыбу за токены</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: linear-gradient(160deg, #d4f1f9 0%, #a0d8ef 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            padding: 12px;
        }}
        .lake-card {{
            max-width: 500px;
            width: 100%;
            background: rgba(255,255,255,0.3);
            backdrop-filter: blur(2px);
            border-radius: 48px 48px 36px 36px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 16px 16px 32px;
        }}
        .lake {{
            background: radial-gradient(circle at 30% 40%, #3b9ec7, #1e6f96);
            border-radius: 80px 80px 60px 60px;
            min-height: 280px;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }}
        .lake::before {{
            content: "";
            position: absolute;
            bottom: 0;
            width: 100%;
            height: 40px;
            background: repeating-linear-gradient(transparent 0px, transparent 18px, rgba(255,255,240,0.2) 18px, rgba(255,255,240,0.3) 28px);
        }}
        .fish {{
            transition: all 0.3s cubic-bezier(0.34, 1.2, 0.64, 1);
            filter: drop-shadow(0 8px 12px rgba(0,0,0,0.2));
        }}
        .balance-panel {{
            background: white;
            border-radius: 60px;
            padding: 12px 20px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .balance-label {{
            font-size: 13px;
            letter-spacing: 1px;
            color: #2c7a47;
            font-weight: 600;
        }}
        .token-count {{
            font-size: 44px;
            font-weight: 800;
            color: #f5b042;
            line-height: 1;
        }}
        .next-reward {{
            background: rgba(255,255,245,0.95);
            border-radius: 32px;
            padding: 14px;
            margin-bottom: 20px;
        }}
        .progress-bar-bg {{
            background: #e0e7e3;
            border-radius: 40px;
            height: 10px;
            margin: 10px 0 6px;
            overflow: hidden;
        }}
        .progress-fill {{
            background: #ffb347;
            width: 0%;
            height: 100%;
            border-radius: 40px;
            transition: width 0.3s;
        }}
        .actions {{
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 8px;
        }}
        .btn {{
            flex: 1;
            min-width: 140px;
            text-align: center;
            padding: 14px 0;
            border-radius: 60px;
            font-weight: 600;
            text-decoration: none;
            font-size: 16px;
            background: white;
            color: #1f6e43;
            cursor: pointer;
            border: none;
        }}
        .btn-primary {{
            background: #2c7a47;
            color: white;
            border: none;
            box-shadow: 0 4px 0 #1b5230;
        }}
        .btn-primary:active {{
            transform: translateY(2px);
            box-shadow: 0 1px 0 #1b5230;
        }}
        .milestones {{
            margin-top: 20px;
            background: rgba(255,255,250,0.85);
            border-radius: 32px;
            padding: 12px 16px;
        }}
        .milestone-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid rgba(0,0,0,0.05);
            font-size: 14px;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .milestone-tokens {{
            font-weight: 700;
            color: #f5a623;
        }}
        .input-group {{
            margin-top: 16px;
            display: flex;
            gap: 10px;
        }}
        .code-input {{
            flex: 2;
            padding: 14px;
            border-radius: 60px;
            border: none;
            font-size: 16px;
            text-align: center;
            font-family: monospace;
            letter-spacing: 2px;
        }}
        @media (max-width: 480px) {{
            .lake {{ min-height: 220px; }}
            .token-count {{ font-size: 36px; }}
            .btn {{ padding: 12px 0; font-size: 14px; min-width: 120px; }}
        }}
    </style>
</head>
<body>
<div class="lake-card">
    <div class="lake"><div class="fish" id="fishEmoji" style="font-size:30px;">🐟</div></div>
    <div class="balance-panel">
        <div class="balance-label">ТВОИ ТОКЕНЫ</div>
        <div class="token-count"><span id="tokenValue">{tokens}</span> 🪙</div>
    </div>
    <div class="next-reward" id="nextRewardBox">
        <div style="font-size:13px; font-weight:600;">🎁 ДО СЛЕДУЮЩЕЙ НАГРАДЫ</div>
        <div id="nextPrizeName" style="font-weight:700; margin:6px 0;">—</div>
        <div class="progress-bar-bg"><div class="progress-fill" id="progressFill"></div></div>
        <div style="display: flex; justify-content: space-between; font-size: 12px;">
            <span id="currentTokensLabel">{tokens}</span>
            <span id="targetTokensLabel">0</span>
        </div>
    </div>

    <div class="actions">
        <button onclick="showCodeInput()" class="btn btn-primary">🔑 Ввести код</button>
        <a href="/shop" class="btn">🛒 Магазин</a>
    </div>

    <div id="codeInputArea" style="display: none; margin-top: 16px;">
        <div class="input-group">
            <input type="text" id="codeInput" class="code-input" placeholder="例如: ABC123DEF456" maxlength="12">
            <button onclick="submitCode()" class="btn" style="flex:1; background:#2c7a47; color:white; box-shadow:none;">Активировать</button>
        </div>
        <div style="font-size:12px; text-align:center; margin-top:8px; color:#555;">Введите 12-значный код с пачки корма</div>
    </div>

    <div class="milestones">
        <div style="font-size:13px; font-weight:600; margin-bottom:8px;">🐟 Рост рыбы:</div>
        <div class="milestone-item"><span>🐟 малёк</span><span class="milestone-tokens">0 🪙</span></div>
        <div class="milestone-item"><span>🐠 средняя</span><span class="milestone-tokens">100 🪙</span></div>
        <div class="milestone-item"><span>🐡 крупная</span><span class="milestone-tokens">250 🪙</span></div>
        <div class="milestone-item"><span>🐋 гигант</span><span class="milestone-tokens">500 🪙</span></div>
        <div class="milestone-item"><span>🏆 легенда</span><span class="milestone-tokens">750 🪙</span></div>
        <div class="milestone-item"><span>👑 золотая</span><span class="milestone-tokens">1000 🪙</span></div>
    </div>
</div>

<script>
    const rewardLevels = [
        {{ '{{' }} tokens: 0, prize: "Начинай копить!", size: 30, fishIcon: "🐟" }},
        {{ '{{' }} tokens: 100, prize: "Маленькая пачка корма", size: 50, fishIcon: "🐠" }},
        {{ '{{' }} tokens: 250, prize: "Средняя пачка корма", size: 72, fishIcon: "🐡" }},
        {{ '{{' }} tokens: 500, prize: "Большая пачка корма", size: 100, fishIcon: "🐋" }},
        {{ '{{' }} tokens: 750, prize: "Удочка", size: 130, fishIcon: "🏆" }},
        {{ '{{' }} tokens: 1000, prize: "Золотая рыбка", size: 160, fishIcon: "👑🐟" }}
    ];
    let currentTokens = {tokens};

    function showCodeInput() {{
        const area = document.getElementById('codeInputArea');
        area.style.display = area.style.display === 'none' ? 'block' : 'none';
    }}

    async function submitCode() {{
        const code = document.getElementById('codeInput').value.trim().toUpperCase();
        if (!code) {{
            alert('Введите код с пачки корма');
            return;
        }}

        document.getElementById('codeInputArea').style.display = 'none';
        const resultDiv = document.getElementById('nextRewardBox');
        const originalHTML = resultDiv.innerHTML;
        resultDiv.innerHTML = '<div style="text-align:center;">⏳ Проверка кода...</div>';

        try {{
            const res = await fetch('/api/scan', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ data: code }})
            }});
            const data = await res.json();
            if (data.success) {{
                resultDiv.innerHTML = '<div style="text-align:center; color:green;">✅ ' + data.message + '</div>';
                currentTokens = data.tokens;
                document.getElementById('tokenValue').innerText = currentTokens;
                updateLakeAndProgress();
                setTimeout(() => window.location.reload(), 2000);
            }} else {{
                resultDiv.innerHTML = '<div style="text-align:center; color:red;">❌ ' + data.message + '</div>';
                setTimeout(() => {{ resultDiv.innerHTML = originalHTML; }}, 2000);
            }}
        }} catch(err) {{
            resultDiv.innerHTML = '<div style="text-align:center; color:red;">❌ Ошибка сервера</div>';
            setTimeout(() => {{ resultDiv.innerHTML = originalHTML; }}, 2000);
        }}
        document.getElementById('codeInput').value = '';
    }}

    function updateLakeAndProgress() {{
        let currentLevel = rewardLevels[0];
        let nextLevel = rewardLevels[1];
        for (let i = rewardLevels.length-1; i >= 0; i--) {{
            if (currentTokens >= rewardLevels[i].tokens) {{
                currentLevel = rewardLevels[i];
                nextLevel = rewardLevels[i+1] || null;
                break;
            }}
        }}
        const fish = document.getElementById('fishEmoji');
        fish.style.fontSize = currentLevel.size + 'px';
        fish.innerHTML = currentLevel.fishIcon;
        const nextPrizeDiv = document.getElementById('nextPrizeName');
        const targetSpan = document.getElementById('targetTokensLabel');
        const progressFill = document.getElementById('progressFill');
        if (nextLevel) {{
            nextPrizeDiv.innerHTML = nextLevel.prize + ` (${{nextLevel.tokens}} 🪙)`;
            targetSpan.innerText = nextLevel.tokens;
            let prev = currentLevel.tokens;
            let range = nextLevel.tokens - prev;
            let progress = currentTokens - prev;
            let percent = Math.min(100, Math.max(0, (progress/range)*100));
            progressFill.style.width = percent + '%';
        }} else {{
            nextPrizeDiv.innerHTML = "🥳 ВСЕ ПРИЗЫ ПОЛУЧЕНЫ!";
            progressFill.style.width = '100%';
        }}
        document.getElementById('currentTokensLabel').innerText = currentTokens;
    }}

    async function refreshBalance() {{
        try {{
            const res = await fetch('/api/balance');
            const data = await res.json();
            if (data.tokens !== undefined && data.tokens !== currentTokens) {{
                currentTokens = data.tokens;
                document.getElementById('tokenValue').innerText = currentTokens;
                updateLakeAndProgress();
            }}
        }} catch(e) {{}}
    }}

    updateLakeAndProgress();
    setInterval(refreshBalance, 3000);

    document.getElementById('codeInput').addEventListener('keypress', function(e) {{
        if (e.key === 'Enter') submitCode();
    }});
</script>
</body>
</html>
    """
    response = HTMLResponse(html_content)
    response.set_cookie(key="session_id", value=session_id)
    return response


# ========== API БАЛАНСА ==========
@app.get("/api/balance")
async def get_balance(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"tokens": 0}
    with get_db() as db:
        user_tokens = db.query(UserToken).filter_by(session_id=session_id).first()
        tokens = user_tokens.total_tokens if user_tokens else 0
    return {"tokens": tokens}


# ========== API АКТИВАЦИИ КОДА ==========
@app.post("/api/scan")
async def scan_qr(qr_data: dict, request: Request):
    code = qr_data.get("data")
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"success": False, "message": "Сессия не найдена"}
    with get_db() as db:
        qr_record = db.query(QRCode).filter_by(code=code).first()
        if not qr_record:
            return {"success": False, "message": "❌ Неверный код"}
        if qr_record.status == "used":
            return {"success": False, "message": "⚠️ Этот код уже был активирован"}
        existing = db.query(Transaction).filter_by(qr_code_id=qr_record.id, user_session=session_id).first()
        if existing:
            return {"success": False, "message": "⚠️ Вы уже активировали этот код"}
        tokens = qr_record.tokens_value
        qr_record.status = "used"
        qr_record.scanned_at = datetime.now()
        transaction = Transaction(qr_code_id=qr_record.id, user_session=session_id, tokens_awarded=tokens)
        db.add(transaction)
        user_tokens = db.query(UserToken).filter_by(session_id=session_id).first()
        if not user_tokens:
            user_tokens = UserToken(session_id=session_id, total_tokens=0)
            db.add(user_tokens)
        user_tokens.total_tokens += tokens
        user_tokens.last_updated = datetime.now()
        db.commit()
        return {"success": True, "message": f"✅ Вы получили {tokens} токенов!", "tokens": user_tokens.total_tokens}


# ========== МАГАЗИН ==========
@app.get("/shop", response_class=HTMLResponse)
async def shop(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/")
    with get_db() as db:
        user_tokens = db.query(UserToken).filter_by(session_id=session_id).first()
        tokens = user_tokens.total_tokens if user_tokens else 0
    products = [
        {"name": "🐟 Маленькая пачка корма", "tokens": 100},
        {"name": "🐠 Средняя пачка корма", "tokens": 250},
        {"name": "🐡 Большая пачка корма", "tokens": 500},
        {"name": "🎣 Удочка", "tokens": 750},
        {"name": "🏆 Золотая рыбка (приз)", "tokens": 1000}
    ]
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Магазин призов</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: linear-gradient(160deg, #d4f1f9, #a0d8ef);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .shop-container {{
            max-width: 500px;
            width: 100%;
            background: rgba(255,255,255,0.9);
            border-radius: 48px;
            padding: 24px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .balance {{
            background: #2c7a47;
            color: white;
            padding: 16px;
            border-radius: 60px;
            text-align: center;
            margin-bottom: 24px;
            font-weight: bold;
        }}
        .product {{
            background: white;
            border-radius: 24px;
            padding: 16px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        .product-name {{ font-size: 16px; font-weight: 500; }}
        .product-tokens {{ color: #f5a623; font-weight: bold; }}
        button {{
            background: #2c7a47;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        button:disabled {{ background: #ccc; cursor: not-allowed; }}
        .back-btn {{
            display: block;
            text-align: center;
            margin-top: 20px;
            color: #1f6e43;
            text-decoration: none;
        }}
    </style>
</head>
<body>
<div class="shop-container">
    <div class="balance">💰 Ваши токены: {tokens} 🪙</div>
    <h2 style="margin-bottom:16px;">🎁 Обмен на призы</h2>
"""
    for p in products:
        disabled = "disabled" if tokens < p["tokens"] else ""
        html += f"""
    <div class="product">
        <div><div class="product-name">{p['name']}</div><div class="product-tokens">{p['tokens']} токенов</div></div>
        <button onclick="exchange('{p['name']}', {p['tokens']})" {disabled}>Обменять</button>
    </div>
"""
    html += f"""
    <a href="/" class="back-btn">← На главную</a>
</div>
<script>
    function exchange(name, cost) {{
        if (confirm(`Обменять ${{name}} за ${{cost}} токенов?`)) {{
            alert("Скажите этот код продавцу: " + Math.random().toString(36).substr(2, 8).toUpperCase() + "\\n\\nПокажите Альбеку и получите приз!");
        }}
    }}
</script>
</body>
</html>
    """
    return HTMLResponse(html)


# ========== АДМИНКА ==========
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    password = request.query_params.get("password")
    if password != "albek123":
        return HTMLResponse("Доступ запрещён. Используйте ?password=albek123", status_code=403)
    with get_db() as db:
        qr_codes = db.query(QRCode).all()
        stats = {"total": len(qr_codes), "active": len([q for q in qr_codes if q.status == "active"]),
                 "used": len([q for q in qr_codes if q.status == "used"])}
    rows = "".join(
        f"<tr><td>{c.id}</td><td>{c.code}</td><td>{c.status}</td><td>{c.tokens_value}</td><td>{c.scanned_at or '—'}</td></tr>"
        for c in qr_codes)
    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Админка</title><style>
    body {{ font-family: monospace; padding: 20px; background: #f0f0f0; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #4CAF50; color: white; }}
    .stats {{ background: #e0e0e0; padding: 10px; margin-bottom: 20px; }}
    form {{ margin-bottom: 30px; }}
    input, button {{ padding: 8px; margin: 5px; }}
</style></head>
<body>
<h1>Админ панель Альбека</h1>
<div class="stats">Всего: {stats['total']} | Активных: {stats['active']} | Использованных: {stats['used']}</div>
<h2>Создать коды</h2>
<form method="post" action="/admin/generate">
    <input type="number" name="count" value="10" min="1"> штук
    <input type="number" name="tokens" value="10" min="1"> токенов
    <button type="submit">Сгенерировать</button>
</form>
<h2>Существующие коды (для печати на пачках)</h2>
<a href="/admin/codes/export">📥 Скачать CSV</a>
<table><tr><th>ID</th><th>Код (напечатайте на пачке)</th><th>Статус</th><th>Токены</th><th>Активирован</th></tr>{rows}</table>
</body>
</html>
    """
    return HTMLResponse(html)


@app.post("/admin/generate")
async def generate_qr_codes(count: int = Form(10), tokens: int = Form(10)):
    with get_db() as db:
        for _ in range(min(count, 100)):
            code = generate_unique_code()
            db.add(QRCode(code=code, status="active", tokens_value=tokens))
        db.commit()
    return RedirectResponse(url="/admin?password=albek123", status_code=303)


@app.get("/admin/codes/export")
async def export_codes():
    with get_db() as db:
        qr_codes = db.query(QRCode).all()
        output = "Код,Статус,Токены\n" + "\n".join(f"{c.code},{c.status},{c.tokens_value}" for c in qr_codes)
    return HTMLResponse(f"<pre>{output}</pre>")


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)