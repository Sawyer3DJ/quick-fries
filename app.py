
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

orders = []

dashboard_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Beefeater Orders</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; padding: 20px; }
        h1 { color: #FF6A13; text-align: center; }
        .order { background: #333; padding: 10px; margin: 10px 0; border-left: 5px solid #FF6A13; }
    </style>
</head>
<body>
    <h1>Live Orders</h1>
    {% for order in orders %}
    <div class="order">
        <strong>Time:</strong> {{ order['timestamp'] }}<br>
        <strong>Items:</strong> {{ order['order'] | join(', ') }}<br>
        <strong>Comments:</strong> {{ order['comments'] }}
    </div>
    {% else %}
    <p>No orders yet.</p>
    {% endfor %}
    <script>
        setTimeout(() => window.location.reload(), 5000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(dashboard_template, orders=orders)

@app.route('/receive-order', methods=['POST'])
def receive_order():
    try:
        order = request.json
        order['timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        orders.append(order)
        print("Order received:", order)
        return jsonify({"message": "Order received successfully!"}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Failed to receive order"}), 500

@app.route('/test')
def test():
    return "Server is up and reachable!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
