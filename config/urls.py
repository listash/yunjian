from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views import defaults as default_views
from yunjian.news.views import NewsListView

urlpatterns = [
    path("", NewsListView.as_view(), name="home"),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # User management
    path("users/", include("yunjian.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # 第三方应用
    path('mdeditor/', include('mdeditor.urls')),
    path("search/", include("haystack.urls")),
    # Your stuff: custom urls includes go here
    path("news/", include("yunjian.news.urls", namespace="news")),
    path("articles/", include("yunjian.articles.urls", namespace="articles")),
    path("qa/", include("yunjian.qa.urls", namespace="qa")),
    path("messages/", include("yunjian.messager.urls", namespace="messager")),
    path("notifications/", include("yunjian.notifications.urls", namespace="notifications")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
# 在生产环境下的配置
else:
    urlpatterns += [
        re_path("^static/(?P<path>.*)$", serve, {'document_root': settings.STATIC_ROOT}),
        re_path("^media/(?P<path>.*)$", serve, {'document_root': settings.MEDIA_ROOT})
    ]
