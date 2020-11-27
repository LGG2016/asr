#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time
import requests
import json
import hashlib
import os
from requests_toolbelt.multipart.encoder import MultipartEncoder
from optparse import OptionParser
import utils

import log
from configparser import ConfigParser

logger = log.logging.getLogger('sbc')

parser = OptionParser()

class Http_Client(object):
    def __init__(self, ProductId, PublicKey, SecretKey, AudioFile, Format='pcm'):
        self.productId = ProductId
        self.publicKey = PublicKey
        self.secretKey = SecretKey
        self.AudioFile = AudioFile
        self.Format = Format

        self.TokenFile = 'sbc.token'
        self.TokenUrl = "http://api.talkinggenie.com/api/v2/public/authToken"
        self.ResultUrl = "https://api.talkinggenie.com/smart/sinspection/api/v2/getTransResult"
        self.UpLoadUrl = "http://api.talkinggenie.com/smart/sinspection/api/v1/fileUpload"
        self.Token = ''
        self.Result = ''
        if self.Format == 'pcm':
            self.AudioFile = utils.PcmFileToWavFile(self.AudioFile)

    def __del__(self):
        if self.Format == 'pcm':
            os.remove(self.AudioFile)

    def fetch_token(self, refresh=False):
        ret = False
        if False == refresh:
            if os.path.exists(self.TokenFile):
                with open(self.TokenFile, "r") as fd:
                    info = fd.readline().split(":")
                    if len(info) == 2:
                        token = info[0]
                        expire = info[1]
                        ctime = int(time.time())
                        if (int(expire) > ctime):
                            logger.info("use local token in the sbc.token file")
                            self.Token = token
                            return True
                        else:
                            logger.info("local token expire, get again...")

        timeStamp = str(int(round(time.time() * 1000)))
        sign = hashlib.md5(
            (self.publicKey + self.productId + timeStamp + self.secretKey).encode('utf8')).hexdigest()
        # 请求头
        data = {
            "productId": self.productId,
            "publicKey": self.publicKey,
            "sign": sign,
            "timeStamp": timeStamp
        }
        headers = {
            'Content-Type': "application/json"
        }
        response = requests.post(url=self.TokenUrl, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            self.Token = response.json()["result"].get("token")
            logger.info("new token:%s" % self.Token)
            expire = response.json()["result"].get("expireTime")
            with open(self.TokenFile, "w+") as out:
                out.write(self.Token + ":" + str(round(int(expire)/1000)))
            return True
        else:
            logger.error("get token failed, request status:%d" % response.status_code)
        return ret

    def getResult(self, id):
        ret = False
        # 请求头
        headers = {
            'Content-Type': "application/json;charset=UTF-8",
            'Accept': "application/json;charset=UTF-8",
            'X-AISPEECH-TOKEN': self.Token,
            'X-AISPEECH-PRODUCT-ID': self.productId
        }
        data={}
        data["dialog"] = {}
        data["dialog"]["productId"] = self.productId
        data["metaObject"] = {}
        data["metaObject"]["fileId"] = id
        retry=0
        while retry < 5:
            time.sleep(0.1)
            try:
                response = requests.post(url=self.ResultUrl, headers=headers, data=json.dumps(data))
            except:
                retry+=1
                logger.error("get result exception ...")
                continue
            else:
                if response.status_code == 200:
                    logger.info("fileId:%s, get result:%s", id, response.text)
                    info = response.json()
                    if info["code"] == 200:
                        info_status = info["data"]["status"]
                        if info_status == "TRANSFERING":
                            logger.info("get result response status is transfering, continue ...")
                            continue
                            retry += 1
                        elif info_status == "SUCCEED":
                            for part in info["data"]["result"]:
                                self.Result += part["text"]
                            ret = True
                            break
                        else:
                            logger.error("get result failed, status: %s" % info_status)
                            break
                    else:
                        logger.error("get result failed, code: %d" % info["code"])
                        break
                else:
                    logger.error("get result failed, response code: %d, text: %s,", response.status_code, response.text)
                    break

        return ret


    def GetAsrResult(self):

        if False == self.fetch_token():
            logger.error("fetch token failed, file:%s" % self.AudioFile)
            return self.Result

        # 上传文件
        # 请求头
        param = {}
        param["dialog"] = {}
        param["dialog"]["productId"] = self.productId
        param["metaObject"] = {}
        param["metaObject"]["recordId"] = self.AudioFile
        param["metaObject"]["priority"] = 100
        #param["metaObject"]["speechSeparate"] = True
        #param["metaObject"]["speakerNumber"] = 1
        encoder = MultipartEncoder(
            fields={
                'param': json.dumps(param, sort_keys=True, indent=4, separators=(',', ': ')),
                'file': (self.AudioFile, open(self.AudioFile, 'rb'), 'application/octet-stream')
            }
        )
        headers = {
            'Content-Type': encoder.content_type,
            'Accept': "application/json",
            'X-AISPEECH-TOKEN': self.Token,
            'X-AISPEECH-PRODUCT-ID': self.productId
        }
        logger.info("sbc recognition [%s] ..." % self.AudioFile)
        try:
            response = requests.post(url=self.UpLoadUrl, headers=headers, data=encoder)
        except:
            logger.error("upload [%s] file exception" % (self.AudioFile))
        else:
            if response.status_code == 200:
                result = response.json()
                if result["code"] == 200:
                    fileId = result["data"]["fileId"]
                    if False == self.getResult(fileId):
                        logger.error("sbc get result failed, file:%s" % self.AudioFile)
                    else:
                        logger.info("get result success, file:%s, result:%s" % (self.AudioFile, self.Result))
                else:
                    logger.error("upload [%s] failed, result code: %d, msg: %s, status: %s" % (self.AudioFile, result["code"], result["msg"], result["data"]["status"]))
            else:
                logger.error("upload [%s] failed, response code: %d" % (self.AudioFile, response.status_code))

        return self.Result


if __name__ == '__main__':
    audiofile = "./audio/16k.pcm"
    conf = ConfigParser()
    conf.read('./conf/config.ini', encoding='UTF-8')
    client = Http_Client(ProductId=conf['sbc']['productid'], PublicKey=conf['sbc']['publickey'], SecretKey=conf['sbc']['secretkey'], AudioFile=audiofile, Format='pcm')
    print("file:%s, result:%s" % (audiofile, client.GetAsrResult()))

