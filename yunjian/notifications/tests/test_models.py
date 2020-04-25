#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/3/3 20:53
# @Author  : Listash
# @File    : test_models.py
# @Software: PyCharm
from test_plus.test import TestCase

from yunjian.news.models import News
from yunjian.notifications.models import Notification
from yunjian.notifications.views import notification_handler


class NotificationsModelsTest(TestCase):

    def setUp(self):
        self.user = self.make_user("user01")
        self.other_user = self.make_user("user02")
        # user01赞了user02
        self.first_notification = Notification.objects.create(
            actor=self.user,
            recipient=self.other_user,
            verb="L"
        )
        # user01评论了user02
        self.second_notification = Notification.objects.create(
            actor=self.user,
            recipient=self.other_user,
            verb="C"
        )
        # user02回答了user01
        self.third_notification = Notification.objects.create(
            actor=self.other_user,
            recipient=self.user,
            verb="A"
        )

    def test_return_values(self):
        """对象类型和返回值, 返回值使用mark_safe，尚未完善"""
        assert isinstance(self.first_notification, Notification)
        assert isinstance(self.second_notification, Notification)
        assert isinstance(self.third_notification, Notification)


    def test_return_unread(self):
        assert Notification.objects.unread().count() == 3
        assert self.first_notification in Notification.objects.unread()
        assert self.second_notification in Notification.objects.unread()
        assert self.third_notification in Notification.objects.unread()

    def test_mark_as_read_and_return(self):
        self.first_notification.mark_as_read()
        assert Notification.objects.read().count() == 1
        assert self.first_notification in Notification.objects.read()
        self.first_notification.mark_as_unread()
        assert Notification.objects.read().count() == 0

    def test_mark_all_as_read(self):
        Notification.objects.mark_all_as_read()
        assert Notification.objects.read().count() == 3
        Notification.objects.mark_all_as_unread(self.other_user)  # 通知接收者为self.other_user
        print(Notification.objects.read().count())
        assert Notification.objects.read().count() == 1
        Notification.objects.mark_all_as_unread()
        assert Notification.objects.unread().count() == 3
        Notification.objects.mark_all_as_read(self.other_user)
        assert Notification.objects.read().count() == 2

    @staticmethod
    def test_get_most_recent():
        assert Notification.objects.get_most_recent().count() == 3

    def test_notification(self):
        """单个通知"""
        Notification.objects.mark_all_as_read()
        obj = News.objects.create(
            user=self.user,
            content="内容示例",
            reply=True
        )
        notification_handler(self.other_user, self.user, "C", obj)  # other_user评论了user
        assert Notification.objects.unread().count() == 1
