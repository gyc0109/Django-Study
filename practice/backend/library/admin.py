"""admin 后台配置。

注册模型后，就能在 http://127.0.0.1:8001/admin/ 里
用网页可视化管理分类和图书，比直接敲 SQL 方便得多。

前提：先创建一个超级管理员账号
    python manage.py createsuperuser
"""

# admin 是 Django 自带的后台管理模块。
from django.contrib import admin

# 导入要注册的模型。
from .models import Book, Category


# ------------------------------------------------------------
# @admin.register(Category) 是装饰器写法，等价于：
#     admin.site.register(Category, CategoryAdmin)
# 作用：把「模型」和「后台配置类」绑定起来。
# ------------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """分类在 admin 后台的展示方式。"""

    # 列表页显示哪些列（第一个参数也可以写成 "id"）。
    # created_at 是自动生成的，这里只读展示，不能在列表里直接编辑。
    list_display = ["id", "name", "created_at"]

    # 右上角搜索框按哪些字段搜索。
    # 底层是 LIKE 查询；字段越多，搜索越慢，只放常用的即可。
    search_fields = ["name"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """图书在 admin 后台的展示方式。"""

    # 列表页的列。
    # category 会显示 __str__ 的返回值（分类名），而不是冷冰冰的 id。
    list_display = ["id", "title", "author", "price", "stock", "category", "created_at"]

    # 右侧筛选栏：可以按分类快速过滤。
    # 分类很多时会把所有分类列出来，数据量大的项目要慎用。
    list_filter = ["category"]

    search_fields = ["title", "author"]

    # 允许在列表页直接修改库存（适合快速补货），
    # 不用点进详情页再保存。
    # 注意：list_editable 里的字段不能同时出现在 list_display_links 中，
    # 否则 Django 会报配置错误。
    list_editable = ["stock"]
