from django.test import Client
from test_plus.test import TestCase
from django.urls import reverse

from yunjian.news.models import News


class NewsViewsTest(TestCase):
    def setUp(self):
        # 创建2个用户
        self.user = self.make_user(username="user01")
        self.another_user = self.make_user(username="user02")

        # 创建2个客户端
        self.client = Client()
        self.another_client = Client()

        # 两个用户分别登陆
        self.client.login(username="user01", password="password")
        self.another_client.login(username="user02", password="password")

        # 创建3条news，user01发表两条动态，user02评论第1条动态
        self .first_news = News.objects.create(
            user=self.user,
            content="动态一"
        )
        self.second_news = News.objects.create(
            user=self.user,
            content="动态二"
        )
        self.third_news = News.objects.create(
            user=self.another_user,
            content="评论动态一",
            parent=self.first_news,
            reply=True
        )

    def test_news_list(self):
        """测试动态列表页功能"""
        response = self.client.get(reverse("news:list"))
        assert response.status_code == 200
        assert self.first_news in response.context['news_list']
        assert self.second_news in response.context['news_list']
        assert self.third_news not in response.context['news_list']

    def test_delete_view(self):
        """测试删除功能"""
        initial_count = News.objects.count()
        # 删除第二条动态
        response = self.client.post(reverse("news:delete_news", kwargs={"pk": self.second_news.pk}))
        assert response.status_code == 302
        assert News.objects.count() == initial_count - 1

    def test_post_news(self):
        """测试发表动态"""
        initial_count = News.objects.count()
        response = self.client.post(
            reverse("news:post_news"),
            {"post": "zion强无敌"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",   # 表示发送AJAX request请求
        )
        assert response.status_code == 200
        assert News.objects.count() == initial_count + 1

    def test_like(self):
        """测试点赞"""
        response = self.client.post(
            reverse("news:like_post"),
            {"news": self.first_news.pk},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert response.status_code == 200
        assert self.first_news.liked_count() == 1
        assert self.user in self.first_news.get_likers()
        assert response.json()["likes"] == 1

    def test_get_thread(self):
        """测试获取评论"""
        response = self.client.get(
            reverse("news:get_thread"),
            {"news": self.first_news.pk},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert response.status_code == 200
        assert response.json()['uuid'] == str(self.first_news.pk)
        assert "动态一" in response.json()["news"]
        assert "评论动态一" in response.json()["thread"]

    def test_post_comment(self):
        """测试发表评论"""
        response = self.client.post(
            reverse("news:post_comment"),
            {"reply": "评论动态二", "parent": self.second_news.pk},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        assert response.status_code == 200
        assert response.json()['comments'] == 1
