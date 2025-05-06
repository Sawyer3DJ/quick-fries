
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import socket
import time
import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app)

orders = []
cleared_orders = []

@app.route('/test', methods=['GET'])
def test():
    return "Server is up and reachable!", 200

@app.route('/receive-order', methods=['POST'])
def receive_order():
    try:
        data = request.get_json()
        data['timestamp'] = time.time()
        data['recalled'] = False
        orders.append(data)
        return jsonify({"status": "Order received"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to receive order"}), 500

@app.route('/clear/<int:index>', methods=['POST'])
def clear_order(index):
    try:
        cleared_order = orders[index]
        cleared_order['cleared_at'] = time.time()
        cleared_orders.insert(0, cleared_order)  # newest first
        del orders[index]
        return ('', 204)
    except:
        return ('Not found', 404)

@app.route('/undo-clear', methods=['POST'])
def undo_clear():
    if cleared_orders:
        recalled_order = cleared_orders.pop(0)
        recalled_order['recalled'] = True
        orders.append(recalled_order)
    return ('', 204)

@app.route('/orders')
def get_orders():
    now = time.time()
    sorted_orders = sorted(orders, key=lambda x: x['timestamp'])
    for o in sorted_orders:
        o['elapsed'] = int(now - o['timestamp'])
    return jsonify(sorted_orders)

@app.route('/recall-history')
def recall_history():
    html = '''
    <html><head><title>Recall History</title>
    <style>
      body { font-family: Arial, sans-serif; background-color: #1a1a1a; color: white; padding: 20px; }
      h1 { color: #FF6A13; }
      table { width: 100%; border-collapse: collapse; background-color: #333; margin-top: 20px; }
      th, td { border: 1px solid #555; padding: 10px; text-align: center; }
      th { background-color: #FF6A13; }
      a button { margin-top: 20px; padding: 10px 20px; background-color: #FF6A13; color: white; border: none; cursor: pointer; }
    </style>
    </head><body>
    <h1>Recall History</h1>
    <table>
    <tr><th>Order #</th><th>Items</th><th>Comments</th><th>Time on Screen</th></tr>
    '''
    for order in cleared_orders:
        duration = int(order['cleared_at'] - order['timestamp'])
        summary = "<ul>" + "".join([f"<li>{i['quantity']}x {i['name']}</li>" for i in order['order']]) + "</ul>"
        html += f"<tr><td>#{order['orderNum']}</td><td>{summary}</td><td>{order['comments']}</td><td>{duration // 60}:{duration % 60:02d}</td></tr>"
    html += '''
    </table>
    <a href="/"><button>Back to Dashboard</button></a>
    </body></html>
    '''
    return html

@app.route('/')
def dashboard():
    now = datetime.datetime.now().strftime("%d/%m/%y %H:%M")
    html = f'''
    <html><head><title>Live Order Dashboard</title>
    <style>
      body {{ font-family: Arial, sans-serif; background-color: #1a1a1a; color: white; padding: 20px; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #333; }}
      th, td {{ border: 1px solid #555; padding: 10px; vertical-align: middle; text-align: center; }}
      th {{ background-color: #FF6A13; }}
      button {{ font-size: 16px; background-color: #dc3545; color: white; border: none; padding: 10px 15px; cursor: pointer; margin-left: 5px; }}
      #controlBar {{ display: flex; justify-content: flex-end; margin-bottom: 10px; gap: 10px; align-items: center; }}
      .recalled {{ color: #FFD700; font-weight: bold; margin-left: 10px; }}
      .controls {{ white-space: nowrap; display: flex; align-items: center; justify-content: center; gap: 6px; }}
      .light-box {{ width: 36px; height: 36px; border-radius: 5px; display: inline-block; margin: auto; }}
      .green {{ background-color: #28a745; }}
      .amber {{ background-color: #ffc107; }}
      .red {{ background-color: #dc3545; }}
      .order-id {{ font-size: 1.4em; color: white; font-weight: bold; }}
      .timer {{ font-size: 1.2em; font-weight: bold; }}
      label {{ font-size: 0.9em; margin-left: 10px; }}
      #datetime {{ position: absolute; top: 20px; right: 30px; font-size: 0.9em; color: #ccc; }}
      .split-cols {{ display: flex; justify-content: space-around; text-align: left; gap: 20px; }}
    </style>
    <script>
      let soundOn = true;
      let knownOrders = 0;
      let bell = new Audio("https://cdn.pixabay.com/audio/2022/10/30/audio_9f65c554b7.mp3");

      function formatTime(seconds) {{
        const m = String(Math.floor(seconds / 60)).padStart(2, '0');
        const s = String(seconds % 60).padStart(2, '0');
        return m + ':' + s;
      }}

      function getLightClass(elapsed) {{
        if (elapsed < 60) return 'green';
        else if (elapsed < 120) return 'amber';
        else return 'red';
      }}

      function fetchOrders() {{
        fetch('/orders').then(r => r.json()).then(data => {{
          if (data.length > knownOrders && soundOn) {{
            bell.play();
          }}
          knownOrders = data.length;
          let html = '<table><tr><th>Target</th><th>Time</th><th>Order #</th><th>Items</th><th>Comments</th><th>Clear</th></tr>';
          data.forEach((order, i) => {{
            const light = getLightClass(order.elapsed);
            let food = '', drink = '';
            order.order.forEach(function(itm) {{
              const name = itm.name.toLowerCase();
              if (name.includes("cola") || name.includes("coffee") || name.includes("fanta") || name.includes("tea") || name.includes("water") || name.includes("latte") || name.includes("cappuccino"))
                drink += `<li>${{itm.quantity}}x ${{itm.name}}</li>`;
              else
                food += `<li>${{itm.quantity}}x ${{itm.name}}</li>`;
            }});
            html += '<tr>';
            html += '<td><div class="light-box ' + light + '"></div></td>';
            html += '<td class="timer">' + formatTime(order.elapsed) + '</td>';
            html += '<td class="order-id">#' + order.orderNum + '</td>';
            html += `<td><div class="split-cols"><div><strong>Food:</strong><ul>${{food}}</ul></div><div><strong>Drinks:</strong><ul>${{drink}}</ul></div></div></td>`;
            html += '<td>' + order.comments + '</td>';
            html += '<td class="controls"><button onclick="clearOrder(' + i + ')">Clear</button>';
            html += (order.recalled ? '<span class="recalled">RECALLED</span>' : '');
            html += '</td></tr>';
          }});
          html += '</table>';
          document.getElementById('orderTable').innerHTML = html;
        }});
      }}

      function clearOrder(index) {{
        fetch('/clear/' + index, {{ method: 'POST' }}).then(() => fetchOrders());
      }}

      function undoClear() {{
        fetch('/undo-clear', {{ method: 'POST' }}).then(() => fetchOrders());
      }}

      function toggleSound(checkbox) {{
        soundOn = checkbox.checked;
      }}

      setInterval(fetchOrders, 5000);
      window.onload = fetchOrders;
    </script>
    </head><body>
    <div id="datetime">Date & Time: {now}</div>
    <h1 style="color:#FF6A13;">Live Order Dashboard</h1>
    <label><input type="checkbox" checked onchange="toggleSound(this)"> Enable Sound Alerts</label>
    <div id="controlBar">
      <a href="/overview"><button style="background-color:#FF6A13;">Overview</button></a>
      <a href="/recall-history"><button style="background-color:#FF6A13;">Recall History</button></a>
      <button onclick="fetchOrders()" style="background-color:#007bff;">Refresh</button>
      <button onclick="undoClear()" style="background-color:#888;">Undo Clear</button>
    </div>
    <div id="orderTable"></div>
    </body></html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"Flask server running at: http://{local_ip}:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
