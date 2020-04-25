#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/20 12:20
# @Author  : Listash
# @File    : urls.py
# @Software: PyCharm

from django.urls import path

from yunjian.notifications import views
app_name = "notifications"
urlpatterns = [
    path("", views.NotificationUnreadListView.as_view(), name="unread"),
    path("mark-as-read/<str:slug>/", views.mark_as_read, name="mark_as_read"),
    path("mark-all-as-read/", views.mark_all_as_read, name="mark_all_as_read"),
    path("latest-notifications/", views.get_latest_notifications, name="latest_notifications"),
]
