#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
# @Time    : 2020/4/1 8:34
# @Author  : Listash
# @File    : get_remainder.py
# @Software: PyCharm
from django import template

register = template.Library()


@register.filter
def get_remainder(num):
    remainder = int(num) % 10
    return remainder
