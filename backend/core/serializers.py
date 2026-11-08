"""
序列化器（Serializer）—— 模型和 JSON 之间的翻译官。

为什么需要它？
    数据库里存的是 Python 对象（Note 实例），
    但前端只能收发 JSON 文本。
    Serializer 负责双向转换：
        前端 JSON  ->  校验  ->  Note 对象  ->  存数据库（反序列化）
        Note 对象  ->  转成字典  ->  JSON 响应（序列化）

ModelSerializer 是快捷写法：只要指定模型和字段，
DRF 会自动帮你生成校验规则（比如 title 必填、最长 100 字）。
"""

from rest_framework import serializers

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    """Note 模型的序列化器。"""

    class Meta:
        # 指定要序列化的模型
        model = Note
        # 接口里要出现哪些字段；"__all__" 表示全部
        fields = ["id", "title", "content", "created_at"]
        # 只读字段：客户端不能自己设置，由数据库自动生成
        # id 自增、created_at 自动取当前时间，所以设为只读
        read_only_fields = ["id", "created_at"]
