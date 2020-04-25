from __future__ import unicode_literals

from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


# 此装饰器的目的是使python适应不同的版本，比如python2.x版本像python3一样可以处理unicode字符
@python_2_unicode_compatible
class User(AbstractUser):
    """自定义用户模型"""
    nickname = models.CharField(verbose_name="昵称", null=True, blank=True, max_length=255)
    position = models.CharField(verbose_name="职位", null=True, blank=True, max_length=50)
    introduction = models.TextField(verbose_name="简介", null=True, blank=True, default="")
    picture = models.ImageField(verbose_name="头像", null=True, blank=True, upload_to='profile_pics/')
    city = models.CharField(verbose_name="城市", null=True, blank=True, max_length=50)
    personal_url = models.URLField(verbose_name="个人链接", null=True, blank=True, max_length=255)
    weibo = models.URLField(verbose_name="微博链接", null=True, blank=True, max_length=255)
    zhihu = models.URLField(verbose_name="知乎链接", null=True, blank=True, max_length=255)
    github = models.URLField(verbose_name="Github链接", null=True, blank=True, max_length=255)
    linkedin = models.URLField(verbose_name="Linkedin链接", null=True, blank=True, max_length=255)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def get_profile_name(self):
        if self.nickname:
            return self.nickname
        return self.username
