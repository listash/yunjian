#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/2/20 12:20
# @Author  : Listash
# @File    : consumers.py
# @Software: PyCharm
import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationsConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        """建立连接"""
        if self.scope['user'].is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add('notifications', self.channel_name)

            await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        """將接收到的消息返回給前端"""
        await self.send(text_data=json.dumps(text_data))

    async def disconnect(self, code):
        await self.channel_layer.group_discard('notifications', self.channel_name)
