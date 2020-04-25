# 因为不希望在测试views时走中间件,url路由，wsgi等流程，所以要使用RequestFactory
from django.test import RequestFactory
from test_plus.test import TestCase

from yunjian.users.views import UserRedirectView, UserUpdateView


class BaseUserTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = self.make_user()


class TestUserUpdateView(BaseUserTestCase):
    def setUp(self):
        super().setUp()
        self.view = UserUpdateView()
        # 模拟request请求
        request = self.factory.get('/fake-url/')
        request.user = self.user
        self.view.request = request

    def test_get_success_url(self):
        self.assertEqual(self.view.get_success_url(), f"/users/{self.user.username}/")

    def test_get_object(self):
        self.assertEqual(self.view.get_object(), self.user)


class TestUserRedirectView(BaseUserTestCase):
    def setUp(self):
        super().setUp()
        self.view = UserRedirectView()
        request = self.factory.get('/fake-url/')
        request.user = self.user
        self.view.request = request

    def test_get_redirect_url(self):
        self.assertEqual(self.view.get_redirect_url(), f"/users/{self.user.username}/")
