from flask import Flask, request, jsonify, render_template, render_template_string
from flask_cors import CORS
from models import db, ClipboardItem
from db import init_db
from datetime import datetime
import pytz
import os

app = Flask(__name__)
CORS(app)  # 启用CORS支持

# 配置数据库
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Railway环境使用PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
else:
    # 本地环境使用SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clipboard.db'

init_db(app)

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>剪贴板历史记录</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .clipboard-item {
            background: white;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .content {
            font-size: 16px;
            margin-bottom: 10px;
            word-break: break-all;
        }
        .meta {
            color: #666;
            font-size: 14px;
        }
        .refresh-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background: #45a049;
        }
        .empty-message {
            text-align: center;
            color: #666;
            margin-top: 50px;
        }
    </style>
</head>
<body>
    <h1>📋 剪贴板历史记录</h1>
    <div style="text-align: center;">
        <button class="refresh-btn" onclick="location.reload()">刷新</button>
    </div>
    {% if items %}
        {% for item in items %}
        <div class="clipboard-item">
            <div class="content">{{ item.content }}</div>
            <div class="meta">
                📱 设备ID: {{ item.device_id }}<br>
                ⏰ 时间: {{ item.timestamp }}
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div class="empty-message">
            <p>还没有剪贴板记录</p>
        </div>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def index():
    # 获取最近的剪贴板记录
    items = ClipboardItem.query.order_by(ClipboardItem.timestamp.desc()).limit(20).all()
    
    # 转换时间为本地时间
    local_tz = pytz.timezone('Asia/Shanghai')  # 使用中国时区
    for item in items:
        local_time = item.timestamp.replace(tzinfo=pytz.UTC).astimezone(local_tz)
        item.timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template_string(HTML_TEMPLATE, items=items)

# 👉 剪贴板上传接口
@app.route("/clipboard", methods=["POST"])
def upload_clipboard():
    data = request.get_json()
    content = data.get("content")
    device_id = data.get("device_id")

    if not content or not device_id:
        return jsonify({"error": "Missing content or device_id"}), 400

    item = ClipboardItem(content=content, device_id=device_id, timestamp=datetime.utcnow())
    db.session.add(item)
    db.session.commit()

    return jsonify({"status": "success", "id": item.id})

# 👉 获取最新剪贴板内容接口
@app.route("/clipboard/latest", methods=["GET"])
def get_latest_clipboard():
    device_id = request.args.get("device_id")
    if not device_id:
        return jsonify({"error": "Missing device_id"}), 400

    item = ClipboardItem.query.filter_by(device_id=device_id)\
        .order_by(ClipboardItem.timestamp.desc()).first()

    if not item:
        return jsonify({"message": "No data found"}), 404

    return jsonify({
        "id": item.id,
        "content": item.content,
        "device_id": item.device_id,
        "timestamp": item.timestamp.isoformat()
    })

# 👉 获取剪贴板历史记录接口
@app.route("/clipboard/history", methods=["GET"])
def get_clipboard_history():
    device_id = request.args.get("device_id")
    limit = request.args.get("limit", default=10, type=int)
    
    query = ClipboardItem.query
    if device_id:
        query = query.filter_by(device_id=device_id)
    
    items = query.order_by(ClipboardItem.timestamp.desc()).limit(limit).all()
    
    return jsonify([{
        "id": item.id,
        "content": item.content,
        "device_id": item.device_id,
        "timestamp": item.timestamp.isoformat()
    } for item in items])

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)