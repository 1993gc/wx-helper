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
# import cv2

reload(sys)

sys.setdefaultencoding("utf-8")

base = 'pro_url'
# base = 'dev_url'
# base = 'local_url'
config = configparser.ConfigParser()
config.read(os.getcwd()+"/config.ini")

save_max_id_url = config.get(base, "save_max_id")
get_max_id_url = config.get(base, "get_max_id")
save_url = config.get(base, "save_url")

pool = redis.ConnectionPool(host="r-bp1t0exes9r7r83dnspd.redis.rds.aliyuncs.com", port=6379, password='Bn0ayanQ1^gIjlsD', decode_responses=True,db=4)
# pool = redis.ConnectionPool(host="127.0.0.1", port=6379,  decode_responses=True,db=4)
reids = redis.Redis(connection_pool=pool)

redis_key = "mobile:material:info"
has_done_key = "done:mobile:material:info"

def getUin():

    cmd = 'adb shell su 0 cat /data/data/com.tencent.mm/shared_prefs/system_config_prefs.xml'
    args = shlex.split(cmd)
    info = subprocess.check_output(args)
    root = ET.fromstring(info)
    for child in root:
        if child.attrib['name'] == 'default_uin':
            return child.attrib['value']


def getKey(uin, imei):
    raw = str(imei) + str(uin)
    return hashlib.md5(str(raw).encode('utf8')).hexdigest()[0:7]


def cpFile(uin, fileName):
    path = hashlib.md5(str('mm' + str(uin)).encode('utf8')).hexdigest()
    # cmd = '/opt/AndroidSDK/platform-tools/adb shell su 0 cp /data/data/com.tencent.mm/MicroMsg/' + \
    #       path + '/EnMicroMsg.db /sdcard/' + fileName
    cmd = 'adb shell su 0 cp /data/data/com.tencent.mm/MicroMsg/' + \
          path + '/EnMicroMsg.db /sdcard/' + fileName

    # exit(123)
    args = shlex.split(cmd)
    suc = subprocess.call(args)
    if suc == 0:
        # cmd = '/opt/AndroidSDK/platform-tools/adb pull /sdcard/' + fileName + ' ./' + fileName
        cmd = 'adb pull /sdcard/' + fileName + ' ./' + fileName
        args = shlex.split(cmd)
        ret = subprocess.call(args)
        if ret != 0:
            exit(255)
    del_cmd = 'adb shell su 0 rm -rf  /sdcard/' + fileName
    del_args = shlex.split(del_cmd)
    suc = subprocess.call(del_args)


def decrypt(key, dbName, decodeDbName):
    if isfile(decodeDbName):
        os.unlink(decodeDbName)
    conn = sqlite.connect(dbName)
    c = conn.cursor()
    # try:
    c.execute("PRAGMA key = '" + key + "';")
    c.execute("PRAGMA cipher_use_hmac = OFF;")
    c.execute("PRAGMA cipher_page_size = 1024;")
    c.execute("PRAGMA kdf_iter = 4000;")
    c.execute("ATTACH DATABASE '" + decodeDbName + "' AS db KEY '';")
    c.execute("SELECT sqlcipher_export('db');")
    c.execute("DETACH DATABASE db;")
    c.close()
    status = 1
    # except Exception as e:
    #     print e
    #     c.close()
    #     status = 0
    return status


def query(dbName, sql):
    conn = sqlite.connect(dbName)
    c = conn.cursor()
    try:
        rows = c.execute(sql)
        return c.fetchall()
        c.close()
    except Exception as e:
        print e.message
        c.close()

def queryOne(dbName, sql):
    conn = sqlite.connect(dbName)
    c = conn.cursor()
    try:
        rows = c.execute(sql)
        return c.fetchone()
        c.close()
    except Exception as e:
        print e.message
        c.close()


def get_last_time():
    req = urllib2.Request(url=get_max_id_url)

    res = urllib2.urlopen(req)
    res = res.read()

    result = json.loads(res)

    return result['data']['msg_time']


def post_data(url, data):
    req = requests.post(url=url, data=data)
    result = json.loads(req.content)
    return result

def cpImg(imgInfo):

    bigImgPath = imgInfo[4]
    if "SERVERID:" in bigImgPath:
        print "图片未点击"
        return False
    path = '/sdcard/tencent/MicroMsg/7ec622c2555abbd60cabd1c2201082ef/image2/'+ str(bigImgPath[0:2]) + "/" + bigImgPath[2:4] + "/" + str(bigImgPath)

    cmd = 'adb shell su 0 cp  ' + path  + ' /sdcard/'+ str(bigImgPath)

    # exit(123)
    args = shlex.split(cmd)
    suc = subprocess.call(args)
    if suc == 0:
        # cmd = '/opt/AndroidSDK/platform-tools/adb pull /sdcard/' + fileName + ' ./' + fileName
        cmd = 'adb pull /sdcard/' +  str(bigImgPath) + ' ./'
        args = shlex.split(cmd)
        ret = subprocess.call(args)
        if ret != 0:
            return False
    del_cmd = 'adb shell su 0 rm -rf  /sdcard/' +  str(bigImgPath)
    del_args = shlex.split(del_cmd)
    suc = subprocess.call(del_args)
    return True

def tailorImg(decodeDbName,msg_id,msgSvrId):

    # msgSvrId = 5879835802442584638
    sql = "SELECT * FROM main.ImgInfo2 WHERE msgSvrId = '"+ str(msgSvrId)+"'"

    data = queryOne(decodeDbName, sql)
    if data is None:
        return False
    bigImgPath = data[4]

    if reids.sismember(has_done_key, msg_id):
        print "已处理，跳过识别"
        return True

    cpImg(data)
    path = "./"+ str(bigImgPath)
    file_exists = os.path.exists(path)
    if not file_exists:

        print str(msg_id) + "文件不存在"
        return False
    ext = pathlib.Path(path).suffix
    if ext != '.jpg':
        print "文件格式不对"
        return  False
    img = Image.open(path)
    img_size = img.size
    img_w = img_size[0]
    img_h = img_size[1]

    if img_w < 500:
        left_px = 50
    elif img_w < 800:
        left_px = 100
    else:
        left_px = 120

    if img_h<=800:
        top_px = 100
    elif img_h<=1500:
        top_px = 150
    else:
        top_px = 200
    region = img.crop((left_px, top_px, img_w, img_h))
    new_img_path = os.path.splitext(bigImgPath)[0]+"_S"+str(left_px)+os.path.splitext(bigImgPath)[1]


    region.save(new_img_path,quality=75,subsampling=0)

    location_info = baidu.get_location( new_img_path)
    # print(location_info)
    # print("img_path ===> " + new_img_path)
    # print(msgSvrId)
    theEnd =['了解更多','了多','了解公众号','了众号','公众号','0了解更多','0了解公众号',"人关注"]

    if "error_code" in location_info:
        print "接口调用受限"
        # print( location_info['error_msg'])
        return False
    index = 0
    is_err_index = False
    content_start_index = 0
    content_end_index = 0
    for i in location_info['words_result']:
        words = i['words'].encode('utf-8')
        # print words ,len(words)

        # print(words=='广告'.encode('utf-8'))
        if index == 0:
            if len(words)==6:
                if words=='广告'.encode('utf-8') or words=='廣告'.encode("utf-8"):
                    index = location_info['words_result'].index(i)
                    content_start_index = index + 1
                    gz_name = location_info['words_result'][index-1]['words'].encode('utf-8')
            elif len(words)<6:
                if words=='告'.encode('utf-8') or words=='广'.encode('utf-8'):
                    index = location_info['words_result'].index(i)
                    content_start_index = index + 1
                    gz_name = location_info['words_result'][index - 1]['words'].encode('utf-8')
            else :
                if words =='广告√'.encode('utf-8') or words =='廣告√'.encode('utf-8'):
                    index = location_info['words_result'].index(i)
                    content_start_index = index + 1
                    gz_name = location_info['words_result'][index - 1]['words'].encode('utf-8')
                if ('广告'.encode('utf-8') in words) and len(location_info['words_result'][index+1]['words'].encode('utf-8'))==12:
                    content_start_index = index
                    gz_name = location_info['words_result'][index + 1]['words'].encode('utf-8')
                    is_err_index = True
        # print(index)
        if len(words)<=15:
            if  words in theEnd and index>0:
                content_end_index = location_info['words_result'].index(i)
                content_list = location_info['words_result'][content_start_index:content_end_index]
        else:
            for i_end in theEnd:

                if i_end.encode("utf-8") in words and index>0 and content_start_index>0:
                    content_end_index = location_info['words_result'].index(i)
                    if content_end_index<content_start_index:
                        continue
                    else:
                        content_list = location_info['words_result'][content_start_index:content_end_index]
                if content_end_index == 0:
                    content_list = location_info['words_result'][content_start_index:]
    # print(content_list)

    if index>0:
        chinese = "".join(i['words'].encode('utf-8') for i in content_list)
        if is_err_index:
            chinese =  chinese.replace("广告"+gz_name,"")
        chinese = chinese.replace("了解更多","")
        chinese = chinese.replace("了解公众号","")
        reids.zadd( redis_key,{str(gz_name)+"$$"+str(chinese):int(msg_id)})
        reids.sadd(has_done_key,int(msg_id))
        print "处理完成  删除图片"
        os.remove(new_img_path)
        os.remove(path)
    # print(chinese)
    # exit(1)

def addToBaiDuSim(breif,file_path):

    # options = {}
    # options["tags"] = "100,11"
    add_res = baidu.add_sim_img(file_path, breif)
    return add_res

if __name__ == "__main__":


    try:
        f = open(os.getcwd()+'/save_log.log', 'a+')
        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + " 开始执行 " + "\n")
        #
        last_time = get_last_time()

        uin = '-1763681588'

        imei = '861795037451492'


        fileName = 'EnMicroMsg_' + str(imei) + '.db'
        decodeDbName = 'decrypted_' + fileName
        cpFile(uin, str(fileName))

        key = getKey(uin, imei)
        r = decrypt(key, fileName, decodeDbName)



        sql = "SELECT * FROM main.message WHERE type in ('49','3') and talker='9990246678@chatroom' and createTime >" + str(last_time) + " order by msgId desc ;"

        print  sql
        # last_time = 1614938315000
        # sql = "SELECT * FROM main.message WHERE type in ('49','3') and talker='9990246678@chatroom' and createTime >=" + str(last_time) + " order by msgId asc limit 1000"

        # cpImg()
        data = query(decodeDbName, sql)

        if len(data)==0:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + " 执行结束，暂无数据 " + "\n")
            exit("暂无记录")
        max_id = data[0][0]
        last_msg_time = data[0][6]

        dic = {"id": max_id,"msg_time": last_msg_time}
        # print max_id


        all_data = []

        try:
            for i in range(0, len(data)):

                # print("msgId ===> "+str(data[i][0]))
                # print("msgSvrId ===> "+str(data[i][1]))
                # print("type ===> "+str(data[i][2]))
                msg_id = data[i][0]

                if data[i][2]==3:
                    tailorImg(decodeDbName,data[i][0], data[i][1])
                else:

                    xml = data[i][8].encode("utf-8")
                    xml = xml.replace("wxid_13f0egsr6ru921:", '').strip()
                    xml = xml.replace("wxid_jq3prlkeex4n22:", '').strip()
                    xml = xml.replace("wxid_de2alqsqjd5j22:", '').strip()
                    xml = xml.replace("wxid_vjnfbpldlo4x22:", '').strip()
                    xml = re.sub(u"[\x00-\x08\x0b-\x0c\x0e-\x1f]+", u"", xml)


                    xml_dom = parseString(xml)
                    tree = ET.fromstring(xml)
                    elementobj = xml_dom.documentElement
                    if elementobj.getElementsByTagName('title')[0].firstChild:
                        title = elementobj.getElementsByTagName('title')[0].firstChild.data.encode("utf-8")
                    else:
                        title = ''
                    ctype = elementobj.getElementsByTagName('type')[0].firstChild.data.encode("utf-8")

                    if ctype=="19":
                        print "不是分享链接,跳过"
                        continue

                    if elementobj.getElementsByTagName('des')[0].firstChild:
                        des = elementobj.getElementsByTagName('des')[0].firstChild.data.encode("utf-8")
                    else:
                        des = ''

                    if elementobj.getElementsByTagName('url')[0].firstChild:
                        url = elementobj.getElementsByTagName('url')[0].firstChild.data.encode("utf-8")
                    else:
                        url = ''

                    timeStamp = float(data[i][6]/1000)
                    timeArray = time.localtime(timeStamp)
                    msg_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

                    canvasPageXml = elementobj.getElementsByTagName('canvasPageXml')
                    if not canvasPageXml[0].firstChild:
                        print("未知类型的分享链接")
                        continue
                    pageXml = parseString(canvasPageXml[0].firstChild.data.encode("utf-8"))
                    pageobj = pageXml.documentElement
                    nickname = pageobj.getElementsByTagName('nickname')[0].firstChild.data.encode("utf-8")
                    content_list = pageobj.getElementsByTagName('content')

                    for j in range(0, len(content_list)):
                        if pageobj.getElementsByTagName('content')[j].firstChild != None:
                            if len(unicode(
                                    pageobj.getElementsByTagName('content')[j].firstChild.data.encode("utf-8").replace('\n','').replace('\r', '').replace(' ', ''))[0:300]) > 250:
                                share_desc = unicode(pageobj.getElementsByTagName('content')[j].firstChild.data.encode("utf-8").replace('\n', '').replace('\r', '').replace(' ', ''))[0:300]

                                break
                    data_dict = {"title": title, "des": des, "url": url, "nickname": nickname,"share_desc": share_desc.encode("utf-8"),"msg_time": msg_time, "msg_id": msg_id}
                    all_data.append(data_dict)
        except Exception as e:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + str(msg_id) + " 保存异常： " + str(e.message) + "\n")
            # print xml
            print
            'traceback.print_exc():', traceback.print_exc()
            print
            'traceback.format_exc():\n%s' % traceback.format_exc()

        # save_url = 'http://kanban.com/material/mobileMaterial'
        # print len(all_data)
        data_slice = [all_data[x:x + 100] for x in range(0, len(all_data), 100)]
        # print(len(data_slice))
        num = 0
        try:
            for i in range(0, len(data_slice)):
                num += len(data_slice[i])
                ret = post_data(save_url, data=json.dumps(data_slice[i]))
                if not ret['status']:
                    f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + str(i) + " 保存失败： " + ret['message'] + "\n")
                f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + str(i) + " 保存成功： " + ret['message']+ "\n")
                print "当前已处理" + str(num)+" 条数据"
        except Exception as e:

            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + str(msg_id) + " 保存异常： " + str(e.message)+ "\n")

        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + " 执行结束 " + "\n")
    except Exception as e:
        print e
        # print os.getcwd()
        print 'traceback.print_exc():', traceback.print_exc()
        print 'traceback.format_exc():\n%s' % traceback.format_exc()
        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + " 执行异常： " + str(e) +os.getcwd()+ "\n")
    res = post_data(save_max_id_url, {"id": max_id, "msg_time": last_msg_time})
