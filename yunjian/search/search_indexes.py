#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/27 2:12
# @Author  : Listash
# @File    : search_indexes.py
# @Software: PyCharm
import datetime

from haystack import indexes
from taggit.models import Tag

from yunjian.news.models import News
from yunjian.articles.models import Article
from yunjian.qa.models import Question
from yunjian.users.models import User


class ArticleIndex(indexes.SearchIndex, indexes.Indexable):
    """对Article模型类中部分字段建立索引"""
    text = indexes.CharField(document=True, use_template=True, template_name='search/articles_text.txt')

    def get_model(self):
        return Article

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(status="P", updated_at__lte=datetime.datetime.now())


class NewsIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, template_name='search/news_text.txt')

    def get_model(self):
        return News

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(reply=False, updated_at__lte=datetime.datetime.now())


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, template_name='search/users_text.txt')

    def get_model(self):
        return User

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(updated_at__lte=datetime.datetime.now())


class QuestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, template_name='search/question_text.txt')

    def get_model(self):
        return Question

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(updated_at__lte=datetime.datetime.now())


class TagsIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, template_name='search/tags_text.txt')

    def get_model(self):
        return Tag

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
