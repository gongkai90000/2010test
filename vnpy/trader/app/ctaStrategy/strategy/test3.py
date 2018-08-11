#!/usr/bin/python
# coding: UTF-8

"""This script parse stock info"""

import re
import urllib

dataUrl = "http://hq.sinajs.cn/list=RM1901"
stdout = urllib.urlopen(dataUrl)
stdoutInfo = stdout.read()
tempData = re.search('''(")(.+)(")''', stdoutInfo).group(2)
stockInfo = tempData.split(",")
print stockInfo[0].decode("gbk")

#http://blog.sina.com.cn/s/blog_4cf8aad30102eiog.html