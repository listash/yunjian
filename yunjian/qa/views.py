#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/11 16:16
# @Author  : Listash
# @File    : views.py
# @Software: PyCharm

from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, DetailView

from yunjian.helpers import ajax_required
from yunjian.qa.models import Question, Answer
from yunjian.qa.forms import QuestionMDForm, AnswerMDForm
from yunjian.notifications.views import notification_handler


class QuestionListView(ListView):
    model = Question
    queryset = Question.objects.select_related('user')
    paginate_by = 5
    context_object_name = "questions"
    template_name = "qa/question_list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context['popular_tags'] = Question.objects.get_counted_tags()
        context['active'] = "all"
        return context


class AnsweredQuestionView(QuestionListView):

    def get_queryset(self):
        return Question.objects.get_answered()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        # context['popular_tags'] = Question.objects.get_answered().get_counted_tags()
        context['active'] = "answered"
        return context


class UnansweredQuestionView(QuestionListView):

    def get_queryset(self):
        return Question.objects.get_unanswered()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        # context['popular_tags'] = Question.objects.get_unanswered().get_counted_tags()
        context['active'] = "unanswered"
        return context


class CreateQuestionView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionMDForm
    message = "您的问题已经提交！"
    template_name = 'qa/question_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """成功后跳转"""
        messages.success(self.request, self.message)  # 消息传递给下一次请求
        return reverse_lazy("qa:unanswer_q")


class QuestionDetailView(DetailView):
    """问题详情页"""
    model = Question
    context_object_name = 'question'
    template_name = 'qa/question_detail.html'

    def get_queryset(self):
        return Question.objects.select_related('user').filter(pk=self.kwargs['pk'])


class CreateAnswerView(LoginRequiredMixin, CreateView):
    """回答问题"""
    model = Answer
    form_class = AnswerMDForm
    message = "您的回答已经提交！"
    template_name = 'qa/answer_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.question_id = self.kwargs['question_id']
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, self.message)
        return reverse_lazy("qa:question_detail", kwargs={"pk": self.kwargs['question_id']})


@login_required
@ajax_required
@require_http_methods(['POST'])
def question_vote(request):
    """给问题投票 AJAX POST请求"""
    question_id = request.POST.get("question")
    value = True if request.POST["value"] == "U" else False
    question = Question.objects.get(pk=question_id)
    users = question.votes.values_list('user', flat=True)  # 当前问题的所有投票用户

    # 如果用户赞/踩过，要继续点击上次点击的按钮执行取消点赞/踩的操作，那么就删除记录，这个方法虽然代码精简但是不利于标记状态
    # if request.user.pk in users and (question.votes.get(user=request.user).value == value):
    #     question.votes.get(user=request.user).delete()
    # else:
    #     question.votes.update_or_create(user=request.user, defaults={"value": value})

    # 1.用户首次操作，点赞/踩
    if request.user.pk not in users:
        question.votes.create(user=request.user, value=value)
        if value:
            voting = 1  # 首次点赞，结果为赞
        else:
            voting = -1  # 首次踩，结果为踩
    # 2.用户已经赞过，取消点赞或者变为踩

    elif question.votes.get(user=request.user).value:
        if value:
            question.votes.get(user=request.user).delete()
            voting = 0  # 中立
        else:
            question.votes.update_or_create(user=request.user, defaults={"value": value})
            voting = -1
    # 3.用户已经踩过，取消踩或变为点赞
    else:
        if value:
            question.votes.update_or_create(user=request.user, defaults={"value": value})
            voting = 1
        else:
            question.votes.get(user=request.user).delete()
            voting = 0

    return JsonResponse({"votes": question.total_votes(), "voting": voting})


@login_required
@ajax_required
@require_http_methods(['POST'])
def answer_vote(request):
    """
    之前使用answer.votes.update()方法报这个错误，
    django.db.utils.IntegrityError: (1062, "Duplicate entry '...' for key 'qa_vote.PRIMARY'")
    改为update_or_create()后解决，前端逻辑修改正确
    """
    # 获取ajax的post请求传递的answer.id
    answer_id = request.POST['answer']
    # 获取ajax传递的value值，转换为布尔值
    value = True if request.POST["value"] == "U" else False
    # 通过主键获取对应answer
    answer = Answer.objects.get(uuid_id=answer_id)
    # 获取answer对应的点赞/踩用户的主键组成的列表
    users = answer.votes.values_list('user', flat=True)  # <QuerySet [5]>以user的主键构成的QuerySet列表

    # 1.用户首次操作，点赞/踩
    if request.user.pk not in users:
        answer.votes.create(user=request.user, value=value)
        # 点赞
        if value:
            voting = 1  # voting=1为赞，-1为踩，0为中立
        # 踩
        else:
            voting = -1  # 首次踩，结果为踩
    # 2.用户已经赞过，取消点赞或者变为踩
    elif answer.votes.get(user=request.user).value:
        # 取消点赞
        if value:
            answer.votes.get(user=request.user).delete()
            voting = 0  # 中立
        # 踩
        else:
            answer.votes.update_or_create(user=request.user, defaults={"value": value})
            voting = -1
    # 3.用户已经踩过，取消踩或变为点赞
    else:
        # 点赞
        if value:
            answer.votes.update_or_create(user=request.user, defaults={"value": value})
            voting = 1
        # 取消踩
        else:
            answer.votes.get(user=request.user).delete()
            voting = 0

    return JsonResponse({"votes": answer.total_votes(), "voting": voting})


@login_required
@ajax_required
@require_http_methods(['POST'])
def accept_answer(request):
    """
    认可回答 AJAX POST请求
    已经被接受的回答不能被取消
    """
    answer_id = request.POST.get('answer')
    answer = Answer.objects.get(pk=answer_id)
    # 如果当前登录用户不是提问者，抛出权限拒绝错误，前端也进行过一次检验，可能没有必要做这一步
    if answer.question.user.username != request.user.username:
        raise PermissionDenied
    answer.accept_answer()

    # 发送通知给回答者
    notification_handler(request.user, answer.user, 'W', answer)

    return JsonResponse({"status": "true"})
