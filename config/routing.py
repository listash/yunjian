from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from yunjian.messager.consumers import MessagesConsumer
from yunjian.notifications.consumers import NotificationsConsumer


# self.scope['type']获取协议类型
# self.scope['url_route']['kwargs']['username']获取url中的关键字参数
application = ProtocolTypeRouter({
    # 普通的HTTP请求不需要我们手动在这里添加，框架会自动加载
    # 'http': views
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path('ws/notifications/', NotificationsConsumer),
                path('ws/<str:username>/', MessagesConsumer),
            ])
        )
    )
})

# AuthMiddlewareStack用于Websocket认证，集成了CookieMiddleware, SessionMiddleWare, AuthMiddleWare,兼容Django认证系统
# OriginValidator和AllowedHostsOriginValidator可以防止通过WebSocket进行CSRF攻击
# OriginValidator需要手动添加需要访问的源站，AllowedHostsOriginValidator可以读取Django的settings.py中的ALLOWED_HOSTS配置


