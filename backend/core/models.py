from django.db import models


class Note(models.Model):
    title = models.CharField("标题", max_length=100)
    content = models.TextField("内容", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.title
