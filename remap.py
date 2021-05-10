#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-

import subprocess
import re
import hashlib
import os
import shlex
import xml.etree.ElementTree as ET
from os.path import isfile
from pysqlcipher import dbapi2 as sqlite
import json
import urllib2
from xml.dom.minidom import parseString
import requests
import sys
import time
import configparser
import traceback
from PIL import Image
import baidu
import redis
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import pathlib

from material import getKey,cpFile,decrypt,query,queryOne,cpImg,tailorImg

pool = redis.ConnectionPool(host="r-bp1t0exes9r7r83dnspd.redis.rds.aliyuncs.com", port=6379, password='Bn0ayanQ1^gIjlsD', decode_responses=True,db=4)
# pool = redis.ConnectionPool(host="127.0.0.1", port=6379,  decode_responses=True,db=4)
reids = redis.Redis(connection_pool=pool)
redis = redis.Redis(connection_pool=pool)

redis_key = "has:remap:list"
has_done_key = "done:remap:list"

def re_map(msg_id,dbName):
    start_id = int(msg_id) - 10
    end_id = int(msg_id) + 10
    sql = "select * from main.message WHERE type =3 and talker='9990246678@chatroom' and msgId >=" + str(start_id) + " and msgId<="+ str(end_id)+";"
    data = query(dbName, sql)
    for i in range(0, len(data)):
        tailorImg(decodeDbName, data[i][0], data[i][1])
    redis.lpush(has_done_key,msg_id)

if __name__ == "__main__":
    uin = '-1763681588'
    imei = '861795037451492'
    fileName = 'reMap_EnMicroMsg_' + str(imei) + 'reMap.db'
    decodeDbName = 'reMap_decrypted_' + fileName

    # cpFile(uin, str(fileName))
    #
    # key = getKey(uin, imei)
    #
    # r = decrypt(key, fileName, decodeDbName)

    list_len = redis.llen(redis_key)

    for i in range(0,list_len):
        msg_id = redis.rpop(redis_key)
        print "但前处理" + str(msg_id)
        re_map(msg_id,decodeDbName)




