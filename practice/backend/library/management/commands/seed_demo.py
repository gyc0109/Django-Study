"""自定义管理命令：python manage.py seed_demo

为什么写命令，而不是手动在 admin 里一条条添加？
    1. 可重复执行：用 get_or_create / update_or_create，不会产生重复数据
    2. 团队共享：别人拉下代码，执行一条命令就有演示数据
    3. 可版本管理：数据准备逻辑跟着代码一起提交，改了什么一目了然

Django 找命令的规则（目录结构不能错）：
    library/
        management/
            __init__.py            <- 必须有，否则不是 Python 包
            commands/
                __init__.py        <- 必须有
                seed_demo.py       <- 文件名就是命令名
执行时写 `python manage.py seed_demo`（不带 .py）。
"""

# Decimal：把字符串 "89.00" 精确地转成小数，避免浮点误差。
from decimal import Decimal

# BaseCommand 是所有管理命令的基类。
from django.core.management.base import BaseCommand

# 命令里要操作模型，所以导入它们（注意从项目根开始写完整路径）。
from library.models import Book, Category


class Command(BaseCommand):
    """Django 会实例化这个类，然后调用 handle()。

    help 属性的内容会显示在 `python manage.py help seed_demo` 里。
    """

    help = "写入演示用的分类和图书数据（可重复执行）"

    def handle(self, *args, **options):
        """命令的真正入口。

        *args / **options：
            Django 会把命令行参数解析后传进来。
            本命令没有自定义参数，所以直接忽略即可。
        """

        # ========================================================
        # 第 1 步：准备分类
        # ========================================================
        category_names = ["技术", "小说", "历史", "心理"]

        # 用一个字典把「分类名 -> 分类对象」记下来，
        # 后面创建图书时就能直接拿到对象，不用再查一次数据库。
        categories = {}

        for name in category_names:
            # get_or_create(name=name) 的返回值是 (对象, 是否新建)：
            #   不存在 -> 创建一条，created=True
            #   已存在 -> 直接返回，created=False
            # 用 _ 接收「是否新建」，表示我们并不关心这个值。
            # 这样重复执行命令也不会插入重复分类。
            category, _ = Category.objects.get_or_create(name=name)
            categories[name] = category

        # ========================================================
        # 第 2 步：准备图书数据
        # 每条是元组：(书名, 作者, 价格字符串, 库存, 分类名)
        # 价格用字符串而不是浮点数，是为了传给 Decimal 时保持精确。
        # ========================================================
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

        # 用元组解包把一行拆成 5 个变量，可读性比 books[i][0] 好得多。
        for title, author, price, stock, category_name in books:
            # update_or_create 的规则：
            #   按 title 查找；
            #   找到 -> 用 defaults 里的值更新（书名本身不参与更新）
            #   没找到 -> 创建一条，字段值来自 title + defaults
            # 这样反复执行命令，数据会被「重置」成这里的值，不会越跑越多。
            Book.objects.update_or_create(
                title=title,
                defaults={
                    "author": author,
                    # Decimal("89.00") 精确表示 89.00，
                    # 比 float 的 89.0 更适合金额字段。
                    "price": Decimal(price),
                    "stock": stock,
                    # 从字典里取出分类对象（外键赋对象，Django 自动存它的 id）
                    "category": categories[category_name],
                },
            )

        # ========================================================
        # 第 3 步：在终端打印结果
        # ========================================================
        # self.stdout.write 比 print 更规范：
        #   可以用 self.style.SUCCESS 加绿色，测试时也方便捕获输出。
        self.stdout.write(
            self.style.SUCCESS(
                f"演示数据已准备完成：{Category.objects.count()} 个分类，"
                f"{Book.objects.count()} 本图书"
            )
        )
