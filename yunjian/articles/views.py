#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/7 22:25
# @Author  : Listash
# @File    : views.py
# @Software: PyCharm

from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, UpdateView, DetailView, DeleteView
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, HttpResponse, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from yunjian.articles.models import Article
from yunjian.articles.forms import ArticleMDEditorFrom, CommentForm
from yunjian.helpers import AuthorRequiredMixin
from yunjian.notifications.models import Notification
from yunjian.notifications.views import notification_handler
from yunjian.articles.models import Comment


class ArticleListView(ListView):
    """已发布的文章列表"""
    model = Article
    paginate_by = 6
    context_object_name = "articles"
    template_name = "articles/article_list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        # 获取标签
        context['popular_tags'] = Article.objects.get_counted_tags()
        return context

    def get_queryset(self):
        return Article.objects.get_published()


class TagListView(ArticleListView):
    """含有tag标签的文章列表"""
    def get_queryset(self):
        tag = self.kwargs['tag']
        return Article.objects.get_contains_tag(tag)


class ColumnListView(ArticleListView):
    """获取相关栏目的文章列表"""
    def get_queryset(self):
        column_title = self.kwargs['column']
        return Article.objects.filter(column__title=column_title).all()


class DraftListView(ArticleListView):
    """草稿箱文章列表"""
    def get_queryset(self):
        return Article.objects.filter(user=self.request.user).get_drafts()


# get 请求，保存在缓存数据库中1小时, 会保留上次缓存的用户信息，导致其他用户创建文章时csrf验证失败，所以不适合在此处使用，应该在模板中使用cache
# @method_decorator(cache_page(60 * 60), name='get')
class ArticleCreateView(LoginRequiredMixin, CreateView):
    """发表文章"""
    model = Article
    form_class = ArticleMDEditorFrom
    template_name = "articles/article_create.html"
    message = "您的文章已创建成功！"

    # 重写form_valid方法，将登录的用户传递给表单实例
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """成功后跳转"""
        messages.success(self.request, self.message)  # 消息传递给下一次请求
        return reverse_lazy("articles:list")

    # 自定义初始化方法，如定期发送公告，或发送有规律的内容时可以使用
    # def get_initial(self):
    #     initial = super().get_initial()
    #     # 写入初始化逻辑
    #     return initial


class ArticleDetailView(DetailView):
    """文章详情"""
    model = Article
    template_name = "articles/article_detail.html"

    def get_object(self, queryset=None):
        """
        当有其他用户对文章发表者进行评论时，会触发消息通知，在文章的发表者点击相关的消息通知跳转到文章页时，应该
        将文章的所有评论消息标记为已读
        使用GenericRelation时，导入Notification报错，尚不清楚原因，所以使用ContentType来获取通知
        """
        # article = Article.objects.select_related('user').get(slug=self.kwargs['slug'])
        article = super().get_object()
        if self.request.user == article.user:
            content_type_id = ContentType.objects.get(model='article').id
            # 获取文章通知
            notifications = Notification.objects.filter(content_type_id=content_type_id, object_id=article.id)
            # 标记通知为已读
            notifications.mark_all_as_read()
        # 访问量+1
        article.view_nums += 1
        article.save(update_fields=['view_nums'])
        return article

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        # 使用self.get_object()还会触发一次上面的‘标记为已读’功能，所以先写成这样
        article = Article.objects.select_related('user').get(slug=self.kwargs['slug'])
        comments = Comment.objects.filter(article=article)
        comment_form = CommentForm()
        context['comments'] = comments
        context['comment_form'] = comment_form
        return context


class ArticleEditView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    """编辑文章"""
    model = Article
    message = "您的文章已编辑成功！"
    form_class = ArticleMDEditorFrom
    template_name = "articles/article_update.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """
        成功后跳转,编辑完文章后，要将该文章缓存cache_page清空，需要获取redis缓存中的该文章的key，将该key删除，怎么获取呢，
        感觉需要看看生成key的源码(待解决）
        """

        messages.success(self.request, self.message)  # 消息传递给下一次请求
        return reverse_lazy("articles:article", kwargs={"slug": self.get_object().slug})


class ArticleDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    model = Article
    template_name = "articles/article_confirm_delete.html"
    pk_url_kwarg = "pk"
    success_url = reverse_lazy('articles:list')


@login_required
def post_comment(request, article_id, parent_comment_id=None):
    """发表评论"""
    article = get_object_or_404(Article, id=article_id)

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.article = article
            new_comment.user = request.user

            # 二级及以下评论
            if parent_comment_id:
                parent_comment = Comment.objects.get(id=parent_comment_id)
                # 若回复层数超过二级，则转化为二级
                new_comment.parent_id = parent_comment.get_root().id
                new_comment.reply_to = parent_comment.user
                new_comment.save()
                # 二级及以下评论的消息通知
                notification_handler(request.user, parent_comment.user, 'R', parent_comment)
                return JsonResponse({'code': '200 OK'})

            # 保存一级评论
            new_comment.save()
            # 一级评论的消息通知
            notification_handler(request.user, article.user, 'C', article)
            return redirect('articles:article', slug=article.slug)
        else:
            return HttpResponse('表单内容有误，请重新填写！')
    # GET请求用于生成回复栏
    elif request.method == 'GET':
        comment_form = CommentForm()
        context = {
            'comment_form': comment_form,
            'article_id': article_id,
            'parent_comment_id': parent_comment_id
        }
        return render(request, 'articles/reply_comment.html', context)
    else:
        return HttpResponse("仅接受GET/POST请求")
