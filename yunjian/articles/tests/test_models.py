#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/9 17:16
# @Author  : Listash
# @File    : test_models.py
# @Software: PyCharm

from test_plus.test import TestCase

from yunjian.articles.models import Article


class ArticleModelsTest(TestCase):
    """测试文章model"""
    def setUp(self):
        self.user = self.make_user()
        # 创建文章
        self.article_test_p = Article.objects.create(
            title="测试文章",
            user=self.user,
            content="文章内容...",
            status="P",

        )
        self.article_test_d = Article.objects.create(
            title="测试草稿",
            user=self.user,
            content="草稿内容...",

        )

    def test_object_instance(self):
        """测试实例对象是不是Article模型类"""
        self.assertIsInstance(self.article_test_p, Article)
        self.assertIsInstance(self.article_test_d, Article)

    def test_return_values(self):
        """测试返回值"""
        self.assertIn(self.article_test_p, Article.objects.get_published())
        self.assertIn(self.article_test_d, Article.objects.get_drafts())
        self.assertEqual(self.article_test_p.__str__(), "测试文章")
        self.assertEqual(Article.objects.get_published()[0].title, "测试文章")
