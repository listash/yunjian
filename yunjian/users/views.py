from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView, RedirectView, UpdateView
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _


User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    template_name = "users/user_detail.html"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user.username)
        context['moments_num'] = user.user_news.filter(reply=False).count()
        context['article_num'] = user.user_article.get_published().count()
        # 评论数·逻辑不严谨，目前不太关键
        context['comment_num'] = user.user_news.filter(reply=True).count() + user.user_comment.all().count()
        context['question_num'] = user.q_author.all().count()
        context['answer_num'] = user.a_author.all().count()
        # 互动数 = 动态点赞数+问答点赞数+评论数+私信用户数(双方都有接受和发送私信)
        tmp = set()
        # 我发送私信给多少不同的用户
        sent_users = user.sent_messages.all()
        for s in sent_users:
            tmp.add(s.recipient.username)
        # 我接收了多少用户的私信
        received_users = user.received_messages.all()
        for s in received_users:
            tmp.add(s.sender.username)

        context['interaction_num'] = \
            user.liked_news.all().count() + user.qa_vote.all().count() + context['comment_num'] + len(tmp)
        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):

    model = User
    template_name = "users/user_form.html"
    fields = ["nickname", "email", "picture", "introduction", "position", "city", "personal_url", "weibo",
              "zhihu", "github", "linkedin"]

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self, queryset=None):
        return User.objects.get(username=self.request.user.username)

    def form_valid(self, form):
        messages.add_message(
            self.request, messages.INFO, _("Infos successfully updated")
        )
        return super().form_valid(form)


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})
