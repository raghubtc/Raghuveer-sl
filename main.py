import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import time
import threading
import websocket
import requests

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

TOKEN = os.environ.get('VIRTUAL_TOKEN', 'doyLiCZePc0QXfq')
APP_ID = '1089'

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

TOKEN = os.environ.get('VIRTUAL_TOKEN', 'doyLiCZePcOQXfq')
APP_ID = '1089'

ws = None
bot_running = False
trailing_stop_active = False
peak_balance = 9862.98
current_balance = 9862.98
total_trades = 0
win_trades = 0
session_pnl = 0
trade_history = []

def on_message(ws, message):
    global current_balance, peak_balance, total_trades, win_trades, session_pnl
    data = json.loads(message)
    
    if 'authorize' in data:
        if data['authorize'].get('is_virtual'):
            current_balance = float(data['authorize']['balance'])
            if current_balance > peak_balance:
                peak_balance = current_balance
            socketio.emit('balance_update', {
                'balance': current_balance,
                'peak': peak_balance,
                'pnl': session_pnl,
                'total': total_trades,
                'winrate': round((win_trades/total_trades*100) if total_trades > 0 else 0, 2)
            })
    
    if 'balance' in data:
        current_balance = float(data['balance']['balance'])
        if current_balance > peak_balance:
            peak_balance = current_balance
            socketio.emit('balance_update', {
                'balance': current_balance,
                'peak': peak_balance,
                'pnl': session_pnl,
                'total': total_trades,
                'winrate': round((win_trades/total_trades*100) if total_trades > 0 else 0, 2)
            })
    
    if 'buy' in data:
        total_trades += 1
        trade_history.append({
            'time': time.strftime('%H:%M:%S'),
            'type': data['buy']['contract_type'],
            'stake': data['buy']['buy_price'],
            'status': 'OPEN',
            'profit': 0
        })
        socketio.emit('trade_update', {'trades': trade_history[-10:]})
    
    if 'proposal_open_contract' in data:
        contract = data['proposal_open_contract']
        if contract['is_sold']:
            profit = float(contract['profit'])
            session_pnl += profit
            if profit > 0:
                win_trades += 1
            if trade_history:
                trade_history[-1]['status'] = 'WIN' if profit > 0 else 'LOSS'
                trade_history[-1]['profit'] = profit
            socketio.emit('trade_update', {'trades': trade_history[-10:]})
            socketio.emit('balance_update', {
                'balance': current_balance,
                'peak': peak_balance,
                'pnl': session_pnl,
                'total': total_trades,
                'winrate': round((win_trades/total_trades*100) if total_trades > 0 else 0, 2)
            })

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket Closed")
    time.sleep(5)
    connect_deriv()

def on_open(ws):
    print("Connected to Deriv")
    auth_data = {"authorize": TOKEN}
    ws.send(json.dumps(auth_data))
    time.sleep(1)
    subscribe_data = {"balance": 1, "subscribe": 1}
    ws.send(json.dumps(subscribe_data))

def connect_deriv():
    global ws
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    ws.run_forever()
# Global variables - upar add karo agar nahi hain
current_balance = 0.0
total_trades = 0
bot_running = False
trailing_stop_active = False

@app.route('/')
def index():
    @app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return {"status": "ok", "balance": current_balance}

@socketio.on('start_bot')
def start_bot(data):
    global bot_running, trailing_stop_active
    bot_running = True
    trailing_stop_active = data.get('trailing_stop', False)
    emit('bot_status', {'status': 'Running', 'trailing': trailing_stop_active})

@socketio.on('stop_bot')
def stop_bot():
    global bot_running
    bot_running = False
    emit('bot_status', {'status': 'Stopped'})
