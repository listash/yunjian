#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/18 23:28
# @Author  : Listash
# @File    : consumer.py
# @Software: PyCharm

import json

from channels.generic.websocket import AsyncWebsocketConsumer


class MessagesConsumer(AsyncWebsocketConsumer):
    """处理私信应用中的Websocket请求"""
    async def connect(self):
        if self.scope['user'].is_anonymous:
            # 未登录的用户拒绝连接
            await self.close()
        else:
            # 加入聊天组，用户名命名聊天组以保证频道内组名唯一，channel_name方法随机生成频道名以保证频道名唯一，也可以自己定义
            await self.channel_layer.group_add(self.scope['user'].username, self.channel_name)
            await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        """接受私信"""
        await self.send(text_data=json.dumps(text_data))

    async def disconnect(self, code):
        """离开聊天组"""
        await self.channel_layer.group_discard(self.scope['user'].username, self.channel_name)
