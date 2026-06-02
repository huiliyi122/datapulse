"""
DataPulse 桌面应用入口 — 双击即用
"""
import os
import sys
import threading
import time
import webbrowser


def main():
    """启动服务并自动打开浏览器"""
    import uvicorn

    # PyInstaller 兼容
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
        backend_dir = os.path.join(base_dir, 'backend')
        spider_dir = os.path.join(base_dir, 'spider')
    elif os.environ.get('DATAPULSE_PORTABLE'):
        base_dir = os.getcwd()
        backend_dir = os.path.join(base_dir, 'backend')
        spider_dir = os.path.join(base_dir, 'spider')
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = base_dir
        spider_dir = os.path.join(os.path.dirname(base_dir), 'spider')

    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)
    sys.path.insert(0, spider_dir)

    # 延迟打开浏览器
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://127.0.0.1:8000")

    threading.Thread(target=open_browser, daemon=True).start()

    print("=" * 50)
    print("  DataPulse v0.3.5 — Data Collection & Analysis Platform")
    print("  浏览器已自动打开，如未打开请访问:")
    print("  http://127.0.0.1:8000")
    print("  按 Ctrl+C 停止服务")
    print("=" * 50)

    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
