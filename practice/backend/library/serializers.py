"""序列化器（Serializer）—— 模型对象和 JSON 之间的「翻译官」。

为什么需要它？
    数据库里存的是 Python 对象（Book / Category 实例），
    但前端只能收发 JSON 文本，两边「语言」不通，必须有人翻译。

两个方向（务必分清）：
    序列化（读）  ：Book 对象      -> Python 字典 -> JSON 响应
    反序列化（写）：前端 JSON     -> 校验         -> 模型对象 -> 存数据库

ModelSerializer 是「快捷写法」：
    只要告诉它「用哪个模型、要哪些字段」，
    它会根据模型字段自动生成对应的序列化字段和基础校验规则
    （例如 title 必填、最长 120 字、price 是小数……），
    不用像普通 Serializer 那样一个字段一个字段手写。
"""

# rest_framework.serializers 里既有 Serializer 基类，也有各种字段类型
# （IntegerField、SerializerMethodField……）和 ValidationError。
from rest_framework import serializers

# 导入本 app 的模型：序列化器要围绕它们工作。
# 这里用「相对导入」：.models 表示「同一个包（library）下的 models.py」。
from .models import Book, Category


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器：负责分类的读和写。"""

    # ------------------------------------------------------------
    # 这一个字段不是数据库里的列，而是「临时算出来的」。
    #
    # source="books.count" 的意思：
    #   books 是模型里 ForeignKey 的 related_name（反向管理器）；
    #   .count 会调用它的 count()，翻译成 SQL 就是 SELECT COUNT(*) ...
    #   所以每个分类都会多一条 COUNT 查询（分类多时是 N+1，进阶优化见文档）。
    #
    # read_only=True：
    #   只出现在响应里，客户端提交这个字段会被忽略。
    #   原因：book_count 是统计结果，不能让客户端随便写。
    # ------------------------------------------------------------
    book_count = serializers.IntegerField(source="books.count", read_only=True)

    class Meta:
        """告诉 DRF：用哪个模型、暴露哪些字段、哪些字段只读。"""

        model = Category

        # 接口里出现的字段清单（顺序就是 JSON 里的顺序）。
        # 数据库列：id / name / created_at
        # 计算字段：book_count
        fields = ["id", "name", "book_count", "created_at"]

        # 只读字段：客户端不能自己设置它们。
        #   id        -> 数据库自增，客户端不可能知道
        #   created_at -> auto_now_add，由 Django 自动填
        # 如果客户端硬传这两个字段，DRF 会直接忽略，不会报错。
        read_only_fields = ["id", "created_at"]


class BookSerializer(serializers.ModelSerializer):
    """图书序列化器：负责图书的读和写。"""

    # ------------------------------------------------------------
    # 前端列表里想直接显示「技术」这样的分类名，
    # 但写数据时只需要传分类 id（category 字段）。
    # 所以额外加一个只读的计算字段 category_name。
    #
    # SerializerMethodField 的规则：
    #   它会去找名为 get_<字段名> 的方法（这里是 get_category_name），
    #   并把方法的返回值放进 JSON。
    # ------------------------------------------------------------
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "price",
            "stock",
            "category",       # 写：传分类 id（外键在 JSON 里就是 id）
            "category_name",  # 读：返回分类名称（人类可读）
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_category_name(self, obj):
        """把 category 外键翻译成分类名称。

        参数 obj：当前正在被序列化的 Book 实例。
        返回：
            有分类 -> 分类名（例如「技术」）
            无分类 -> 固定字符串「未分类」，避免前端显示 null
        """
        # obj.category 可能是 None（模型里 null=True），所以要先判断再取 .name。
        return obj.category.name if obj.category else "未分类"

    def validate_price(self, value):
        """字段级校验：价格不能为负数。

        DRF 的校验顺序（简化版）：
            1. 字段类型转换（to_internal_value）
            2. 字段自带校验器（例如 max_digits / decimal_places）
            3. validate_<字段名>（也就是这个方法）
            4. validate（整个对象的联合校验）
        只要在这里 raise ValidationError，DRF 会自动返回 400，
        并把错误信息放进 {"price": ["价格不能为负数"]}。
        """
        if value < 0:
            raise serializers.ValidationError("价格不能为负数")
        # 校验通过必须把值 return 回去，否则该字段会变成 None。
        return value

    def validate_stock(self, value):
        """字段级校验：库存不能为负数（理论上）。

        实际情况要说明白：
            模型的 stock 是 PositiveIntegerField，
            ModelSerializer 自动给它加了 min_value=0 的校验器。
            这个校验在第 2 步（字段自带校验器）就执行了，
            负数根本走不到这里，所以接口看到的是 DRF 默认提示
            「请确保该值大于或者等于 0。」，而不是下面这句中文。

        那这个方法还有用吗？
            有。如果以后把模型字段换成普通 IntegerField，
            这段中文提示就会生效。保留它是为了「多一层业务校验」，
            同时也演示 validate_<字段名> 的写法。
        """
        if value < 0:
            raise serializers.ValidationError("库存不能为负数")
        return value
