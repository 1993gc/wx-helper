# -*- coding:utf-8 -*-
import subprocess
import hashlib
import os
import re
import socket
import shlex
import xml.etree.ElementTree as ET

import requests
import json
import time
import telnetlib
from pysqlcipher3 import dbapi2 as sqlite


def check_devices():
    cmd = 'adb devices'
    args = shlex.split(cmd)
    ret = subprocess.call(args)
    return ret

def check_root():
    cmd = 'adb root'
    args = shlex.split(cmd)
    info = subprocess.call(args)
    return info





def get_uin():
    return '-1763681588'
    cmd = 'adb shell su 0 cat /data/data/com.tencent.mm/shared_prefs/system_config_prefs.xml'
    args = shlex.split(cmd)
    info = subprocess.check_output(args).decode('utf-8')

    print(type(info))
    print(GetMiddleStr(info,'xml ',''))
    exit()
    print(re.sub('enter main '+GetMiddleStr(xml_str,'<?xml','>')+" /dev/null",'',xml_str))
    exit(12)
    root = ET.fromstring(xml_str)
    for child in root:
        if child.attrib['name'] == 'default_uin':
            uin = child.attrib['value']
            break
    if uin == "0":
        print("当前手机未登录微信,请登录")
        time.sleep(3)
        win32gui.EnumWindows(handle_window, None)
    else:
        return uin

def GetMiddleStr(content,startStr,endStr):
    patternStr = r'%s(.+?)%s'%(startStr,endStr)
    p = re.compile(patternStr,re.IGNORECASE)
    m= re.match(p,content)
    if m:
        return m.group(1)

def get_imeia():
    imei = subprocess.getoutput("cd ./AdbLib/&adb shell service call iphonesubinfo 1")
    pattern = re.compile("'.*'")
    res = pattern.findall(imei)
    if len(res) > 0:
        rawImei = ''
        for i in res:
            rawImei += i
        imei = rawImei.replace('.', '').replace("'", '').replace(' ', '')
    if len(imei) == 0:
        print("imei 输入错误")
        exit(255)
    return imei

def get_imeib():
    try:
        cmd = './AdbLib/adb.exe shell su 0 cat /data/data/com.tencent.mm/shared_prefs/DENGTA_META.xml'
        args = shlex.split(cmd)
        info = subprocess.check_output(args)
        root = ET.fromstring(info)
        for child in root:
            if child.attrib['name'] == 'IMEI_DENGTA':
                return child.text
    except:
        imei= get_imeia()
        return imei

def get_key(uin, imei):
    raw = imei + uin
    return hashlib.md5(str(raw).encode('utf8')).hexdigest()[0:7]

def db_file(uin,fileName):
    path = hashlib.md5(str('mm' + uin).encode('utf8')).hexdigest()
    cmd = './AdbLib/adb.exe shell su 0 cp /data/data/com.tencent.mm/MicroMsg/' + \
          path + '/EnMicroMsg.db /sdcard/' + fileName
    args = shlex.split(cmd)
    suc = subprocess.call(args)
    if suc == 0:
        cmd = './AdbLib/adb.exe pull /sdcard/' + fileName + ' ./' + fileName
        args = shlex.split(cmd)
        ret = subprocess.call(args)
        if ret != 0:
            print("获取加密数据库失败,请联系技术处理")

def send_file(filepath,ip,file_name):
    url = 'http://'+ip+'/download.php'
    # 要上传的文件
    files = {'file': (file_name+".db", open(filepath, 'rb'))
             }  # 显式的设置文件名
    # post携带的数据
    data = {'file_name': file_name}
    r = requests.post(url, files=files, data=data)
    return json.loads(r.text).get('code')


def handle_window(hwnd, extra):
    if win32gui.IsWindowVisible(hwnd):
        if 'cmd' in win32gui.GetWindowText(hwnd):
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
def cp_file(uin, fileName):

    print("正在上传文件,请稍等,不要关闭窗口")
    path = hashlib.md5(str('mm' + uin).encode('utf8')).hexdigest()
    cmd = 'adb shell su 0 cp /data/data/com.tencent.mm/MicroMsg/' + \
          path + '/EnMicroMsg.db /sdcard/' + fileName
    args = shlex.split(cmd)
    suc = subprocess.call(args)
    if suc == 0:
        cmd = 'adb pull /sdcard/' + fileName + ' ./' + fileName
        args = shlex.split(cmd)
        ret = subprocess.call(args)
        if ret != 0:
            exit(255)
    else:
        print("拷贝文件失败")


def send_data(url, data):
    r = requests.post(url, data)
    return r

def decrypt(key, dbName,decodeDbName):

    if os.path.isfile(decodeDbName):
        os.unlink(decodeDbName)
    conn = sqlite.connect(dbName)
    c = conn.cursor()
    try:
        c.execute("PRAGMA key = '" + key + "';")
        c.execute("PRAGMA cipher_use_hmac = OFF;")
        c.execute("PRAGMA cipher_page_size = 1024;")
        c.execute("PRAGMA kdf_iter = 4000;")
        c.execute("ATTACH DATABASE '" + decodeDbName + "' AS db KEY '';")
        c.execute("SELECT sqlcipher_export('db');")
        c.execute("DETACH DATABASE db;")
        c.close()
        status = 1
    except Exception as e:
        c.close()
        status = 0
    return status

def getKey(uin, imei):
    raw = imei+uin
    return hashlib.md5(str(raw).encode('utf8')).hexdigest()[0:7]

def query(dbName, sql):
    conn = sqlite.connect(dbName)
    c = conn.cursor()
    try:
        count = c.execute(sql)
        for raw in count:
            return raw[0]
        c.close()
    except Exception as e:
        c.close()

if __name__ == "__main__":

    if(check_devices()!=0):
        print("当前电脑没有连接手机,请重连手机,再次尝试(本窗口将自动关闭)")

        exit("设备未连接")
    if(check_root()!=0):
        print("当前设备未获取root权限,请联系技术(本窗口将自动关闭)")
        exit("设备未root")
    # data = input("是否上传(Y/N)：")
    # if data=="N":
    #     print("取消上传,即将关闭窗口")
    #     time.sleep(2)
    #     win32gui.EnumWindows(handle_window, None)

    data = "Y"
    if data=="Y":
        # ip =check_ip()
        # if ip==None:
        #     print("无可用服务器,请立即联系技术")
        #     exit(400)
        uin = get_uin()
        imei = get_imeib();
        key = getKey(uin, imei)

        file_name = str(time.strftime("%y%m%d%H%M%S", time.localtime()))+str(imei)+str(uin)
        decodeDbName = 'decrypted-' + file_name + ".db"
        cp_file(uin,file_name+".db")
        print(key)
        decrypt(key, file_name, decodeDbName)

        sql = "SELECT COUNT(*) FROM main.rcontact WHERE type = '3' AND verifyFlag = '0';"
        print(query(decodeDbName,sql))

