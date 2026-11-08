"""序列化器（Serializer）—— 模型对象和 JSON 之间的翻译官。

两个方向：
    序列化   ：Note/Book 对象  ->  Python 字典  ->  JSON 响应
    反序列化 ：前端 JSON      ->  校验          ->  模型对象  ->  存数据库

ModelSerializer 会根据模型自动生成字段和基础校验规则。
"""

from rest_framework import serializers

from .models import Book, Category


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器。"""

    # 额外加一个「该分类下有多少本书」的只读字段。
    # source="books.count" 会调用反向关联管理器 books 的 count()。
    # 注意：分类很多时这样会产生 N+1 查询，进阶优化见教学文档。
    book_count = serializers.IntegerField(source="books.count", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "book_count", "created_at"]
        # 这两个字段由数据库生成，客户端不能自己设置
        read_only_fields = ["id", "created_at"]


class BookSerializer(serializers.ModelSerializer):
    """图书序列化器。"""

    # 前端展示需要分类名，但写数据时只需要传分类 id。
    # SerializerMethodField 可以自定义返回值，这里顺便处理「未分类」。
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "price",
            "stock",
            "category",       # 写：传分类 id
            "category_name",  # 读：返回分类名称
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_category_name(self, obj):
        """obj 是当前 Book 实例。"""
        return obj.category.name if obj.category else "未分类"

    def validate_price(self, value):
        """自定义字段校验：价格不能为负数。

        DRF 的校验流程（简化）：
            to_internal_value -> 字段校验 -> validate_<字段名> -> validate
        抛 ValidationError 会自动返回 400。
        """
        if value < 0:
            raise serializers.ValidationError("价格不能为负数")
        return value

    def validate_stock(self, value):
        """库存同样不能为负数。

        模型字段 PositiveIntegerField 本身也会挡，
        但在这里校验能给出更友好的中文提示。
        """
        if value < 0:
            raise serializers.ValidationError("库存不能为负数")
        return value
