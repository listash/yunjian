#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/10 21:17
# @Author  : Listash
# @File    : urls.py
# @Software: PyCharm
from django.urls import path

from yunjian.qa import views
app_name = 'qa'
urlpatterns = [
    path("", views.UnansweredQuestionView.as_view(), name="unanswer_q"),
    path("answered/", views.AnsweredQuestionView.as_view(), name="answer_q"),
    path("indexed/", views.QuestionListView.as_view(), name="all_q"),
    path("ask-question/", views.CreateQuestionView.as_view(), name="ask_question"),
    path("question-detail/<int:pk>/", views.QuestionDetailView.as_view(), name="question_detail"),
    path("propose-answer/<int:question_id>/", views.CreateAnswerView.as_view(), name="propose_answer"),
    path("answer/vote/", views.answer_vote, name="answer_vote"),
    path("question/vote/", views.question_vote, name="question_vote"),
    path("accept-answer/", views.accept_answer, name="accept_answer"),
]
