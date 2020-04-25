from __future__ import unicode_literals
from random import randint
import uuid
from collections import Counter

from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey

import markdown
from slugify import slugify
from mdeditor.fields import MDTextField
from taggit.managers import TaggableManager

from yunjian.users.models import User


@python_2_unicode_compatible
class Vote(models.Model):
    uuid_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, verbose_name="用户", related_name='qa_vote', on_delete=models.CASCADE)
    value = models.BooleanField(verbose_name="赞同或反对", default=True)  # True为赞同
    # GenericForeignKey设置
    content_type = models.ForeignKey(ContentType, related_name='votes_on', on_delete=models.CASCADE)
    # 因为要关联的表的主键有的是str，有的是int类型，此处使用CharField
    object_id = models.CharField(max_length=255)
    vote = GenericForeignKey('content_type', 'object_id')  # 等同于GenericForeignKey()
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        verbose_name = '投票'
        verbose_name_plural = verbose_name
        # 联合唯一，表示某一用户只能给某一个模型类中的某一条数据点赞或踩
        unique_together = ('user', 'content_type', 'object_id')
        # SQL优化,设置联合唯一索引
        index_together = ('content_type', 'object_id')


@python_2_unicode_compatible
class QuestionQuerySet(models.query.QuerySet):
    """自定义QuerySet,提高模型类的可用性"""
    def get_answered(self):
        return self.filter(has_answer=True).select_related('user')

    def get_unanswered(self):
        return self.filter(has_answer=False).select_related('user')

    def get_counted_tags(self):
        tag_dict = {}
        query = self.all().annotate(tagged=models.Count('tags')).filter(tagged__gt=0)
        for obj in query:
            for tag in obj.tags.names():
                if tag not in tag_dict:
                    tag_dict[tag] = 1
                else:
                    tag_dict[tag] += 1
        return tag_dict.items()


@python_2_unicode_compatible
class Question(models.Model):
    STATUS = (("O", "Open"), ("C", "Close"), ("D", "Draft"))
    user = models.ForeignKey(User, verbose_name="提问者", related_name="q_author", on_delete=models.CASCADE)
    title = models.CharField(verbose_name="问题标题", unique=True, max_length=255,)
    slug = models.SlugField(verbose_name="URL别名", null=True, blank=True, max_length=255)
    status = models.CharField(verbose_name="问题状态", choices=STATUS, default="O", max_length=1)
    content = MDTextField(verbose_name="问题内容")
    has_answer = models.BooleanField(verbose_name="接受回答", default=False)  # 是否有满意的回答
    tags = TaggableManager(verbose_name="标签", help_text='多个标签请用英文标点逗号隔开')
    votes = GenericRelation(Vote, verbose_name="投票情况")  # 通过GenericRelation关联到vote表，不是实际的字段
    created_at = models.DateTimeField(db_index=True, verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    objects = QuestionQuerySet.as_manager()

    class Meta:
        verbose_name = "问题"
        verbose_name_plural = verbose_name
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        改写save方法，
        1.自定义slug后保存，
        2.保存后发送消息通知：某用户提出了什么问题，
        此功能待做，如果使用notification_handler,那么需要为每一个非提问者用户创建一条通知记录，对数据库的操作量有点大。
        所以需要想想其他办法
        """
        if not self.slug:
            self.slug = slugify(self.title) + '-' + str(randint(1, 100000))
        super().save()

    def get_markdown(self):
        return markdown.markdown(self.content,
                                 extensions=[
                                     'markdown.extensions.extra',
                                     'markdown.extensions.codehilite',
                                 ])

    def total_votes(self):
        """总投票数，赞成票数减去反对票数"""
        dic = Counter(self.votes.values_list('value', flat=True))
        return dic[True] - dic[False]

    def get_answers(self):
        """获取所有回答"""
        return Answer.objects.filter(question=self).select_related('user', 'question')

    def count_answers(self):
        """统计回答数量"""
        return self.get_answers().count()

    def get_upvoters(self):
        """统计支持的用户列表"""
        return [vote.user for vote in self.votes.filter(value=True).select_related('user').prefetch_related('vote')]

    def get_downvoters(self):
        """反对的用户列表"""
        return [vote.user for vote in self.votes.filter(value=False).select_related('user').prefetch_related('vote')]

    def get_accepted_answer(self):
        """获取被接受的回答"""
        return Answer.objects.select_related('user', 'question').get(question=self, is_answer=True)


@python_2_unicode_compatible
class Answer(models.Model):
    uuid_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, verbose_name="回答者", related_name="a_author", on_delete=models.CASCADE)
    # 问题删除后，答案也要删除
    question = models.ForeignKey(Question, verbose_name="问题", on_delete=models.CASCADE)
    content = MDTextField(verbose_name="回答内容")
    is_answer = models.BooleanField(verbose_name="回答是否被接受", default=False)
    votes = GenericRelation(Vote, verbose_name="投票情况")
    created_at = models.DateTimeField(db_index=True, verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        verbose_name = "回答"
        verbose_name_plural = verbose_name
        ordering = ("-is_answer", "-created_at")

    def __str__(self):
        return self.content

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        from yunjian.notifications.views import notification_handler
        notification_handler(self.user, self.question.user, "A", self.question)

    def get_markdown(self):
        return markdown.markdown(self.content,
                                 extensions=[
                                     'markdown.extensions.extra',
                                     'markdown.extensions.codehilite',
                                 ])

    def total_votes(self):
        """总投票数，赞成票数减去反对票数"""
        dic = Counter(self.votes.values_list('value', flat=True))
        return dic[True] - dic[False]

    def get_upvoters(self):
        """统计支持的用户列表"""
        return [vote.user for vote in self.votes.filter(value=True).select_related('user').prefetch_related('vote')]

    def get_downvoters(self):
        """反对的用户列表"""
        return [vote.user for vote in self.votes.filter(value=False).select_related('user').prefetch_related('vote')]

    def accept_answer(self):
        """获取被采纳的回答"""
        # 是被采纳的回答，对应问题的所有回答的is_answer设为False
        answer_set = Answer.objects.filter(question=self.question)
        answer_set.update(is_answer=False)
        # 再将本回答的is_answer设为True，保存
        self.is_answer = True
        self.save()
        # 将对应问题的has_answer设为True，保存
        self.question.has_answer = True
        self.question.save()
