from test_plus.test import TestCase


class TestUser(TestCase):
    def setUp(self):
        # def make_user(cls, username='testuser', password='password', perms=None)
        self.user = self.make_user()

    def test__str__(self):
        self.assertEqual(self.user.__str__(), "testuser")

    def test_get_absolute_url(self):
        self.assertEqual(self.user.get_absolute_url(), "/users/testuser/")

    def test_get_profile_name(self):
        assert self.user.get_profile_name() == "testuser"
        self.user.nickname = "zion"
        assert self.user.get_profile_name() == "zion"