"""
Remote control web server - lets parents control browser time limits from phone
"""
import threading
import socket
from flask import Flask, request, jsonify, render_template_string, make_response

PARENT_PASSWORD = "parent123"

_MOBILE_PAGE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>家長控制</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, sans-serif; background: #f0f4f8; color: #333; }
  .container { max-width: 480px; margin: 0 auto; padding: 16px; }
  h1 { text-align: center; font-size: 1.4rem; padding: 16px 0 8px; color: #1a56a0; }

  .card { background: white; border-radius: 12px; padding: 16px; margin-bottom: 14px;
          box-shadow: 0 2px 8px rgba(0,0,0,.08); }
  .card h2 { font-size: 1rem; color: #555; margin-bottom: 10px; }

  .balance { font-size: 2.5rem; font-weight: bold; text-align: center; color: #1a56a0; }
  .balance-unit { font-size: 1rem; color: #888; text-align: center; }

  .status-row { display: flex; justify-content: space-between; align-items: center;
                padding: 6px 0; font-size: 0.95rem; }
  .badge { padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
  .badge-on  { background: #d4f8e8; color: #1a7a3c; }
  .badge-off { background: #fde8e8; color: #9b1c1c; }

  input[type=password], input[type=number] {
    width: 100%; padding: 10px 12px; border: 1px solid #ccc; border-radius: 8px;
    font-size: 1rem; margin-top: 6px;
  }

  .btn { width: 100%; padding: 12px; border: none; border-radius: 10px; font-size: 1rem;
         font-weight: bold; cursor: pointer; margin-top: 10px; transition: opacity .15s; }
  .btn:active { opacity: .75; }
  .btn-blue   { background: #1a56a0; color: white; }
  .btn-green  { background: #1a7a3c; color: white; }
  .btn-red    { background: #c0392b; color: white; }
  .btn-yellow { background: #d97706; color: white; }

  .row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .msg { text-align: center; padding: 8px; border-radius: 8px; margin-top: 10px;
         font-size: 0.9rem; display: none; }
  .msg-ok  { background: #d4f8e8; color: #1a7a3c; }
  .msg-err { background: #fde8e8; color: #9b1c1c; }

  #lock-screen { position: fixed; inset: 0; background: #f0f4f8;
                 display: flex; flex-direction: column; align-items: center;
                 justify-content: center; padding: 24px; z-index: 100; }
  #lock-screen h2 { font-size: 1.3rem; margin-bottom: 16px; color: #1a56a0; }
  #lock-screen input { width: 100%; max-width: 300px; }
  #lock-screen .btn { max-width: 300px; }
</style>
</head>
<body>

<!-- Lock screen -->
<div id="lock-screen">
  <h2>🔒 家長驗證</h2>
  <input type="password" id="pin-input" placeholder="輸入家長密碼" autocomplete="current-password">
  <button class="btn btn-blue" onclick="unlock()" style="margin-top:12px">登入</button>
  <div id="lock-msg" class="msg msg-err" style="max-width:300px;margin-top:8px"></div>
</div>

<div class="container" id="main" style="display:none">
  <h1>🏠 家長控制</h1>

  <!-- Time balance -->
  <div class="card">
    <h2>⏱ 剩餘時間</h2>
    <div class="balance" id="balance">--</div>
    <div class="balance-unit">分鐘</div>
    <div class="status-row" style="margin-top:10px">
      <span>瀏覽器監控</span>
      <span class="badge" id="monitor-badge">--</span>
    </div>
    <div class="status-row">
      <span>瀏覽器目前</span>
      <span class="badge" id="browser-badge">--</span>
    </div>
    <div class="status-row">
      <span>本次已用</span>
      <span id="session-mins">-- 分鐘</span>
    </div>
    <button class="btn btn-blue" onclick="loadStatus()" style="margin-top:8px">🔄 重新整理</button>
  </div>

  <!-- Toggle monitoring -->
  <div class="card">
    <h2>📡 瀏覽器監控開關</h2>
    <div class="row-2">
      <button class="btn btn-green" onclick="setMonitor(true)">✅ 啟用監控</button>
      <button class="btn btn-yellow" onclick="setMonitor(false)">⏸ 停用監控</button>
    </div>
    <div id="monitor-msg" class="msg"></div>
  </div>

  <!-- Adjust time -->
  <div class="card">
    <h2>⏰ 調整時間（分鐘）</h2>
    <input type="number" id="time-delta" value="0" min="-999" max="999" placeholder="正數 = 加時間，負數 = 扣時間">
    <div class="row-2">
      <button class="btn btn-green" onclick="adjustTime()">確認調整</button>
      <button class="btn btn-red" onclick="resetTime()">歸零</button>
    </div>
    <div id="time-msg" class="msg"></div>
  </div>

  <!-- Force close -->
  <div class="card">
    <h2>🚫 強制關閉瀏覽器</h2>
    <button class="btn btn-red" onclick="closeBrowsers()">立即關閉所有瀏覽器</button>
    <div id="close-msg" class="msg"></div>
  </div>
</div>

<script>
let _pwd = '';

function unlock() {
  const pwd = document.getElementById('pin-input').value;
  fetch('/api/status').then(r => r.json()).then(() => {
    // test password with a harmless adjust of 0
    fetch('/api/adjust_time', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({password: pwd, minutes: 0})
    }).then(r => {
      if (r.status === 403) {
        showMsg('lock-msg', '密碼錯誤！', false);
      } else {
        _pwd = pwd;
        document.getElementById('lock-screen').style.display = 'none';
        document.getElementById('main').style.display = 'block';
        loadStatus();
        setInterval(loadStatus, 10000);
      }
    });
  });
}

document.getElementById('pin-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') unlock();
});

function loadStatus() {
  fetch('/api/status').then(r => r.json()).then(d => {
    document.getElementById('balance').textContent = d.balance;
    setbadge('monitor-badge', d.browser_monitoring ? '已啟用' : '已停用', d.browser_monitoring);
    setbadge('browser-badge', d.browser_running ? '使用中' : '未開啟', d.browser_running);
    document.getElementById('session-mins').textContent = d.browser_session_minutes + ' 分鐘';
  });
}

function setBadge(id, text, ok) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = 'badge ' + (ok ? 'badge-on' : 'badge-off');
}
// alias
function setbadge(id, text, ok) { setBadge(id, text, ok); }

function showMsg(id, text, ok) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = 'msg ' + (ok ? 'msg-ok' : 'msg-err');
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 3000);
}

function setMonitor(enabled) {
  fetch('/api/toggle_browser', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({password: _pwd, enabled: enabled})
  }).then(r => r.json()).then(d => {
    if (d.error) { showMsg('monitor-msg', d.error, false); return; }
    showMsg('monitor-msg', '瀏覽器監控已' + (d.browser_monitoring ? '啟用' : '停用'), true);
    loadStatus();
  });
}

function adjustTime() {
  const mins = parseInt(document.getElementById('time-delta').value || '0');
  fetch('/api/adjust_time', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({password: _pwd, minutes: mins})
  }).then(r => r.json()).then(d => {
    if (d.error) { showMsg('time-msg', d.error, false); return; }
    showMsg('time-msg', '調整完成！剩餘 ' + d.balance + ' 分鐘', true);
    loadStatus();
  });
}

function resetTime() {
  if (!confirm('確定要將時間歸零嗎？')) return;
  fetch('/api/reset_time', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({password: _pwd})
  }).then(r => r.json()).then(d => {
    if (d.error) { showMsg('time-msg', d.error, false); return; }
    showMsg('time-msg', '已歸零！', true);
    loadStatus();
  });
}

function closeBrowsers() {
  if (!confirm('確定要立即關閉所有瀏覽器嗎？')) return;
  fetch('/api/close_browsers', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({password: _pwd})
  }).then(r => r.json()).then(d => {
    if (d.error) { showMsg('close-msg', d.error, false); return; }
    showMsg('close-msg', '瀏覽器已關閉！', true);
    loadStatus();
  });
}
</script>
</body>
</html>
"""


class RemoteControlServer:
    """Lightweight Flask server for phone-based parent control."""

    def __init__(self, game_tracker, db, port: int = 5050):
        self.game_tracker = game_tracker
        self.db = db
        self.port = port
        self.app = Flask(__name__)
        self.app.logger.disabled = True
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self._add_cors()
        self._setup_routes()

    def _add_cors(self):
        """Allow local-network devices (Mac Mini, phone) to call the API."""
        app = self.app

        @app.after_request
        def add_cors_headers(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response

        @app.route('/api/<path:path>', methods=['OPTIONS'])
        def options_handler(path):
            return make_response('', 204)

    def _check_password(self, data: dict) -> bool:
        return data.get('password') == PARENT_PASSWORD

    def _setup_routes(self):
        app = self.app
        gt = self.game_tracker
        db = self.db

        @app.route('/')
        def index():
            return render_template_string(_MOBILE_PAGE)

        @app.route('/api/status')
        def status():
            ctrl = gt.controller
            return jsonify({
                'balance': gt.get_time_balance(),
                'browser_monitoring': ctrl.browser_monitoring_enabled,
                'browser_running': ctrl.is_browser_running,
                'browser_session_minutes': ctrl.get_browser_session_minutes(),
            })

        @app.route('/api/adjust_time', methods=['POST'])
        def adjust_time():
            data = request.get_json(force=True) or {}
            if not self._check_password(data):
                return jsonify({'error': '密碼錯誤'}), 403
            minutes = int(data.get('minutes', 0))
            if minutes > 0:
                gt.controller.add_time(minutes)
                db.add_game_time(minutes)
            elif minutes < 0:
                db.use_game_time(abs(minutes))
                gt.controller.time_balance = db.get_game_time_balance()
            return jsonify({'balance': gt.get_time_balance()})

        @app.route('/api/reset_time', methods=['POST'])
        def reset_time():
            data = request.get_json(force=True) or {}
            if not self._check_password(data):
                return jsonify({'error': '密碼錯誤'}), 403
            balance = gt.get_time_balance()
            if balance > 0:
                db.use_game_time(balance)
                gt.controller.time_balance = 0
            return jsonify({'balance': 0})

        @app.route('/api/toggle_browser', methods=['POST'])
        def toggle_browser():
            data = request.get_json(force=True) or {}
            if not self._check_password(data):
                return jsonify({'error': '密碼錯誤'}), 403
            enabled = bool(data.get('enabled', True))
            gt.controller.browser_monitoring_enabled = enabled
            return jsonify({'browser_monitoring': enabled})

        @app.route('/api/close_browsers', methods=['POST'])
        def close_browsers():
            data = request.get_json(force=True) or {}
            if not self._check_password(data):
                return jsonify({'error': '密碼錯誤'}), 403
            gt.controller.stop_browser_processes()
            return jsonify({'success': True})

    @staticmethod
    def get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return '127.0.0.1'

    def start(self) -> str:
        """Start server in a daemon thread. Returns local IP address."""
        thread = threading.Thread(
            target=lambda: self.app.run(
                host='0.0.0.0',
                port=self.port,
                debug=False,
                use_reloader=False,
            ),
            daemon=True,
        )
        thread.start()
        return self.get_local_ip()


def start_remote_server(game_tracker, db, port: int = 5050):
    """Start the remote control server. Returns (ip, port)."""
    server = RemoteControlServer(game_tracker, db, port)
    ip = server.start()
    return ip, port
