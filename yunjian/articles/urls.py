#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/7 22:38
# @Author  : Listash
# @File    : urls.py
# @Software: PyCharm

from django.urls import path

from yunjian.articles import views
app_name = "articles"
urlpatterns = [
    path("list/", views.ArticleListView.as_view(), name="list"),
    path("tag/list/<str:tag>/", views.TagListView.as_view(), name='tag_list'),
    path("column/list/<str:column>/", views.ColumnListView.as_view(), name='column_list'),
    path("drafts/", views.DraftListView.as_view(), name="drafts"),

    path("write-new-article/", views.ArticleCreateView.as_view(), name="write_new"),
    # 优化，缓存5min，但是由于缓存存在，文章重新编辑后的内容不能立即载入，如何在重新编辑后释放原来的缓存呢
    # path("<str:slug>/", cache_page(60 * 5)(views.ArticleDetailView.as_view()), name="article"),
    path("<str:slug>/", views.ArticleDetailView.as_view(), name="article"),
    path("edit/<int:pk>/", views.ArticleEditView.as_view(), name="edit_article"),
    path("delete/<int:pk>", views.ArticleDeleteView.as_view(), name='delete_article'),

    path('post-comment/<int:article_id>/', views.post_comment, name='post_comment'),
    path('post-comment/<int:article_id>/<int:parent_comment_id>/', views.post_comment, name='comment_reply'),


]
