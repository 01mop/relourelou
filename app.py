"""
╔══════════════════════════════════════════════════════════════════════╗
║   QUANTUM BOT  v1.0  —  Trading Bot Interface                        ║
║   Strategies · Backtesting · Live Trading · IB · Binance · ML       ║
╚══════════════════════════════════════════════════════════════════════╝
Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_OK = True
except ModuleNotFoundError:
    PLOTLY_OK = False
from datetime import datetime, timedelta
import time, json, threading, queue
from pathlib import Path

st.set_page_config(
    page_title="QUANTUM BOT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Plotly check ──────────────────────────────────────────────────────
if not PLOTLY_OK:
    st.error("❌ Plotly n'est pas installé. Ajoute 'plotly' dans ton fichier requirements.txt puis redémarre l'application.")
    st.stop()

# ── CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;600&family=Orbitron:wght@700;900&display=swap');
html,body,[class*="css"]{background:#070b10!important;color:#c8d8e8!important;font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#070b10;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1520,#080f18)!important;border-right:1px solid #1a2f45;}
section[data-testid="stSidebar"] *{color:#7aafc8!important;}
section[data-testid="stSidebar"] label{color:#4da8da!important;font-family:'Space Mono',monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;}
.stTextInput>div>div input,.stSelectbox>div>div,.stMultiSelect>div>div,.stNumberInput>div>div input{background:#0d1e2e!important;border:1px solid #1e3a55!important;border-radius:2px!important;color:#4da8da!important;font-family:'Space Mono',monospace!important;}
.stTabs [data-baseweb="tab-list"]{background:#0a1520;border-bottom:1px solid #1a3a55;gap:0;}
.stTabs [data-baseweb="tab"]{color:#4a7a99;font-family:'Space Mono',monospace;font-size:10px;letter-spacing:1px;padding:10px 16px;border-bottom:2px solid transparent;}
.stTabs [aria-selected="true"]{color:#00d4ff!important;border-bottom:2px solid #00d4ff!important;background:transparent!important;}
[data-testid="metric-container"]{background:linear-gradient(135deg,#0d1f30,#0a1520);border:1px solid #1a3a55;border-left:3px solid #00d4ff;border-radius:2px;padding:10px 14px;}
[data-testid="metric-container"] label{color:#4da8da!important;font-family:'Space Mono',monospace;font-size:9px;letter-spacing:1.5px;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#e8f4fd!important;font-family:'Space Mono',monospace;font-size:16px;}
.blabel{font-family:'Space Mono',monospace;font-size:9px;letter-spacing:2px;color:#2a6a8a;text-transform:uppercase;border-bottom:1px solid #1a3a55;padding-bottom:4px;margin-bottom:10px;}
.bot-card{background:#0d1f30;border:1px solid #1a3a55;border-radius:4px;padding:14px;margin-bottom:10px;}
.bot-running{border-left:4px solid #00ff88;}
.bot-stopped{border-left:4px solid #ff4466;}
.bot-paused{border-left:4px solid #ffaa00;}
.log-box{background:#050810;border:1px solid #1a3a55;border-radius:2px;padding:10px;font-family:'Space Mono',monospace;font-size:10px;height:220px;overflow-y:auto;line-height:1.8;}
.log-buy{color:#00ff88;} .log-sell{color:#ff4466;} .log-info{color:#4da8da;} .log-warn{color:#ffaa00;} .log-err{color:#ff4466;font-weight:bold;}
.status-dot-green{display:inline-block;width:8px;height:8px;border-radius:50%;background:#00ff88;box-shadow:0 0 8px #00ff88;animation:pulse 1.5s infinite;margin-right:6px;}
.status-dot-red{display:inline-block;width:8px;height:8px;border-radius:50%;background:#ff4466;margin-right:6px;}
.status-dot-yellow{display:inline-block;width:8px;height:8px;border-radius:50%;background:#ffaa00;animation:pulse 2s infinite;margin-right:6px;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
hr{border-color:#1a3a55!important;}
::-webkit-scrollbar{width:3px;}::-webkit-scrollbar-thumb{background:#1e3a55;}
.tag-live{background:#0d2a1a;border:1px solid #00ff88;color:#00ff88;font-family:'Space Mono',monospace;font-size:9px;padding:2px 7px;border-radius:2px;display:inline-block;margin:2px;}
.tag-paper{background:#1a1a0d;border:1px solid #ffaa00;color:#ffaa00;font-family:'Space Mono',monospace;font-size:9px;padding:2px 7px;border-radius:2px;display:inline-block;margin:2px;}
.tag-off{background:#2a0d0d;border:1px solid #ff4466;color:#ff4466;font-family:'Space Mono',monospace;font-size:9px;padding:2px 7px;border-radius:2px;display:inline-block;margin:2px;}
</style>
""", unsafe_allow_html=True)

# ── imports from modules ──────────────────────────────────────────────
IMPORT_ERRORS = []

try:
    from core.data_feed import DataFeed
except ModuleNotFoundError as e:
    IMPORT_ERRORS.append(f"DataFeed: {e}")
    class DataFeed:
        def __init__(self, *args, **kwargs):
            self.source = "demo"
        def get_data(self, *args, **kwargs):
            dates = pd.date_range(end=datetime.now(), periods=100, freq="h")
            base = np.linspace(100, 110, len(dates))
            noise = np.random.normal(0, 0.8, len(dates))
            close = base + noise.cumsum() * 0.2
            return pd.DataFrame({
                "Open":   close + np.random.normal(0, 0.3, len(dates)),
                "High":   close + np.abs(np.random.normal(0.6, 0.3, len(dates))),
                "Low":    close - np.abs(np.random.normal(0.6, 0.3, len(dates))),
                "Close":  close,
                "Volume": np.random.randint(100, 1000, len(dates)),
            }, index=dates)

try:
    from core.engine import BotEngine
except ModuleNotFoundError as e:
    IMPORT_ERRORS.append(f"BotEngine: {e}")
    class BotEngine:
        def __init__(self, name="Bot", strategy=None, broker=None, risk_manager=None, symbol="BTCUSDT", timeframe="1h", *args, **kwargs):
            self.name = name
            self.strategy = strategy
            self.broker = broker
            self.risk_manager = risk_manager
            self.symbol = symbol
            self.timeframe = timeframe
            self.status = "stopped"
            self.started_at = None
            self.trades = []
            self.pnl = 0.0
        def start(self):
            self.status = "running"
            self.started_at = datetime.now()
        def stop(self):
            self.status = "stopped"
        def pause(self):
            self.status = "paused"
        def resume(self):
            self.status = "running"

try:
    from core.risk import RiskManager
except ModuleNotFoundError as e:
    IMPORT_ERRORS.append(f"RiskManager: {e}")
    class RiskManager:
        def __init__(self, max_drawdown=10, max_daily_loss=500, max_positions=5, *args, **kwargs):
            self.max_drawdown = max_drawdown
            self.max_daily_loss = max_daily_loss
            self.max_positions = max_positions

try:
    from core.portfolio import Portfolio
except ModuleNotFoundError as e:
    IMPORT_ERRORS.append(f"Portfolio: {e}")
    class Portfolio:
        def __init__(self, *args, **kwargs):
            self.balance = 10000.0
            self.equity = 10000.0
            self.positions = []
            self.trade_history = []
        def summary(self):
            return {
                "balance": self.balance,
                "equity": self.equity,
                "positions": len(self.positions),
                "trades": len(self.trade_history),
            }

class _BaseStrategy:
    def __init__(self, *args, **kwargs):
        self.params = kwargs
    def generate_signal(self, data=None):
        return "HOLD"

try:
    from strategies.classic import SMACrossover, RSIMeanReversion, MACDStrategy, BollingerBands
except ModuleNotFoundError as e:
    IMPORT_ERRORS.append(f"strategies.classic: {e}")
    class SMACrossover(_BaseStrategy): pass
    class RSIMeanReversion(_BaseStrategy): pass
    class MACDStrategy(_BaseStrategy): pass
    class BollingerBands(_BaseStrategy): pass

try:
    from strategies.ml_strat import MLStrategy, ReinforcementStrategy
except ModuleNotFoundError as e:
    IMPORT_ERRORS.append(f"strategies.ml_strat: {e}")
    class MLStrategy(_BaseStrategy): pass
    class ReinforcementStrategy(_BaseStrategy): pass

try:
    from brokers.ib_broker import IBBroker
except ModuleNotFoundError as e:
    IMPORT_ERRORS.append(f"IBBroker: {e}")
    class IBBroker:
        def __init__(self, host="127.0.0.1", port=7497, client_id=1, *args, **kwargs):
            self.host = host; self.port = port; self.client_id = client_id; self.connected = False
        def connect(self): return False

try:
    from brokers.binance_broker import BinanceBroker
except ModuleNotFoundError as e:
    IMPORT_ERRORS.append(f"BinanceBroker: {e}")
    class BinanceBroker:
        def __init__(self, api_key="", api_secret="", testnet=True, *args, **kwargs):
            self.api_key = api_key; self.api_secret = api_secret; self.testnet = testnet; self.connected = False
        def connect(self): return False

try:
    from brokers.paper_broker import PaperBroker
except ModuleNotFoundError as e:
    IMPORT_ERRORS.append(f"PaperBroker: {e}")
    class PaperBroker:
        def __init__(self, *args, **kwargs): self.connected = True
        def connect(self): return True

# ── session state init ────────────────────────────────────────────────
def init_state():
    defaults = {
        "bots": {},
        "logs": {},
        "portfolio": Portfolio(),
        "active_bot": None,
        "broker_status": {"IB": False, "Binance": False, "Paper": True},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

if IMPORT_ERRORS:
    st.warning("⚠️ Mode dégradé : certains modules locaux sont introuvables. L'interface fonctionne avec des objets de démonstration.")
    with st.expander("Détails des modules manquants"):
        for err in IMPORT_ERRORS:
            st.code(err)

PLOTLY_BASE = dict(
    paper_bgcolor="#070b10",
    plot_bgcolor="#070b10",
    font=dict(family="Space Mono, monospace", color="#8aafc8", size=10),
    xaxis=dict(gridcolor="#0d1e2e", zerolinecolor="#0d1e2e"),
    yaxis=dict(gridcolor="#0d1e2e", zerolinecolor="#0d1e2e"),
    margin=dict(l=50, r=20, t=36, b=36),
    legend=dict(bgcolor="#0a1520", bordercolor="#1a3a55", borderwidth=1),
)
COLORS = ["#00d4ff", "#00ff88", "#ffaa00", "#ff4466", "#aa88ff", "#ff88aa", "#44ffdd"]

def blabel(txt):
    st.markdown(f"<div class='blabel'>▸ {txt}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px'>
      <div style='font-family:Orbitron,sans-serif;font-size:16px;font-weight:900;
                  letter-spacing:4px;color:#00d4ff;text-shadow:0 0 12px rgba(0,212,255,.4);'>
        🤖 QUANTUM BOT
      </div>
      <div style='font-family:Space Mono,monospace;font-size:8px;letter-spacing:2px;
                  color:#2a5a7a;margin-top:2px;'>TRADING ENGINE v1.0</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    blabel("Broker connections")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("IB", use_container_width=True):
            st.session_state["broker_status"]["IB"] = not st.session_state["broker_status"]["IB"]
    with c2:
        if st.button("BINANCE", use_container_width=True):
            st.session_state["broker_status"]["Binance"] = not st.session_state["broker_status"]["Binance"]
    with c3:
        st.button("PAPER", use_container_width=True, disabled=True)

    st.markdown(
        f"""
        <div style='margin-top:8px'>
          <span class='{"tag-live" if st.session_state["broker_status"]["IB"] else "tag-off"}'>IB</span>
          <span class='{"tag-live" if st.session_state["broker_status"]["Binance"] else "tag-off"}'>BINANCE</span>
          <span class='tag-paper'>PAPER</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    blabel("Create bot")

    bot_name = st.text_input("Bot Name", value=f"BOT-{len(st.session_state['bots'])+1:03d}")
    symbol = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT", "AAPL", "TSLA", "EURUSD"])
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3)
    strategy_name = st.selectbox(
        "Strategy",
        ["SMA Crossover", "RSI Mean Reversion", "MACD", "Bollinger Bands", "ML Strategy", "RL Strategy"]
    )

    if st.button("➕ Create bot", use_container_width=True):
        strategy_map = {
            "SMA Crossover": SMACrossover(),
            "RSI Mean Reversion": RSIMeanReversion(),
            "MACD": MACDStrategy(),
            "Bollinger Bands": BollingerBands(),
            "ML Strategy": MLStrategy(),
            "RL Strategy": ReinforcementStrategy(),
        }
        bot = BotEngine(
            name=bot_name,
            strategy=strategy_map[strategy_name],
            broker=PaperBroker(),
            risk_manager=RiskManager(),
            symbol=symbol,
            timeframe=timeframe,
        )
        bot_id = f"bot_{len(st.session_state['bots'])+1}"
        st.session_state["bots"][bot_id] = bot
        st.session_state["logs"][bot_id] = [f"[INFO] {datetime.now().strftime('%H:%M:%S')} - Bot créé"]
        st.session_state["active_bot"] = bot_id
        st.success(f"✅ Bot {bot_name} créé")

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════
def add_log(bot_id, level, message):
    if bot_id not in st.session_state["logs"]:
        st.session_state["logs"][bot_id] = []
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state["logs"][bot_id].append(f"[{level}] {ts} - {message}")
    st.session_state["logs"][bot_id] = st.session_state["logs"][bot_id][-200:]

def gen_demo_equity():
    x = pd.date_range(end=datetime.now(), periods=120, freq="h")
    y = np.cumsum(np.random.normal(0, 30, len(x))) + 10000
    return pd.DataFrame({"time": x, "equity": y})

def gen_demo_candles():
    return DataFeed().get_data()

def render_bot_card(bot_id, bot):
    status_class = {"running": "bot-running", "stopped": "bot-stopped", "paused": "bot-paused"}.get(getattr(bot, "status", "stopped"), "bot-stopped")
    status_dot   = {"running": "status-dot-green", "stopped": "status-dot-red", "paused": "status-dot-yellow"}.get(getattr(bot, "status", "stopped"), "status-dot-red")
    st.markdown(f"""
        <div class='bot-card {status_class}'>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-family:Space Mono,monospace;font-size:14px;color:#e8f4fd;">{bot.name}</div>
                    <div style="font-size:11px;color:#6f9bb6;">{getattr(bot,'symbol','N/A')} · {getattr(bot,'timeframe','N/A')}</div>
                </div>
                <div style="font-size:11px;color:#9dc7df;">
                    <span class="{status_dot}"></span>{getattr(bot,'status','stopped').upper()}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════════════
st.title("QUANTUM BOT Control Center")

tab1, tab2, tab3, tab4 = st.tabs(["🤖 Bots", "📈 Market", "💼 Portfolio", "📋 Logs"])

with tab1:
    blabel("Active bots")
    if not st.session_state["bots"]:
        st.info("Aucun bot créé. Utilise le panneau gauche pour en créer un.")
    else:
        cols = st.columns(2)
        for i, (bot_id, bot) in enumerate(st.session_state["bots"].items()):
            with cols[i % 2]:
                render_bot_card(bot_id, bot)
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    if st.button("▶ Start",  key=f"start_{bot_id}",  use_container_width=True):
                        bot.start();  add_log(bot_id, "INFO", f"{bot.name} started")
                with c2:
                    if st.button("⏸ Pause",  key=f"pause_{bot_id}",  use_container_width=True):
                        bot.pause();  add_log(bot_id, "WARN", f"{bot.name} paused")
                with c3:
                    if st.button("▶▶ Resume", key=f"resume_{bot_id}", use_container_width=True):
                        bot.resume(); add_log(bot_id, "INFO", f"{bot.name} resumed")
                with c4:
                    if st.button("⏹ Stop",   key=f"stop_{bot_id}",   use_container_width=True):
                        bot.stop();   add_log(bot_id, "ERR",  f"{bot.name} stopped")

with tab2:
    blabel("Market data")
    candles = gen_demo_candles()
    fig = go.Figure(data=[go.Candlestick(
        x=candles.index,
        open=candles["Open"], high=candles["High"],
        low=candles["Low"],   close=candles["Close"],
        increasing_line_color="#00ff88",
        decreasing_line_color="#ff4466",
    )])
    fig.update_layout(**PLOTLY_BASE, height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    blabel("Portfolio")
    portfolio = st.session_state["portfolio"]
    summary = portfolio.summary() if hasattr(portfolio, "summary") else {
        "balance": 10000, "equity": 10000, "positions": 0, "trades": 0
    }
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Balance",   f"${summary['balance']:,.2f}")
    c2.metric("Equity",    f"${summary['equity']:,.2f}")
    c3.metric("Positions", summary["positions"])
    c4.metric("Trades",    summary["trades"])

    equity = gen_demo_equity()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=equity["time"], y=equity["equity"],
        mode="lines", line=dict(color="#00d4ff", width=2), name="Equity"
    ))
    fig2.update_layout(**PLOTLY_BASE, height=350)
    st.plotly_chart(fig2, use_container_width=True)

with tab4:
    blabel("System logs")
    active_bot = st.session_state.get("active_bot")
    logs = st.session_state["logs"].get(active_bot, ["[INFO] Aucun log pour le moment"]) if active_bot else ["[INFO] Aucun log pour le moment"]
    rendered = []
    for line in logs[-100:]:
        css = "log-buy" if "[BUY]" in line else "log-sell" if "[SELL]" in line else "log-warn" if "[WARN]" in line else "log-err" if "[ERR]" in line else "log-info"
        rendered.append(f"<div class='{css}'>{line}</div>")
    st.markdown(f"<div class='log-box'>{''.join(rendered)}</div>", unsafe_allow_html=True)
