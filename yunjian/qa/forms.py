#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/11 21:05
# @Author  : Listash
# @File    : forms.py
# @Software: PyCharm
from django import forms

from yunjian.qa.models import Question, Answer


class QuestionMDForm(forms.ModelForm):
    status = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Question
        fields = ['title', 'content', 'tags', 'status']



class AnswerMDForm(forms.ModelForm):

    class Meta:
        model = Answer
        fields = ['content']
        labels = {'content': "我的回答："}
