"""
演示数据初始化脚本
启动时自动创建示例数据集和爬虫任务记录
"""
import json
import os


DEMO_DATA = {
    "电子产品价格数据.csv": (
        "商品名称,品牌,价格,销量,评分,上架日期\n"
        + "iPhone 15 Pro Max,Apple,9999,15200,4.8,2024-09-20\n"
        + "华为 Mate 60 Pro,华为,6999,28500,4.9,2024-08-29\n"
        + "小米 14 Pro,小米,4999,32000,4.7,2024-10-26\n"
        + "三星 Galaxy S24 Ultra,Samsung,9699,8900,4.6,2024-01-17\n"
        + "OPPO Find X7,OPPO,3999,18600,4.5,2024-01-08\n"
        + "vivo X100 Pro,vivo,4999,21500,4.7,2024-11-13\n"
        + "荣耀 Magic6 Pro,荣耀,5699,12800,4.6,2024-01-11\n"
        + "一加 12,一加,4299,9800,4.8,2023-12-05\n"
        + "MacBook Pro 14,Apple,14999,5600,4.9,2024-10-30\n"
        + "联想 ThinkPad X1,联想,10999,3200,4.5,2024-03-15\n"
        + "iPad Pro M4,Apple,8999,7800,4.8,2024-05-07\n"
        + "华为 MatePad Pro,华为,4299,6500,4.6,2024-02-22\n"
        + "小米平板 7 Pro,小米,3299,11200,4.5,2024-10-29\n"
        + "索尼 WH-1000XM5,索尼,2499,18900,4.9,2022-05-19\n"
        + "AirPods Pro 2,Apple,1899,35600,4.8,2023-09-12\n"
        + "戴森 V15 Detect,戴森,4990,8200,4.7,2024-03-01\n"
    ),
    "电商销售数据.csv": (
        "日期,订单数,销售额,访客数,转化率,客单价\n"
        + "\n".join(
            f"2026-01-{d:02d},{150+d*5},{75000+d*2000},{5000+d*200},{2.9+d*0.01:.2f},{500+d*2:.2f}"
            for d in range(1, 21)
        )
    ),
    "用户评论数据.csv": (
        "用户名,评分,评论内容,商品分类,评论日期\n"
        + "张***,5,质量非常好物流很快值得推荐,手机,2026-01-15\n"
        + "李***,4,性价比很高用起来很流畅,手机,2026-01-14\n"
        + "王***,2,屏幕有划痕已经申请换货,手机,2026-01-13\n"
        + "赵***,5,收到货了比实体店便宜不少,电脑,2026-01-12\n"
        + "陈***,3,一般般没有想象中好,平板,2026-01-11\n"
        + "刘***,5,第3次购买了送朋友很开心,耳机,2026-01-10\n"
        + "吴***,1,质量太差了用了两天就坏了,手机,2026-01-09\n"
        + "孙***,4,颜色很漂亮手感也很棒,手机,2026-01-08\n"
        + "周***,5,非常满意的一次购物体验,电脑,2026-01-07\n"
        + "黄***,4,包装很严实没有损坏好评,平板,2026-01-06\n"
        + "许***,5,音质特别棒降噪效果很好,耳机,2026-01-05\n"
        + "林***,3,价格波动太大买完就降价,手机,2026-01-04\n"
        + "何***,4,外观设计很时尚功能齐全,电脑,2026-01-03\n"
        + "马***,5,孩子很喜欢质量挺好的,平板,2026-01-02\n"
        + "罗***,1,客服态度很差问题没解决,耳机,2026-01-01\n"
    ),
}


def seed_datasets(upload_dir: str = "./uploads", force: bool = False):
    """创建演示数据集"""
    os.makedirs(upload_dir, exist_ok=True)

    count = 0
    for filename, content in DEMO_DATA.items():
        filepath = os.path.join(upload_dir, filename)
        if os.path.exists(filepath) and not force:
            continue
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1

    return count


def seed_scraper_tasks(output_dir: str = "./output", force: bool = False):
    """创建演示爬虫任务记录"""
    os.makedirs(output_dir, exist_ok=True)

    tasks = [
        {
            "task_id": "demo_products",
            "status": "completed",
            "total": 15,
            "success": 15,
            "failed": 0,
            "elapsed": 2.3,
            "urls": ["https://example.com/products"],
            "created_at": "2026-06-01T08:00:00",
            "completed_at": "2026-06-01T08:02:18",
            "results": [
                {"title": "无线蓝牙耳机", "price": "89.00", "store": "数码旗舰店", "crawled_at": "2026-06-01T08:01:00"},
                {"title": "手机快充充电器", "price": "35.00", "store": "数码旗舰店", "crawled_at": "2026-06-01T08:01:02"},
                {"title": "笔记本支架", "price": "69.00", "store": "办公用品店", "crawled_at": "2026-06-01T08:01:04"},
                {"title": "机械键盘", "price": "299.00", "store": "外设旗舰店", "crawled_at": "2026-06-01T08:01:06"},
                {"title": "鼠标垫大号", "price": "19.90", "store": "外设旗舰店", "crawled_at": "2026-06-01T08:01:08"},
            ],
        },
        {
            "task_id": "demo_prices",
            "status": "completed",
            "total": 20,
            "success": 20,
            "failed": 0,
            "elapsed": 3.1,
            "urls": ["https://example.com/prices"],
            "created_at": "2026-06-01T09:00:00",
            "completed_at": "2026-06-01T09:03:06",
            "results": [
                {"title": "iPhone 15 128G", "price": "5999", "platform": "京东", "crawled_at": "2026-06-01T09:01:00"},
                {"title": "华为 Mate 60", "price": "5499", "platform": "天猫", "crawled_at": "2026-06-01T09:01:05"},
                {"title": "小米 14", "price": "3999", "platform": "京东", "crawled_at": "2026-06-01T09:01:10"},
                {"title": "OPPO Find X7", "price": "4299", "platform": "拼多多", "crawled_at": "2026-06-01T09:01:15"},
                {"title": "vivo X100", "price": "4599", "platform": "京东", "crawled_at": "2026-06-01T09:01:20"},
            ],
        },
        {
            "task_id": "demo_news",
            "status": "completed",
            "total": 30,
            "success": 28,
            "failed": 2,
            "elapsed": 5.2,
            "urls": ["https://example.com/news"],
            "created_at": "2026-06-01T10:00:00",
            "completed_at": "2026-06-01T10:05:12",
            "results": [
                {"title": "AI 技术新突破", "source": "科技日报", "date": "2026-06-01", "crawled_at": "2026-06-01T10:02:00"},
                {"title": "Python 4.0 发布计划", "source": "InfoQ", "date": "2026-06-01", "crawled_at": "2026-06-01T10:02:05"},
                {"title": "开源项目月度报告", "source": "GitHub Blog", "date": "2026-06-01", "crawled_at": "2026-06-01T10:02:10"},
            ],
        },
    ]

    count = 0
    for task in tasks:
        filepath = os.path.join(output_dir, f"{task['task_id']}.json")
        if os.path.exists(filepath) and not force:
            continue
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        count += 1

    return count


def seed_all(upload_dir: str = "./uploads", output_dir: str = "./output", force: bool = False) -> dict:
    """初始化所有演示数据"""
    datasets = seed_datasets(upload_dir, force)
    tasks = seed_scraper_tasks(output_dir, force)
    return {"datasets": datasets, "tasks": tasks}


def main():
    from logging_config import get_logger
    logger = get_logger("datapulse.seed")
    result = seed_all()
    logger.info("种子数据已创建", extra={"datasets": result['datasets'], "tasks": result['tasks']})


if __name__ == "__main__":
    main()
