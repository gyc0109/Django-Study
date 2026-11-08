"""数据模型（Model）—— 用 Python 类描述数据库表。

本项目有两张表，形成「一对多」关系：
    一个分类（Category）  ->  多本书（Book）

为什么要把分类单独建表，而不是在 Book 里存一个字符串？
    1. 避免重复：同一个分类名在每本书里都存一遍，容易写错（"技术" / "技术类"）
    2. 方便管理：改分类名只改一行，所有书自动生效
    3. 方便统计：可以轻松算出每个分类下有多少本书
    4. 数据一致性：数据库层面保证一本书只能关联一个真实存在的分类

改完模型后必须执行：
    python manage.py makemigrations
    python manage.py migrate
"""

from django.db import models


class Category(models.Model):
    """图书分类。"""

    # unique=True：分类名不能重复，数据库会加唯一索引
    name = models.CharField("分类名称", max_length=50, unique=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        # 查询时默认按 id 升序（先建的在前）
        ordering = ["id"]
        # 后台显示的名字（单数/复数）
        verbose_name = "分类"
        verbose_name_plural = "分类"

    def __str__(self):
        # 打印对象时显示分类名，方便调试和 admin 后台
        return self.name


class Book(models.Model):
    """一本图书。"""

    title = models.CharField("书名", max_length=120)
    # blank=True 表示表单可以不填；数据库里会存空字符串
    author = models.CharField("作者", max_length=80, blank=True)

    # DecimalField 适合存金额，避免浮点数精度问题（0.1 + 0.2 != 0.3）
    # max_digits=8：总共最多 8 位；decimal_places=2：小数点后 2 位
    price = models.DecimalField("价格", max_digits=8, decimal_places=2, default=0)

    # PositiveIntegerField：只能存 >= 0 的整数，库存不会变成负数
    stock = models.PositiveIntegerField("库存", default=0)

    # ForeignKey：外键，表示「多本书属于一个分类」
    #   related_name="books"：反向查询用，category.books.all() 拿到该分类下所有书
    #   on_delete=models.PROTECT：分类下还有书时，禁止删除该分类（防止数据孤儿）
    #   null=True, blank=True：允许「未分类」的书
    category = models.ForeignKey(
        Category,
        verbose_name="分类",
        related_name="books",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        # 最新添加的书排在最前面
        ordering = ["-id"]
        verbose_name = "图书"
        verbose_name_plural = "图书"

    def __str__(self):
        return self.title
