from __future__ import unicode_literals
from random import randint

from django.utils.encoding import python_2_unicode_compatible
from django.db import models

from slugify import slugify
from taggit.managers import TaggableManager
from mdeditor.fields import MDTextField
from ckeditor.fields import RichTextField
from mptt.models import MPTTModel, TreeForeignKey

from yunjian.users.models import User


@python_2_unicode_compatible
class ArticleColunm(models.Model):
    """栏目，感觉作用与标签没有太大区别, 暂时没有加入用户的外键，这样会对定制有一定影响"""

    title = models.CharField(verbose_name='栏目名称', max_length=50)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '栏目'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class ArticleQuerySet(models.query.QuerySet):
    """自定义QuerySet,提高模型类的可用性"""
    def get_published(self):
        """获取已发表的文章"""
        return self.filter(status="P").select_related('user')

    def get_drafts(self):
        """返回草稿箱的文章"""
        return self.filter(status="D").select_related('user')

    def get_contains_tag(self, tag):
        """返回包含tag标签的文章"""
        return self.filter(tags__name__in=[tag])

    def get_counted_tags(self):
        """统计发表的文章中，各个标签(大于0的)出现的次数"""
        tag_dict = {}
        query = self.filter(status="P").annotate(tagged=models.Count('tags')).filter(tagged__gt=0)
        for obj in query:
            for tag in obj.tags.names():
                if tag not in tag_dict:
                    tag_dict[tag] = 1
                else:
                    tag_dict[tag] += 1
        return tag_dict.items()


@python_2_unicode_compatible
class Article(models.Model):
    STATUS = (("D", "Draft"), ("P", "Published"))
    title = models.CharField(verbose_name="标题", unique=True, max_length=255)
    top_image = models.ImageField(upload_to='articles_top_images/%Y/%m/%d/', verbose_name='文章顶部背景图',
                                  blank=True, null=True, help_text='建议规格1920x300')
    image = models.ImageField(upload_to='articles_images/%Y/%m/%d/', verbose_name='文章图片', blank=True, null=True)
    user = models.ForeignKey(User, verbose_name="作者", null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="user_article")
    slug = models.SlugField(verbose_name="（URL）别名", max_length=255)
    status = models.CharField(verbose_name="状态", choices=STATUS, default="D", max_length=1)
    view_nums = models.PositiveIntegerField(verbose_name='阅读次数', default=0)
    column = models.ForeignKey(ArticleColunm, verbose_name='所属栏目', null=True, blank=True,
                               related_name='article', on_delete=models.CASCADE)
    summary = models.TextField(verbose_name="文章摘要", max_length=200, help_text="请输入摘要，200字以内",
                               blank=True, null=True)
    content = MDTextField(verbose_name="文章内容")
    edited = models.BooleanField(verbose_name="是否可编辑", default=False)
    tags = TaggableManager(verbose_name="标签", help_text='多个标签请用英文标点逗号隔开')
    created_at = models.DateTimeField(db_index=True, verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    # 关联自定义查询集
    objects = ArticleQuerySet.as_manager()

    class Meta:
        verbose_name = "文章"
        verbose_name_plural = verbose_name
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # 当标题使用同音字时会报错，此处修改略简单，或许还不如创造一个唯一的字符串
        if not self.slug:
            self.slug = slugify(self.title) + '-' + str(randint(1, 100000))
        super().save()


@python_2_unicode_compatible
class Comment(MPTTModel):
    user = models.ForeignKey(User, verbose_name="评论者",
                             blank=True, null=True, related_name="user_comment",
                             on_delete=models.SET_NULL)
    article = models.ForeignKey(Article, verbose_name="评论的文章", related_name="article_comment",
                                on_delete=models.CASCADE)
    comment = RichTextField(verbose_name="评论内容")
    created_at = models.DateTimeField(db_index=True, verbose_name="创建时间", auto_now_add=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                            related_name="children_comments", verbose_name="父评论")
    reply_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE,
                                 verbose_name="被评论人", related_name="reply_comments")

    # 继承MPTTModel后的Meta
    class MPTTMETA:
        order_insertion_by = ['created_at']

    def __str__(self):
        return self.comment
