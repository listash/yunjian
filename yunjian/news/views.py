from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, DeleteView
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse_lazy

from yunjian.news.models import News
from yunjian.helpers import ajax_required, AuthorRequiredMixin


class NewsListView(LoginRequiredMixin, ListView):
    """首页动态"""
    Model = News
    paginate_by = 10  # url中的?page
    # page_kwarg = "p"  # ?page改为?p
    # context_object_name = 'news_list'  # 默认是 '模型类名_list' 或者是 'object_list'
    # ordering = "-created_at"  # 多条件的排序可以使用元组实现(x, y)
    template_name = "news/news_list.html"  # 默认是 '模型类名_list.html'

    # def get_ordering(self):  #
    #     """自定义排序时使用，比如推荐系统"""
    #     pass

    # def get_paginate_by(self, queryset):
    #     """自定义分页"""
    #     pass

    def get_queryset(self):
        """自定义queryset，比如进行过滤"""
        # 优化查询，select_related()用于ForeignKey或OneToOneField，而prefetch_related()用于多对多字段或GenericForeignKey
        return News.objects.filter(reply=False).select_related('user', 'parent').prefetch_related('liked')

    def get_context_data(self, *, object_list=None, **kwargs):
        """添加额外的上下文"""
        context = super().get_context_data()
        context['active'] = 'all'
        return context


class MyNewsListView(NewsListView):

    def get_queryset(self):
        return News.objects.filter(reply=False, user=self.request.user).\
            select_related('user', 'parent').prefetch_related('liked')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context['active'] = 'my_news'
        return context


# class NewsDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
#     """
#     删除状态,DeleteView每次删除一个对象，不能批量删除，此处如果不加上AuthorRequiredMixin来验证操作者是否是
#     原作者，那么任意用户都可以构造包含主键的url来删除动态
#     """
#     model = News
#     template_name = "news/news_confirm_delete.html"
#     # slug_url_kwarg = "slug"  # 通过url传入要删除对象的主键id，默认值是slug
#     # pk_url_kwarg = "pk"  # 通过url传入要删除对象的主键id，默认值是pk
#     success_url = reverse_lazy("news:list")  # 删除之后要跳转到的路径, reverse_lazy可以在项目URLConf未加载前使用

class NewsDeleteView(LoginRequiredMixin, View):
    """ajax删除动态"""
    def post(self, request):
        news_id = request.POST.get('news')
        news = News.objects.get(uuid=news_id)

        if news.user == request.user:
            news.delete()
            return JsonResponse({'code': '200 OK'})


@login_required
@ajax_required
@require_http_methods(['POST'])
def post_news(request):
    """发送动态，AJAX POST请求"""
    post = request.POST.get("post").strip()
    if post:
        posted = News.objects.create(user=request.user, content=post)
        html = render_to_string("news/news_single.html", {"news": posted, "request": request})
        return HttpResponse(html)
    else:
        return HttpResponseBadRequest("内容不能为空！")


@login_required
@ajax_required
@require_http_methods(['POST'])
def like(request):
    """点赞/取消点赞，AJAX POST请求"""
    news_id = request.POST.get("news")
    news = News.objects.get(pk=news_id)
    # 点赞/取消点赞
    news.switch_like(request.user)
    # 点赞数
    return JsonResponse({"likes": news.liked_count()})


@login_required
@ajax_required
@require_http_methods(['GET'])
def get_thread(request):
    """返回动态的评论，AJAX GET请求"""
    news_id = request.GET.get("news")
    # 优化查询，注意select_related()要用在queryset后，所以在filter后面，或get前面
    news = News.objects.select_related('user').get(pk=news_id)
    news_html = render_to_string("news/news_single.html", {"news": news, "request": request})  # 源动态
    thread_html = render_to_string("news/news_thread.html",
                                   {"thread": news.get_thread().order_by('created_at'),
                                    "request": request})  # 源动态的评论
    return JsonResponse({
        "uuid": news_id,
        "news": news_html,
        "thread": thread_html
    })


@login_required
@ajax_required
@require_http_methods(['POST'])
def post_comment(request):
    """评论，AJAX POST请求"""
    post = request.POST.get("reply").strip()
    parent_id = request.POST.get("parent")
    parent = News.objects.get(pk=parent_id)
    if post:
        parent.reply_this(request.user, post)
        return JsonResponse({"comments": parent.comment_count()})
    else:
        return HttpResponseBadRequest("内容不能为空！")


@login_required
@ajax_required
@require_http_methods('POST')
def update_interactions(request):
    uuid = request.POST.get('id_value')
    news = News.objects.get(uuid=uuid)
    likes = news.liked_count()
    comments = news.comment_count()
    return JsonResponse({"likes": likes, "comments": comments})
