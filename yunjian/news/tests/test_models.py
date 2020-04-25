from test_plus.test import TestCase

from yunjian.news.models import News


class NewsModelsTest(TestCase):
    def setUp(self):
        self.user = self.make_user(username="user01")
        self.another_user = self.make_user(username="user02")
        self.first_news = News.objects.create(user=self.user, content="动态一")
        self.second_news = News.objects.create(user=self.user, content="动态二")
        self.third_news = News.objects.create(user=self.another_user, content="评论动态一",
                                              parent=self.first_news, reply=True)

    def test__str__(self):
        self.assertEqual(self.first_news.__str__(), "动态一")

    def test_switch_like(self):
        """测试点赞/取消赞功能，同时测试了liked_count与get_likers方法"""
        # 点赞
        self.first_news.switch_like(self.user)
        # 若user01给new1点赞，则点赞数必为1
        assert self.first_news.liked_count() == 1
        # 若user01给new1点赞，则user01必然在liked的集合中
        assert self.user in self.first_news.get_likers()
        # 取消点赞
        self.first_news.switch_like(self.user)
        assert self.first_news.liked_count() == 0
        assert self.user not in self.first_news.get_likers()

    def test_reply_this(self):
        """测试回复功能"""
        initial_count = News.objects.count()
        self.first_news.reply_this(self.another_user, "评论动态一")
        # 测试comment_count()方法
        assert self.first_news.comment_count() == 2
        assert News.objects.count() == initial_count + 1
        # 测试get_thread()方法
        assert self.third_news in self.first_news.get_thread()
