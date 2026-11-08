"""admin 后台配置。

注册后就能在 http://127.0.0.1:8001/admin/ 里管理分类和图书，
比直接改数据库方便得多。
"""

from django.contrib import admin

from .models import Book, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # 列表页显示哪些列
    list_display = ["id", "name", "created_at"]
    # 右侧搜索框按哪些字段搜索
    search_fields = ["name"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "author", "price", "stock", "category", "created_at"]
    # 右侧筛选器：可以按分类筛选
    list_filter = ["category"]
    search_fields = ["title", "author"]
    # 列表页可以直接改库存（适合快速补货）
    list_editable = ["stock"]
