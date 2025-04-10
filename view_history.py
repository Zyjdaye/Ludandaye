import requests
from datetime import datetime
import pytz

def format_timestamp(timestamp_str):
    """格式化时间戳为本地时间"""
    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    local_dt = dt.astimezone(pytz.local)
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")

def view_history(device_id=None, limit=10):
    """查看剪贴板历史记录"""
    url = "http://127.0.0.1:5001/clipboard/history"
    params = {"limit": limit}
    if device_id:
        params["device_id"] = device_id
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            items = response.json()
            if not items:
                print("没有找到历史记录")
                return
            
            print("\n=== 剪贴板历史记录 ===")
            print(f"显示最近 {len(items)} 条记录:")
            print("-" * 50)
            
            for item in items:
                print(f"📝 内容: {item['content']}")
                print(f"📱 设备: {item['device_id']}")
                print(f"⏰ 时间: {format_timestamp(item['timestamp'])}")
                print("-" * 50)
        else:
            print(f"获取历史记录失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="查看剪贴板历史记录")
    parser.add_argument("--device", help="按设备ID筛选")
    parser.add_argument("--limit", type=int, default=10, help="显示记录数量（默认10条）")
    
    args = parser.parse_args()
    view_history(args.device, args.limit) 