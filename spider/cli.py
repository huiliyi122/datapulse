"""
DataPulse CLI - 命令行工具
"""
import argparse
import json
import os
import sys


def cmd_crawl(args):
    """执行爬虫任务"""
    print(f"🕷️ DataPulse - 开始采集")
    print(f"   目标URL: {len(args.urls)} 个")
    print(f"   并发数:  {args.concurrent}")
    print(f"   延迟:    {args.delay}s")
    print()

    from spider.engine import SpiderEngine, CrawlRequest
    from spider.pipelines import (
        DataPipelineManager, DataItem,
        JsonExportPipeline, DedupPipeline,
    )

    engine = SpiderEngine(concurrent=args.concurrent)
    pipeline = DataPipelineManager()
    pipeline.add_pipeline(DedupPipeline())
    pipeline.add_pipeline(JsonExportPipeline(output_dir=args.output))

    result = engine.run(args.urls)

    print()
    print(f"✅ 采集完成!")
    print(f"   总计: {result['stats']['total']}")
    print(f"   成功: {result['stats']['success']}")
    print(f"   失败: {result['stats']['failed']}")
    print(f"   耗时: {result['elapsed']:.1f}s")

    pipeline.close()
    return result


def cmd_serve(args):
    """启动 Web 服务"""
    import uvicorn
    print(f"🌐 DataPulse - Web 服务启动")
    print(f"   📊 前端页面:  http://localhost:3000")
    print(f"   📖 API 文档:  http://localhost:{args.port}/docs")
    print(f"   ❤️  健康检查: http://localhost:{args.port}/api/health")
    uvicorn.run("backend.api:app", host=args.host, port=args.port, reload=args.reload)


def cmd_analyze(args):
    """分析本地文件"""
    import pandas as pd
    from backend.analysis import DataAnalyzer

    # 加载文件
    if args.file.endswith(".csv"):
        df = pd.read_csv(args.file)
    elif args.file.endswith((".xlsx", ".xls")):
        df = pd.read_excel(args.file)
    elif args.file.endswith(".json"):
        df = pd.read_json(args.file)
    else:
        print(f"❌ 不支持的文件格式: {args.file}")
        sys.exit(1)

    print(f"📊 分析文件: {args.file}")
    print(f"   行数: {len(df)}  列数: {len(df.columns)}")
    print()

    analyzer = DataAnalyzer(df)
    result = analyzer.summary()
    print(f"📋 数据概览:")
    for k, v in result.items():
        if k not in ["columns_detail", "insights"]:
            print(f"   {k}: {v}")

    print()
    if "insights" in result:
        print("💡 数据洞察:")
        for insight in result["insights"]:
            print(f"   - {insight}")

    print()
    print("📝 字段详情:")
    for col in df.columns[:10]:
        desc = analyzer.describe_column(col)
        print(f"   {col}: {json.dumps(desc, ensure_ascii=False, default=str)[:120]}")


def main():
    parser = argparse.ArgumentParser(
        prog="datapulse",
        description="DataPulse - 数据采集与分析平台",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # crawl 子命令
    crawl_parser = subparsers.add_parser("crawl", help="爬取网页数据")
    crawl_parser.add_argument("urls", nargs="+", help="目标 URL")
    crawl_parser.add_argument("-c", "--concurrent", type=int, default=5, help="并发数 (默认 5)")
    crawl_parser.add_argument("-d", "--delay", type=float, default=1.0, help="请求延迟秒数 (默认 1.0)")
    crawl_parser.add_argument("-o", "--output", default="./output", help="输出目录 (默认 ./output)")
    crawl_parser.set_defaults(func=cmd_crawl)

    # serve 子命令
    serve_parser = subparsers.add_parser("serve", help="启动 Web 服务")
    serve_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    serve_parser.add_argument("--port", type=int, default=8000, help="监听端口")
    serve_parser.add_argument("--no-reload", dest="reload", action="store_false", help="禁用热重载")
    serve_parser.set_defaults(func=cmd_serve, reload=True)

    # analyze 子命令
    analyze_parser = subparsers.add_parser("analyze", help="分析本地数据文件")
    analyze_parser.add_argument("file", help="CSV/Excel/JSON 文件路径")
    analyze_parser.set_defaults(func=cmd_analyze)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
