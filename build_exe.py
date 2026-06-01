"""
DataPulse 桌面版构建脚本

使用 PyInstaller 将项目打包为单个 .exe 文件

构建步骤:
    1. 安装依赖: pip install pyinstaller
    2. 构建前端: cd frontend && npm install && npm run build
    3. 运行本脚本: python build_exe.py
    4. 输出文件: dist/DataPulse.exe

双击 DataPulse.exe 即可启动服务，自动打开浏览器
"""
import os
import shutil
import subprocess
import sys


def check_deps():
    """检查必要工具"""
    # 检查 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("❌ 缺少 PyInstaller，请先安装: pip install pyinstaller")
        sys.exit(1)

    print("✅ PyInstaller 已安装")


def build_frontend():
    """构建前端静态文件"""
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

    print("\n📦 构建前端...")
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)

    subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)

    # 确保产出存在
    dist_dir = os.path.join(frontend_dir, "dist")
    if not os.path.exists(dist_dir):
        print("❌ 前端构建失败: frontend/dist 不存在")
        sys.exit(1)

    print(f"✅ 前端构建完成: {dist_dir}")


def build_exe():
    """调用 PyInstaller 打包"""
    project_root = os.path.dirname(os.path.abspath(__file__))

    print("\n🔨 PyInstaller 打包中（需要几分钟）...")

    # 构建命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "DataPulse",
        "--add-data", f"{project_root}/frontend/dist{os.pathsep}frontend/dist",
        "--add-data", f"{project_root}/backend{os.pathsep}backend",
        "--add-data", f"{project_root}/spider{os.pathsep}spider",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "pandas",
        "--hidden-import", "jieba",
        "--hidden-import", "aiohttp",
        "--hidden-import", "beautifulsoup4",
        os.path.join(project_root, "backend", "app.py"),
    ]

    subprocess.run(cmd, check=True)

    output = os.path.join(project_root, "dist", "DataPulse.exe")
    if os.path.exists(output):
        size_mb = os.path.getsize(output) / (1024 * 1024)
        print(f"\n🎉 构建成功!")
        print(f"   文件: {output}")
        print(f"   大小: {size_mb:.1f} MB")
        print(f"\n   双击 DataPulse.exe 即可启动")
    else:
        print("❌ 构建失败")
        sys.exit(1)


def main():
    print("=" * 50)
    print("  DataPulse 桌面版构建工具")
    print("=" * 50)

    check_deps()
    build_frontend()
    build_exe()

    print("\n📦 分发提示:")
    print("  - 将 dist/DataPulse.exe 发给用户即可")
    print("  - 用户无需安装 Python / Docker / Node.js")
    print("  - 首次启动可能较慢（解压），之后正常")


if __name__ == "__main__":
    main()
