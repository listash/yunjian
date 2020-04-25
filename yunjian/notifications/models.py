from __future__ import unicode_literals
import uuid

from django.utils.encoding import python_2_unicode_compatible
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core import serializers
from django.utils.safestring import mark_safe

from slugify import slugify

from yunjian.users.models import User
from yunjian.articles.models import Article, Comment
from yunjian.qa.models import Answer
from yunjian.qa.models import Question


@python_2_unicode_compatible
class NotificationQuerySet(models.query.QuerySet):

    def unread(self):
        return self.filter(unread=True).select_related('actor', 'recipient')

    def read(self):
        return self.filter(unread=False).select_related('actor', 'recipient')

    def mark_all_as_read(self, recipient=None):
        """全部标记为已读， 可以传入接收者参数"""
        qs = self.unread()
        if recipient:
            qs = qs.filter(recipient=recipient)
        return qs.update(unread=False)

    def mark_all_as_unread(self, recipient=None):
        qs = self.read()
        if recipient:
            qs = qs.filter(recipient=recipient)
        return qs.update(unread=True)

    def get_most_recent(self, recipient=None):
        """获取最近的5条通知"""
        qs = self.unread()[:5]
        if recipient:
            qs = qs.filter(recipient=recipient)[:5]
        return qs

    def serialize_latest_notifications(self, recipient=None):
        """序列化最近5条未读通知，可以传入接收者参数"""
        qs = self.get_most_recent(recipient)
        notification_dic = serializers.serialize('json', qs)
        return notification_dic


@python_2_unicode_compatible
class Notification(models.Model):
    NOTIFICATION_TYPE = (
        ('L', '赞了'),
        ('C', '评论了'),
        ('F', '收藏了'),
        ('P', '提出了问题'),
        ('A', '回答了'),
        ('W', '接受了您的回答'),
        ('R', '回复了'),
        ('I', '登录'),
        ('O', '退出'),
    )
    uuid_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, related_name="actor_notify",
                              on_delete=models.CASCADE, verbose_name="触发者")
    recipient = models.ForeignKey(User, related_name="recipient_notify",
                                  on_delete=models.CASCADE, blank=True, null=True,
                                  verbose_name="接收者")
    unread = models.BooleanField(default=True, verbose_name="未读")
    verb = models.CharField(max_length=1, choices=NOTIFICATION_TYPE, verbose_name="通知类型")
    slug = models.SlugField(max_length=80, null=True, blank=True, verbose_name="URL别名")
    created_at = models.DateTimeField(db_index=True, auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    content_type = models.ForeignKey(ContentType, related_name="notify_action_object",
                                     null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    action_object = GenericForeignKey()  # 或GenericForeignKey("content_type", "object_id")

    objects = NotificationQuerySet.as_manager()

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = verbose_name
        ordering = ("-created_at",)

    def __str__(self):
        if self.action_object:
            from yunjian.news.models import News
            # 文章一级评论通知，通知给文章的发表者
            if isinstance(self.action_object, Article):
                # 这里使用url的模板语句{% url 'articles:article' article.slug %}时会出现引号的冲突，暂时使用以下方法
                return mark_safe(f'<a href="/users/{self.actor.username}">{self.actor.get_profile_name()}</a> '
                                 f'{self.get_verb_display()} <a href="/articles/{self.action_object.slug}">'
                                 f'{self.action_object}</a>')
            # 文章的二级，三级回复，通知给父级评论的发表者，这里消息通知显示会有排版问题，因为评论是ckeditor的RichTextField，
            # 文本中包含HTML标签，不如将通知内容修改为“xx回复了您在文章xx中的评论”
            if isinstance(self.action_object, Comment):
                return mark_safe(f'<a href="/users/{self.actor.username}">{self.actor.get_profile_name()}</a> '
                                 f'{self.get_verb_display()} 您在文章<a href="/articles/{self.action_object.article.slug}">'
                                 f'{self.action_object.article}</a>中的评论')
            # 动态通知，点赞与评论，跳转的路由最好指向某条具体的动态，所以需要添加DetailView，目前先简化处理
            elif isinstance(self.action_object, News):
                return mark_safe(f'<a href="/users/{self.actor.username}">{self.actor.get_profile_name()}</a> '
                                 f'{self.get_verb_display()} <a href="/news/my-news/">'
                                 f'{self.action_object}</a>')
            # 问答通知，包括谁提出了问题，谁回答了你的问题，你接受了回答后的消息通知显示
            # 回答了问题
            elif isinstance(self.action_object, Question):
                return mark_safe(f'<a href="/users/{self.actor.username}">{self.actor.get_profile_name()}</a> '
                                 f'{self.get_verb_display()} <a href="/qa/question-detail/'
                                 f'{self.action_object.id}/">'
                                 f'{self.action_object}</a>')
            # 接受了回答
            elif isinstance(self.action_object, Answer):
                return mark_safe(f'<a href="/users/{self.actor.username}">{self.actor.get_profile_name()}</a> '
                                 f'{self.get_verb_display()} <a href="/qa/question-detail/'
                                 f'{self.action_object.question.id}/">'
                                 f'{self.action_object.question}</a>')
            return f'{self.actor.get_profile_name()} {self.get_verb_display()} {self.action_object}'
        return f'{self.actor.get_profile_name()}  {self.get_verb_display()}'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.slug:
            self.slug = slugify(f'{self.recipient} {self.uuid_id} {self.verb}')
        super().save()

    def mark_as_read(self):
        if self.unread:
            self.unread = False
            self.save()

    def mark_as_unread(self):
        if not self.unread:
            self.unread = True
            self.save()
