# -*- coding: UTF-8 -*-

import http.client
import time
import hashlib
import base64
import hmac
import json
import utils
import log
from configparser import ConfigParser

logger = log.logging.getLogger('yitu')

class Http_Client(object):
    def __init__(self, DevId, DevKey, AudioFile, Format='pcm'):
        self.DevId = DevId
        self.DevKey = DevKey
        self.AudioFile = AudioFile
        self.Format = Format
        self.Host = "asr-prod.yitutech.com"
        self.Url = "http://" + self.Host + "/v2/asr"

        self.Token = ""
        self.Timestamp = 0
        self.Result = ""

    def getToken(self):
        timestamp = int(time.time())
        origin = self.DevId + str(timestamp)
        sign = hmac.new(self.DevKey.encode('utf-8'), origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        self.Sign = sign.hex()
        self.Timestamp = timestamp
        return True

    def Recognition(self):
        ret = False
        header = {
            'Content-type': 'application/json',
            'x-dev-id': self.DevId,
            'x-signature': self.Sign,
            'x-request-send-timestamp': self.Timestamp
        }
        with open(self.AudioFile, "rb") as fd:
            audio = fd.read()
            if self.Format == 'wav': # wav pcm , aue = 'pcm'
                self.Format = 'pcm'
            elif self.Format == 'pcm': #因yitu对pcm的支持有问题，目前采取pcm转wav来请求
                audio = utils.PcmToWav(audio)#pcm to wav

        param = {
            #'audioBase64': base64.urlsafe_b64encode(audio).decode(encoding='utf-8'),
            'audioBase64': base64.b64encode(audio).decode(encoding='utf-8'),
            'lang': 'MANDARIN',
            'scene': 'GENERAL',
            'aue': self.Format
        }
        try:
           conn = http.client.HTTPConnection(self.Host)
           conn.request(method="POST", url=self.Url, body=json.dumps(param), headers=header)
           response = conn.getresponse()
           logger.info("Response status:%d, reason:%s" % (response.status, response.reason))
           if response.status == 200:
               info = json.loads(response.read())
               logger.info("Response body: %s" % json.dumps(info))
               if info["message"] == "success":
                   self.Result = info["resultText"]
                   ret = True
                   logger.info("file:%s, result:%s" % (self.AudioFile, self.Result))
               else:
                   logger.error("message is not success, file:%s" % self.AudioFile)
           else:
               logger.error("response status is not 200, file:%s" % self.AudioFile)

        except Exception as e:
            logger.error("get asr result except, msg:%s" % str(e))
        else:
            conn.close()
        return ret

    def GetAsrResult(self):
        if False == self.getToken():
            logger.error('get token failed, file:%s' % self.AudioFile)
        else:
            if False == self.Recognition():
                logger.error('recognition failed, file:%s' % self.AudioFile)
        return self.Result

if __name__ == '__main__':
    audiofile = "./audio/16k.pcm"
    conf = ConfigParser()
    conf.read('./conf/config.ini', encoding='UTF-8')
    client = Http_Client(DevId=conf['yitu']['devid'], DevKey=conf['yitu']['devkey'], AudioFile=audiofile, Format='pcm')
    print("file:%s, result:%s" % (audiofile, client.GetAsrResult()))

