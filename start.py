import subprocess
import sys
import time
import os
import signal
import threading
import webbrowser

def run_server():
    """运行服务器"""
    print("🚀 启动服务器...")
    return subprocess.Popen([sys.executable, "app.py"])

def run_client():
    """运行客户端"""
    print("📋 启动剪贴板监控...")
    return subprocess.Popen([sys.executable, "upload.py"])

def open_browser():
    """打开浏览器查看历史记录"""
    time.sleep(2)  # 等待服务器启动
    print("🌐 打开历史记录查看器...")
    webbrowser.open("http://127.0.0.1:5001")

def show_menu():
    """显示菜单"""
    print("\n=== 剪贴板同步工具 ===")
    print("1. 查看历史记录")
    print("2. 退出程序")
    print("提示: 按Ctrl+C退出程序")

def view_clipboard_history():
    """查看剪贴板历史"""
    subprocess.run([sys.executable, "view_history.py"])

def main():
    # 启动服务器
    server_process = run_server()
    time.sleep(1)  # 等待服务器启动
    
    # 启动客户端
    client_process = run_client()
    
    # 打开浏览器
    threading.Thread(target=open_browser).start()
    
    try:
        while True:
            show_menu()
            try:
                choice = input("\n请选择操作 (1-2): ").strip()
                if choice == "1":
                    view_clipboard_history()
                elif choice == "2":
                    raise KeyboardInterrupt
                else:
                    print("❌ 无效的选择，请重试")
            except ValueError:
                print("❌ 请输入有效的数字")
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n正在关闭程序...")
        # 关闭所有子进程
        for process in [server_process, client_process]:
            if process:
                if sys.platform == "win32":
                    process.terminate()
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        print("👋 程序已退出")

if __name__ == "__main__":
    # 在非Windows系统上创建新的进程组
    if sys.platform != "win32":
        os.setpgrp()
    main() 