"""数据模型（Model）—— 用 Python 类描述数据库表。

Django 的 ORM（对象关系映射）帮我们省掉了手写 SQL：
    一个类（Category）      ->  数据库里的一张表（library_category）
    类里的一个属性（name）   ->  表里的一个字段（name 列）
    一个对象（category）     ->  表里的一行数据
    对象的属性（category.name）-> 某一行某一列的值

本项目有两张表，形成「一对多」关系：
    一个分类（Category）  ->  多本书（Book）
    一本书（Book）        ->  属于 0 个或 1 个分类

为什么要把分类单独建一张表，而不是在 Book 里直接存分类名字符串？
    1. 避免重复：同一分类名在每本书里都存一遍，改名字要改很多行，还容易写错
       （"技术" / "技术类" / "技术 " 会被当成三个不同分类）
    2. 方便管理：改分类名只改一行，所有书自动生效
    3. 方便统计：可以轻松算出「每个分类下有多少本书」
    4. 数据一致性：数据库层面保证一本书只能关联一个真实存在的分类

改完模型后必须执行两条命令，数据库才会真正变化：
    python manage.py makemigrations   # 生成迁移文件（记录「要改成什么样」）
    python manage.py migrate          # 把迁移真正执行到 MySQL
"""

# models 是 Django 提供的「模型工具箱」，里面全是字段类型：
# CharField（短字符串）、TextField（长文本）、DecimalField（金额）……
from django.db import models


class Category(models.Model):
    """图书分类表。

    表名规则：Django 默认用「app 名_模型名小写」，
    所以这个类对应的 MySQL 表叫 library_category。
    """

    # ------------------------------------------------------------
    # CharField：短字符串，对应数据库的 VARCHAR。
    # 必须指定 max_length，原因有两个：
    #   1. MySQL 的 VARCHAR 必须声明长度；
    #   2. Django 会在「保存前」就检查长度，超长直接报错，而不是等数据库拒绝。
    #
    # 第一个位置参数 "分类名称" 是 verbose_name（人类可读名）：
    #   - admin 后台的表单标签会显示它
    #   - 报错信息会用这个名字，例如「分类名称 不能为空」
    #
    # unique=True：这一列加唯一索引，数据库层面禁止两个分类同名。
    #   好处：即使两条请求同时提交同名分类，也只会成功一条（并发安全）。
    #   注意：一旦插入重复值，数据库会直接抛 IntegrityError。
    # ------------------------------------------------------------
    name = models.CharField("分类名称", max_length=50, unique=True)

    # ------------------------------------------------------------
    # DateTimeField：日期 + 时间，对应数据库的 DATETIME(6)。
    # auto_now_add=True 的含义：
    #   只在「第一次创建」时自动写入当前时间，之后再 save 也不会变。
    #   所以不需要在代码里手动赋值，Django 会替我们填。
    #   与之相对的是 auto_now=True（每次保存都刷新，适合「最后修改时间」）。
    # 注意：这个字段自动带 editable=False，admin 表单里看不到它。
    # ------------------------------------------------------------
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        """Meta 是「元信息」：配置这个模型的额外行为，不产生数据库字段。"""

        # 查询时默认按什么排序。
        # "id" 表示升序（先创建的在前）；前面加负号 "-id" 就是降序。
        # 注意：不写 ordering 时，MySQL 返回顺序是不保证的（可能随索引变化）。
        ordering = ["id"]

        # admin 后台里这个模型显示成什么名字。
        # verbose_name 是单数（「分类」），verbose_name_plural 是复数。
        # 中文没有复数变化，两个写一样即可；英文项目通常写 "Category"/"Categories"。
        verbose_name = "分类"
        verbose_name_plural = "分类"

    def __str__(self):
        """定义「打印对象时显示什么」。

        f"{category}"、admin 后台的下拉框、调试输出都会调用它。
        如果不写，会显示成 <Category: Category object (1)>，很难辨认。
        """
        return self.name


class Book(models.Model):
    """图书表（数据库表名：library_book）。"""

    # ------------------------------------------------------------
    # 书名：必填，最长 120 个字符。
    # 这里没有 blank=True，意味着「表单/接口层面也不允许为空」。
    # 注意区分两个概念（新手最容易混）：
    #   blank=True  -> 表单/接口校验允许为空（讲的是「验证」）
    #   null=True   -> 数据库列允许存 NULL（讲的是「存储」）
    # 对字符串字段一般只用 blank=True，不用 null=True：
    #   因为 Django 约定「空字符串」表示空，而不是 NULL，避免两种「空」并存。
    # ------------------------------------------------------------
    title = models.CharField("书名", max_length=120)

    # ------------------------------------------------------------
    # 作者：blank=True 表示可以不填。
    # 不填时数据库里存的是空字符串 ""（不是 NULL）。
    # ------------------------------------------------------------
    author = models.CharField("作者", max_length=80, blank=True)

    # ------------------------------------------------------------
    # 价格：用 DecimalField 而不是 FloatField。
    # 原因：浮点数有精度问题，0.1 + 0.2 在计算机里不等于 0.3；
    #       金额必须精确，所以用「定点小数」。
    #   max_digits=8     -> 总共最多 8 位数字（整数位 + 小数位）
    #   decimal_places=2 -> 其中小数占 2 位
    #   也就是说最大能存 999999.99
    # default=0：新建图书时如果不传价格，默认 0 元。
    #           也正因为有默认值，接口里 price 变成「非必填」。
    # ------------------------------------------------------------
    price = models.DecimalField("价格", max_digits=8, decimal_places=2, default=0)

    # ------------------------------------------------------------
    # 库存：PositiveIntegerField = 只允许 >= 0 的整数。
    # 它在数据库层会加 CHECK 约束（MySQL 8 支持），
    # 同时在 DRF 序列化器里会自动带一个 min_value=0 的校验器。
    # default=0：不传库存时默认 0。
    # ------------------------------------------------------------
    stock = models.PositiveIntegerField("库存", default=0)

    # ------------------------------------------------------------
    # 外键（ForeignKey）：表示「多本书属于一个分类」。
    # 参数逐个解释：
    #   Category                      -> 关联到哪个模型
    #   verbose_name="分类"            -> 后台/表单显示的中文名
    #   related_name="books"          -> 反向查询名：
    #                                    category.books.all() 拿到该分类下所有书
    #                                    （不写的话默认叫 book_set，可读性差）
    #   on_delete=models.PROTECT      -> 删除策略：分类下还有书时，禁止删除分类。
    #                                    其他常见值：
    #                                      CASCADE  级联删除（删分类顺带删书，危险！）
    #                                      SET_NULL 置空（需要 null=True）
    #                                      SET_DEFAULT 设为默认值
    #   null=True, blank=True         -> 允许「未分类」的书
    # 注意：数据库里实际列名是 category_id，存的是分类的主键 id。
    # ------------------------------------------------------------
    category = models.ForeignKey(
        Category,
        verbose_name="分类",
        related_name="books",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # 创建时间：同 Category.created_at，只在创建时自动写入。
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        """图书模型的元信息。"""

        # 按 id 降序：最新添加的书排在最前面（列表页第一页看到的就是最新的）。
        # 注意负号 "-" 表示降序，这是 Django 的固定写法。
        ordering = ["-id"]

        verbose_name = "图书"
        verbose_name_plural = "图书"

    def __str__(self):
        """后台和调试时显示书名，而不是一串无意义的内存地址。"""
        return self.title
