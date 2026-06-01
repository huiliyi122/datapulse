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
    # 确保工作目录正确
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 初始化种子数据
    try:
        from seed import seed_all
        seed_all()
    except Exception:
        pass

    # 延迟打开浏览器
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://127.0.0.1:8000")

    threading.Thread(target=open_browser, daemon=True).start()

    # 启动服务
    import uvicorn
    print("=" * 50)
    print("  DataPulse v0.3.1 — 数据采集分析平台")
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
