from __future__ import unicode_literals
import uuid

from django.utils.encoding import python_2_unicode_compatible
from django.db import models

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from yunjian.users.models import User
from yunjian.notifications.views import notification_handler


@python_2_unicode_compatible
class News(models.Model):
    # 主键使用uuid，不能编辑要设置editable
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # 当设置为blank=True, null=True时，删除用户后用户的回答可以保留，on_delete=models.SET_NULL附表删除时，主表置空
    user = models.ForeignKey(User, verbose_name="用户", blank=True, null=True,
                             on_delete=models.SET_NULL, related_name="user_news")
    # 关联的父记录
    parent = models.ForeignKey("self", verbose_name="自关联", blank=True, null=True,
                               on_delete=models.CASCADE, related_name="thread")
    content = models.TextField(verbose_name="动态内容")
    # 多对多字段不需要设置blank=True, null=True
    liked = models.ManyToManyField(User, verbose_name="点赞用户", related_name="liked_news")
    # 当default为False时表示动态，当为True时为评论内容
    reply = models.BooleanField(verbose_name="是否为评论", default=False)
    created_at = models.DateTimeField(db_index=True, verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        verbose_name = "动态"
        verbose_name_plural = verbose_name
        # 注意是元组
        ordering = ("-created_at",)

    def __str__(self):
        return self.content

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert=False, force_update=False, using=None,
                     update_fields=None)

        # 提示有人更新了动态
        if not self.reply:
            channel_layer = get_channel_layer()
            payload = {
                'type': 'receive',  # 在动态保存后，把通知传递给notifications下consumers.py的receive方法
                'key': 'additional_news',
                'actor_name': self.user.username,
            }
            async_to_sync(channel_layer.group_send)('notifications', payload)

    def switch_like(self, user):
        """点赞或取消点赞"""
        # 如点赞过，则取消
        if user in self.liked.all():
            self.liked.remove(user)
        else:
            self.liked.add(user)
            # 通知楼主
            notification_handler(user, self.user, 'L', self, key="social_update", id_value=str(self.uuid))

    def get_parent(self):
        """返回自关联的上级记录或者本身"""
        if self.parent:
            return self.parent
        else:
            return self

    def reply_this(self, user, text):
        """
        回复首页的动态
        :param user: 登录的用户
        :param text: 回复的内容
        :return: None
        """
        parent = self.get_parent()
        News.objects.create(
            user=user,
            content=text,
            reply=True,
            parent=parent
        )
        notification_handler(user, parent.user, 'R', parent, id_value=str(parent.uuid), key="social_update")

    def get_thread(self):
        """获取关联到当前记录的所有记录"""
        # 1.获取当前记录的父记录
        parent = self.get_parent()
        # 2.获取该父记录的所有关联记录
        return parent.thread.all()

    def comment_count(self):
        """评论数量"""
        return self.get_thread().count()

    def liked_count(self):
        """点赞数量"""
        return self.liked.count()

    def get_likers(self):
        """所有点赞用户"""
        return self.liked.all()
