"""自定义管理命令：python manage.py seed_demo

为什么要写命令，而不是手动一条条添加？
    1. 可重复执行：用 get_or_create / update_or_create，不会产生重复数据
    2. 团队共享：别人拉下代码执行一条命令就有演示数据
    3. 可版本管理：数据准备逻辑跟着代码一起提交
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from library.models import Book, Category


class Command(BaseCommand):
    help = "写入演示用的分类和图书数据（可重复执行）"

    def handle(self, *args, **options):
        # 1. 先准备分类
        category_names = ["技术", "小说", "历史", "心理"]
        categories = {}
        for name in category_names:
            category, _ = Category.objects.get_or_create(name=name)
            categories[name] = category

        # 2. 再准备图书：(书名, 作者, 价格, 库存, 分类)
        books = [
            ("Python 编程从入门到实践", "Eric Matthes", "89.00", 12, "技术"),
            ("Django 企业开发实战", "黄永祥", "99.00", 6, "技术"),
            ("深入理解计算机系统", "Randal E. Bryant", "139.00", 3, "技术"),
            ("活着", "余华", "45.00", 20, "小说"),
            ("百年孤独", "加西亚·马尔克斯", "55.00", 8, "小说"),
            ("三体", "刘慈欣", "68.00", 15, "小说"),
            ("人类简史", "尤瓦尔·赫拉利", "68.00", 10, "历史"),
            ("万历十五年", "黄仁宇", "42.00", 5, "历史"),
            ("明朝那些事儿", "当年明月", "358.00", 2, "历史"),
            ("被讨厌的勇气", "岸见一郎", "49.80", 9, "心理"),
            ("思考，快与慢", "丹尼尔·卡尼曼", "79.00", 7, "心理"),
            ("非暴力沟通", "马歇尔·卢森堡", "39.00", 11, "心理"),
        ]

        for title, author, price, stock, category_name in books:
            # update_or_create：存在就更新，不存在就创建
            Book.objects.update_or_create(
                title=title,
                defaults={
                    "author": author,
                    "price": Decimal(price),
                    "stock": stock,
                    "category": categories[category_name],
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"演示数据已准备完成：{Category.objects.count()} 个分类，"
                f"{Book.objects.count()} 本图书"
            )
        )
