import requests
import pyperclip
import time
import os
import platform
import json
import hashlib
import threading

# 服务器URL配置
SERVER_URL = os.environ.get('SERVER_URL', 'http://127.0.0.1:5001')

# 设备ID生成函数
def get_device_id():
    # 获取系统信息
    system = platform.system()
    machine = platform.machine()
    node = platform.node()
    
    # 组合信息并生成唯一ID
    device_info = f"{system}_{machine}_{node}"
    return hashlib.md5(device_info.encode()).hexdigest()[:8]

# 剪贴板内容上传函数
def upload_clipboard(content):
    url = f"{SERVER_URL}/clipboard"
    data = {
        "content": content,
        "device_id": device_id
    }
    
    try:
        print(f"📤 正在上传内容...")
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ 成功上传剪贴板内容: {content[:30]}...")
        else:
            print(f"❌ 上传失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 上传出错: {str(e)}")

# 从服务器获取最新内容
def get_latest_content():
    url = f"{SERVER_URL}/clipboard/latest"
    params = {"device_id": device_id}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("content")
        return None
    except Exception as e:
        print(f"❌ 获取最新内容失败: {str(e)}")
        return None

# 同步其他设备的内容
def sync_from_server():
    while True:
        try:
            # 获取当前剪贴板内容
            current_content = pyperclip.paste()
            
            # 获取服务器最新内容
            latest_content = get_latest_content()
            
            # 如果服务器有新内容且与当前内容不同，则更新本地剪贴板
            if latest_content and latest_content != current_content:
                print(f"\n📥 检测到服务器有新内容，正在同步...")
                pyperclip.copy(latest_content)
                print(f"✅ 已同步新内容: {latest_content[:30]}...")
        
        except Exception as e:
            print(f"❌ 同步过程出错: {str(e)}")
        
        time.sleep(2)  # 每2秒检查一次

# 主函数
def main():
    global device_id
    device_id = get_device_id()
    print(f"📱 设备ID: {device_id}")
    print("🔄 开始监控剪贴板...")
    print("提示：复制的内容会自动上传，其他设备的新内容会自动同步到本地")
    
    # 获取初始剪贴板内容
    try:
        last_content = pyperclip.paste()
        print(f"当前剪贴板内容: {last_content[:30]}...")
    except Exception as e:
        print(f"❌ 读取剪贴板失败: {str(e)}")
        last_content = ""
    
    # 启动服务器同步线程
    sync_thread = threading.Thread(target=sync_from_server, daemon=True)
    sync_thread.start()
    
    try:
        while True:
            try:
                # 获取当前剪贴板内容
                current_content = pyperclip.paste()
                
                # 如果内容发生变化，则上传
                if current_content != last_content and current_content.strip():
                    print(f"\n📋 检测到本地剪贴板变化:")
                    print(f"新内容: {current_content[:50]}...")
                    upload_clipboard(current_content)
                    last_content = current_content
                
                # 等待一段时间再检查
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ 监控过程出错: {str(e)}")
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n👋 程序已停止")

if __name__ == "__main__":
    main()