"""
core/serializers.py —— 序列化器层（Serializer）

# ==========================================================================
# 一、序列化器到底解决什么问题？
# ==========================================================================
# 数据库里躺的是 Python 对象（Note 实例），
# 但 HTTP 接口只能传「文本」，通常就是 JSON。
# 这两者之间必须有一个翻译官，它就是 Serializer。
#
# 它有两条工作路线，方向相反：
#
#   【反序列化】前端 JSON  ──►  校验  ──►  Note 对象  ──►  存进 MySQL
#       POST /api/notes/  {"title": "hi", "content": "..."}
#
#   【序列化】  Note 对象  ──►  Python dict  ──►  JSON 响应
#       GET  /api/notes/  [{"id": 1, "title": "hi", ...}]
#
# 序列化器还顺手干了三件事，所以它不只是「翻译」：
#   1. 校验：title 超长、类型不对、缺字段，都会返回 400 和中文错误；
#   2. 字段裁剪：模型有 10 个字段，接口可以只暴露 3 个（避免泄漏敏感数据）；
#   3. 只读保护：id / created_at 只允许读，客户端改了也不生效。
#
# ==========================================================================
# 二、为什么用 ModelSerializer 而不是 Serializer？
# ==========================================================================
# Serializer           —— 手写每个字段，完全自定义，啰嗦但灵活；
# ModelSerializer      —— 只要告诉它「用哪个模型 + 要哪些字段」，
#                         它自动生成字段类型、max_length、required 等规则。
#
# 本项目 99% 的场景用 ModelSerializer 就够了。
# ==========================================================================
"""

# rest_framework.serializers 里包含 Serializer / ModelSerializer / 各种字段类
from rest_framework import serializers

# 相对导入：同目录（core 包）下的 models.py
# 用 . 开头的好处是「不管这个包被放在哪里都能找到」，比硬写 core.models 更稳
from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    """Note 模型的序列化器。

    名字习惯叫 <模型名>Serializer。
    这里一个字段都没手写，全部由 ModelSerializer 根据 Note 模型自动推断：

        Note.title       CharField(max_length=100)  ->  serializers.CharField(required=True, max_length=100)
        Note.content     TextField(blank=True)      ->  serializers.CharField(required=False, allow_blank=True)
        Note.created_at  DateTimeField(auto_now_add)->  serializers.DateTimeField(read_only=True)
        Note.id          BigAutoField               ->  serializers.IntegerField(read_only=True)

    推断出来的校验规则和模型完全一致，所以前端传错参数时的报错也是中文的。
    """

    class Meta:
        """Meta 内部类：告诉 ModelSerializer「基于哪个模型、暴露哪些字段」。"""

        # ---- 基于哪个模型 ----
        # 序列化器会读取这个模型的所有字段定义（类型、长度、是否可空…）
        model = Note

        # ---- 接口里要出现哪些字段 ----
        # 顺序不重要（输出永远按这里列的顺序排，其实 DRF 会保持这个顺序）。
        # 也可以用 "__all__" 表示全部字段，但生产环境不推荐：
        # 万一以后模型加了 password 字段，__all__ 会直接把它暴露出去。
        # 显式列出字段是最安全的做法。
        fields = ["id", "title", "content", "created_at"]

        # ---- 只读字段：客户端传了也不生效 ----
        # id：数据库自增主键，让客户端指定会造成冲突（甚至能覆盖别人的数据）；
        # created_at：模型里设了 auto_now_add，赋值也会被覆盖，
        #             所以不如直接声明只读，语义更清晰。
        #
        # ★ read_only_fields 只对「ModelSerializer 自动推断的字段」生效。
        #   如果你手写了某个字段，要在字段上单独加 read_only=True。
        #
        # ★ 只读字段在 POST 时「不用传」，不是「不能传」——
        #   传了不会报错，只是被静默忽略。这一点常让新手困惑。
        read_only_fields = ["id", "created_at"]
