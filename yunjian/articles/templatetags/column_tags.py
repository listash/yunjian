#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/4/13 15:37
# @Author  : Listash
# @File    : article_column.py
# @Software: PyCharm
# from django import template
#
# from yunjian.articles.models import ArticleColunm
#
# register = template.Library()
#
#
# @register.inclusion_tag('articles/results.html')
# def show_columns():
#     columns = ArticleColunm.objects.all()
#     return {'columns': columns}

from django import template
from yunjian.articles.models import ArticleColunm
register = template.Library()

@register.inclusion_tag('articles/results.html')
def show_columns():
    columns = ArticleColunm.objects.all()
    return {'columns': columns}
