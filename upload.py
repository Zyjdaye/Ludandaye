import requests
import pyperclip
import time
import os
import platform
import json
import hashlib
import threading
import argparse
from urllib.parse import urljoin

# 服务器配置
class ServerConfig:
    # 阿里云服务器配置
    CLOUD_HOST = "8.156.72.8"    # 阿里云公网IP
    CLOUD_PORT = "5001"          # 服务器端口
    CLOUD_PROTOCOL = "http"      # 服务器协议
    
    @staticmethod
    def get_server_url(server_type='cloud'):
        if server_type == 'local':
            return "http://127.0.0.1:5001"
        
        # 从环境变量获取配置
        host = os.environ.get('SERVER_HOST', ServerConfig.CLOUD_HOST)
        port = os.environ.get('SERVER_PORT', ServerConfig.CLOUD_PORT)
        protocol = os.environ.get('SERVER_PROTOCOL', ServerConfig.CLOUD_PROTOCOL)
        
        # 构建服务器URL
        if ':' in host:  # 如果host中已包含端口
            base_url = f"{protocol}://{host}"
        else:
            base_url = f"{protocol}://{host}:{port}"
        
        return base_url

class ClipboardSync:
    def __init__(self, server_type='cloud'):
        self.device_id = self.get_device_id()
        self.server_url = ServerConfig.get_server_url(server_type)
        self.last_error_time = 0
        self.error_count = 0
        self.max_retry_interval = 30  # 最大重试间隔（秒）
        
    @staticmethod
    def get_device_id():
        system = platform.system()
        machine = platform.machine()
        node = platform.node()
        device_info = f"{system}_{machine}_{node}"
        return hashlib.md5(device_info.encode()).hexdigest()[:8]
    
    def handle_request_error(self, e, operation):
        """统一的错误处理"""
        current_time = time.time()
        if current_time - self.last_error_time > 60:  # 重置计数器
            self.error_count = 0
        
        self.error_count += 1
        self.last_error_time = current_time
        
        # 计算重试等待时间（指数退避）
        wait_time = min(2 ** self.error_count, self.max_retry_interval)
        
        print(f"❌ {operation}失败: {str(e)}")
        print(f"⏳ {wait_time}秒后重试...")
        time.sleep(wait_time)
    
    def upload_clipboard(self, content):
        url = urljoin(self.server_url, "/clipboard")
        data = {
            "content": content,
            "device_id": self.device_id
        }
        
        try:
            print(f"📤 正在上传内容到 {self.server_url}...")
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ 成功上传剪贴板内容: {content[:30]}...")
                self.error_count = 0  # 重置错误计数
            else:
                print(f"❌ 上传失败: {response.status_code}")
                print(f"错误信息: {response.text}")
        except requests.exceptions.RequestException as e:
            self.handle_request_error(e, "上传")
    
    def get_latest_content(self):
        url = urljoin(self.server_url, "/clipboard/latest")
        params = {"device_id": self.device_id}
        
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("content")
            return None
        except requests.exceptions.RequestException as e:
            self.handle_request_error(e, "获取最新内容")
            return None
    
    def sync_from_server(self):
        while True:
            try:
                current_content = pyperclip.paste()
                latest_content = self.get_latest_content()
                
                if latest_content and latest_content != current_content:
                    print(f"\n📥 检测到服务器有新内容，正在同步...")
                    pyperclip.copy(latest_content)
                    print(f"✅ 已同步新内容: {latest_content[:30]}...")
            except Exception as e:
                print(f"❌ 同步过程出错: {str(e)}")
            
            time.sleep(2)
    
    def start(self):
        print(f"📱 设备ID: {self.device_id}")
        print(f"🌐 服务器地址: {self.server_url}")
        print("🔄 开始监控剪贴板...")
        print("提示：复制的内容会自动上传，其他设备的新内容会自动同步到本地")
        
        try:
            last_content = pyperclip.paste()
            print(f"当前剪贴板内容: {last_content[:30]}...")
        except Exception as e:
            print(f"❌ 读取剪贴板失败: {str(e)}")
            last_content = ""
        
        # 启动服务器同步线程
        sync_thread = threading.Thread(target=self.sync_from_server, daemon=True)
        sync_thread.start()
        
        try:
            while True:
                try:
                    current_content = pyperclip.paste()
                    if current_content != last_content and current_content.strip():
                        print(f"\n📋 检测到本地剪贴板变化:")
                        print(f"新内容: {current_content[:50]}...")
                        self.upload_clipboard(current_content)
                        last_content = current_content
                    time.sleep(0.5)
                except Exception as e:
                    print(f"❌ 监控过程出错: {str(e)}")
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 程序已停止")

def main():
    parser = argparse.ArgumentParser(description='剪贴板同步客户端')
    parser.add_argument('--local', action='store_true', help='使用本地服务器')
    parser.add_argument('--host', help='服务器主机地址')
    parser.add_argument('--port', help='服务器端口')
    parser.add_argument('--protocol', choices=['http', 'https'], help='服务器协议')
    args = parser.parse_args()
    
    # 设置环境变量
    if args.host:
        os.environ['SERVER_HOST'] = args.host
    if args.port:
        os.environ['SERVER_PORT'] = args.port
    if args.protocol:
        os.environ['SERVER_PROTOCOL'] = args.protocol
    
    # 创建并启动同步器
    syncer = ClipboardSync('local' if args.local else 'cloud')
    syncer.start()

if __name__ == "__main__":
    main()