"""
core/models.py —— 数据模型层（Model）

# ==========================================================================
# 一、这是干什么的？
# ==========================================================================
# Django 的核心卖点就是 ORM（Object Relational Mapping，对象关系映射）。
# 它让你用「Python 类」描述「数据库表」，从此写业务代码时基本不用手写 SQL。
#
# 三组一一对应关系（记住这张表，Django 就懂一半了）：
#
#     Python 世界                  数据库世界
#     ------------------------     -----------------------------
#     class Note(models.Model)  -> 一张表，表名默认 core_note
#     类里的一个类属性           -> 表里的一个字段（列）
#     Note(...) 创建一个实例     -> 一行数据（INSERT）
#     Note.objects.all()         -> SELECT * FROM core_note
#     note.title = "x"; save()   -> UPDATE core_note SET title='x' ...
#     note.delete()              -> DELETE FROM core_note ...
#
# 表名为什么叫 core_note？
#   Django 的默认命名规则是「app 名 + 下划线 + 模型名小写」。
#   这个文件在 core/ 目录下（core 是一个 app），模型叫 Note，
#   所以表名 = core_note。可以用 Meta.db_table 自定义，但没必要。
#
# ==========================================================================
# 二、改完这个文件之后要做什么？（新手最容易忘的一步）
# ==========================================================================
# 只改 Python 代码，数据库是不会自动变的！必须执行两条命令：
#
#   python manage.py makemigrations core
#       # 对比「模型现在的样子」和「上次迁移记录的样子」，
#       # 把差异写成一个 Python 文件放到 core/migrations/ 下。
#       # 这个文件只是一份「改造说明书」，此时数据库还没动。
#
#   python manage.py migrate
#       # 真正把说明书执行到数据库（这里是 MySQL），
#       # 执行 CREATE TABLE / ALTER TABLE 等 SQL。
#
# 记忆口诀：makemigrations 是「写计划」，migrate 是「执行计划」。
#
# ==========================================================================
# 三、这个文件为什么这么短？
# ==========================================================================
# 因为这是 project1（入门演示项目），只需要一张最简单的表。
# 更复杂的用法（外键 ForeignKey、多对多、索引、约束）请看
# practice/backend/library/models.py，那里有 Book + Category 双表演示。
# ==========================================================================
"""

# models 是 Django 自带的模块，里面全是字段类型：
# models.CharField / models.TextField / models.DateTimeField / models.IntegerField ...
# 每个字段类型最终都会翻译成 MySQL 的具体列类型（VARCHAR / LONGTEXT / DATETIME ...）
from django.db import models


class Note(models.Model):
    """一条笔记。

    继承 models.Model 是所有模型的固定写法。
    Django 会自动给这个类补上：
      - id 字段（BigAutoIncrement 主键），你不需要自己声明；
      - objects 管理器（用于查询，如 Note.objects.filter(...)）；
      - save() / delete() 等方法。
    """

    # ----------------------------------------------------------------------
    # 字段 1：标题（短字符串）
    # ----------------------------------------------------------------------
    # models.CharField = 变长字符串，对应 MySQL 的 varchar。
    # ★ 必须给 max_length，否则 Django 启动时直接报错
    #   （因为 MySQL 的 varchar 必须指定长度，Django 不猜）。
    #
    # 第一个位置参数 "标题" 是 verbose_name（人类可读名），作用有三：
    #   1. admin 后台的表单标签显示「标题」而不是 title；
    #   2. DRF 报错时会说「标题：该字段是必填项。」；
    #   3. 生成的迁移文件和数据库注释里也会带这个信息。
    # 如果你不写，Django 会拿属性名 title 自动转成 "title"。
    #
    # ★ 默认行为：这个字段 NOT NULL 且必填。
    #   CharField 默认 blank=False、null=False，意思是
    #   - null=False -> 数据库层面不许存 NULL；
    #   - blank=False -> 表单/序列化器层面「必须传」。
    #   所以前端不传 title 时，POST 会直接返回 400。
    title = models.CharField("标题", max_length=100)

    # ----------------------------------------------------------------------
    # 字段 2：内容（长文本）
    # ----------------------------------------------------------------------
    # models.TextField = 不限长度的文本，对应 MySQL 的 longtext。
    # 它和 CharField 的区别：
    #   CharField  -> varchar(n)，有长度上限，适合标题/姓名/短描述；
    #   TextField  -> longtext，理论上能存 4GB，适合正文/富文本/日志。
    #
    # ★ 反直觉点：blank=True 只影响「校验」，不影响「数据库是否允许 NULL」。
    #   blank=True  -> 表单/序列化器可以不传（DRF 里就是不 required）
    #   null=True   -> 数据库列允许 NULL
    #   这里只写了 blank=True，没写 null=True，所以：
    #   - 你可以 POST {"title": "x"} 不传 content，能过校验；
    #   - 但数据库里存的不是 NULL，而是一个空字符串 ""，
    #     因为 TextField 的默认值就是空字符串。
    #
    # ★ 什么时候才需要 null=True？只有「NULL 和空字符串含义不同」时才需要，
    #   比如「分数」字段：0 分和「没考」是两回事，那种场景用 null=True。
    #   字符串字段一般只加 blank=True，这是 Django 官方推荐做法。
    content = models.TextField("内容", blank=True)

    # ----------------------------------------------------------------------
    # 字段 3：创建时间
    # ----------------------------------------------------------------------
    # models.DateTimeField 对应 MySQL 的 datetime 列。
    #
    # auto_now_add=True 的含义（★ 极易和 auto_now 搞混）：
    #   auto_now_add=True -> 只在「第一次创建」时自动填当前时间，之后就再也不变；
    #   auto_now=True     -> 每次 save() 都刷新为当前时间（适合「最后修改时间」）。
    #
    # 因为设了 auto_now_add，这个字段有三个连带效果：
    #   1. 你在代码里给它赋值也没用，save() 时会被覆盖；
    #   2. 它在序列化器里自动变成 read_only（客户端传了也被忽略）；
    #   3. 数据库里 NOT NULL。
    #
    # ★ 时区：Django 存进数据库的是 UTC 时间（settings.USE_TZ=True 时），
    #   返回给前端时 DRF 会转成 ISO 8601 格式并带时区偏移，
    #   例如 "2026-11-08T10:30:00+08:00"。所以前端拿到的时间看起来是对的，
    #   但如果你直接去 MySQL 里查，看到的可能是差了 8 小时的 UTC 时间。
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        """Meta 是「元信息」内部类：用来配置模型的额外行为，不产生字段。

        常见可配置项：
          ordering        默认排序
          db_table        自定义表名
          verbose_name    后台显示的单数名
          verbose_name_plural  后台显示的复数名
          indexes         索引
          constraints     数据库级约束（如唯一联合约束）
          unique_together 联合唯一（旧写法，新版本推荐 constraints）
        """

        # 默认排序：按 id 倒序，即「最新的笔记排在最前面」。
        # 负号 = 降序（DESC），不加负号 = 升序（ASC）。
        #
        # ★ 这个 ordering 会带来两个重要影响：
        #   1. Note.objects.all() 生成的 SQL 自带 ORDER BY id DESC，
        #      所以你不写 order_by 也是有顺序的；
        #   2. DRF 的分页如果没指定排序，会因为「顺序不稳定」而出现
        #      「第 2 页又出现第 1 页的数据」这种诡异现象。有了默认排序就不会。
        ordering = ["-id"]

    def __str__(self):
        """定义「打印这个对象时显示什么」。

        不写这个方法，print(note) 会得到 <Note: Note object (1)>，
        在 admin 后台的关联下拉框里也全是这种看不懂的东西。

        写了之后变成 <Note: 我的第一条笔记>，调试和后台都好用很多。
        """
        return self.title
