#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/7 23:26
# @Author  : Listash
# @File    : forms.py
# @Software: PyCharm

from django import forms
from django.core.exceptions import ValidationError

from yunjian.articles.models import Article, Comment


class ArticleMDEditorFrom(forms.ModelForm):
    status = forms.CharField(widget=forms.HiddenInput())  # 隐藏input标签
    edited = forms.BooleanField(widget=forms.HiddenInput(), initial=False, required=False)
    # 当使用ModelForm时，可以省略此句(省略后verbose_name生效，不需要设置labels'
    # content = MDTextFormField()

    class Meta:
        model = Article
        fields = ['title', 'column', 'top_image', 'image', 'summary', 'content', 'tags', 'status', 'edited']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}), # 自定义行数
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['comment']

    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if not comment.strip():
            raise ValidationError('内容不能为空！')
        return comment
