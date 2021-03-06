from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from yunjian.notifications.models import Notification


class NotificationUnreadListView(LoginRequiredMixin, ListView):

    model = Notification
    context_object_name = 'notification_list'
    template_name = 'notifications/notification_list.html'

    def get_queryset(self):
        return self.request.user.recipient_notify.unread()


@login_required()
def mark_all_as_read(request):
    """标为全部为已读"""
    redirect_url = request.GET.get("next")
    request.user.recipient_notify.mark_all_as_read()
    messages.add_message(request, messages.SUCCESS, f'用户{request.user.username}的所有通知标为已读')
    if redirect_url:
        return redirect(redirect_url)
    return redirect('notifications:unread')


@login_required
def mark_as_read(request, slug):
    """标记单条为已读"""
    redirect_url = request.GET.get("next")
    notification = get_object_or_404(Notification, slug=slug)
    notification.mark_as_read()
    messages.add_message(request, messages.SUCCESS, f'通知"{notification}"已标为已读')
    if redirect_url:
        return redirect_url(redirect_url)
    return redirect('notifications:unread')


@login_required
def get_latest_notifications(request):
    """最近的未读通知"""
    notifications = request.user.recipient_notify.get_most_recent()
    return render(request, 'notifications/most_recent.html',
                  {"notifications": notifications})


def notification_handler(actor, recipient, verb, action_object, **kwargs):
    """
    通知处理器
    :param actor:                     request.user对象
    :param recipient:                 User Instance 接收者实例
    :param verb:                      str 通知类型
    :param action_object:             Instance 动作对象的实例
    :param kwargs:                    Key, id_value等
    :return:                          None
    """
    if recipient.username == action_object.user.username and actor.username != recipient.username:
        key = kwargs.get('key', 'notification')
        id_value = kwargs.get('id_value', None)
        # 记录通知内容
        Notification.objects.create(
            actor=actor,
            recipient=recipient,
            verb=verb,
            action_object=action_object
        )

        channel_layer = get_channel_layer()
        payload = {
            'type': 'receive',
            'key': key,
            'actor_name': actor.username,
            'id_value': id_value,
        }
        async_to_sync(channel_layer.group_send)('notifications', payload)
