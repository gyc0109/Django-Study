"""
数据模型（Model）—— 用 Python 类描述数据库表。

Django 的 ORM（对象关系映射）让你不用手写 SQL：
    class Note(models.Model)  ->  数据库里的一张表 core_note
    类里的每个属性             ->  表里的一个字段
    一个 Note 对象             ->  表里的一行数据

改完模型后必须执行两条命令，数据库才会真正变化：
    python manage.py makemigrations   # 生成迁移文件（记录"要改成什么样"）
    python manage.py migrate          # 把迁移真正执行到 MySQL

本项目只有一张表：笔记表 Note。
"""

from django.db import models


class Note(models.Model):
    """一条笔记：标题 + 内容 + 创建时间。"""

    # CharField = 短字符串，必须指定 max_length。
    # 第一个参数 "标题" 是给后台/报错信息看的中文名（verbose_name）。
    title = models.CharField("标题", max_length=100)

    # TextField = 长文本，没有长度限制，适合存大段内容。
    # blank=True 表示表单里可以不填（但数据库字段本身仍非空，会存空字符串）。
    content = models.TextField("内容", blank=True)

    # DateTimeField = 日期时间。
    # auto_now_add=True：只在创建时自动写入当前时间，之后不再改变。
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        """Meta 是「元信息」，用来配置这个模型的额外行为。"""

        # 查询时的默认排序：按 id 倒序（最新的在最前面）。
        # 加负号表示降序，去掉负号就是正序。
        ordering = ["-id"]

    def __str__(self):
        """打印对象时显示什么，比如在 admin 后台和调试时。"""
        return self.title
