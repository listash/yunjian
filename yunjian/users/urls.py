from django.urls import path

from yunjian.users import views
app_name = "users"
urlpatterns = [
    path("~redirect/", views.UserRedirectView.as_view(), name="redirect"),
    path("~update/", views.UserUpdateView.as_view(), name="update"),
    path("<str:username>/", views.UserDetailView.as_view(), name="detail"),
]
