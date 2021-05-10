#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
from aip import AipImageSearch
from aip import AipOcr
import requests
import json
import sys
import base64
# from urllib.parse import quote
requests.packages.urllib3.disable_warnings()

IMG_APP_ID = '21552210'
IMG_API_KEY = 'dHqG78qSi8HRdEQMwGipXlLS'
IMG_SECRET_KEY = 'X9hoOwCI6rfjttyh6N9Svuif2MXXtNma'

ORC_APP_ID = '21550072'
ORC_API_KEY = 'EtFX49NClWWND3NFOvG8SjAa'
ORC_SECRET_KEY = 'LUe3aFa8Cz7aPQMcWK8FOfWI8Dn4tAXy'

img_client = AipImageSearch(IMG_APP_ID, IMG_API_KEY, IMG_SECRET_KEY)
orc_client = AipOcr(ORC_APP_ID, ORC_API_KEY, ORC_SECRET_KEY)

def get_access_token():
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id='+ str(IMG_API_KEY) +'&client_secret=' + str(IMG_SECRET_KEY)
    response = requests.get(host)
    result =response.json()
    if result.get('error'):
        return False
    else:
        return result['access_token']

def add_sim_img( filePath, brief):
    image = get_file_content(filePath)
    res = img_client.similarAdd(image, brief)
    return res

def search_img(filePath):
    image = get_file_content(filePath)
    return img_client.similarSearch(image)

def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

def get_location(img_path):
    image = get_file_content(img_path)

    res = orc_client.basicAccurate(image)
    return res
