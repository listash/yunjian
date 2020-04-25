from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "yunjian.users"
    verbose_name = "用户"

    def ready(self):
        try:
            import yunjian.users.signals  # noqa F401
        except ImportError:
            pass
