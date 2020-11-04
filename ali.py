# -*- coding: UTF-8 -*-
# Python 2.x引入httplib模块
# import httplib
# Python 3.x引入http.client模块

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

import http.client
import json
import os
import time
import log
from configparser import ConfigParser

logger = log.logging.getLogger('ali')

# 音频文件
sampleRate = 16000
enablePunctuationPrediction  = False #是否加标点
enableInverseTextNormalization = False #是否在后处理中执行ITN
enableVoiceDetection  = False #是否启动语音检测

class Http_Client(object):
    def __init__(self, AppKey, AccessKeyId, AccessKeySecret, AudioFile, Format="pcm"):
        self.AppKey = AppKey
        self.AccessKeyId = AccessKeyId
        self.AccessKeySecret = AccessKeySecret
        self.AudioFile = AudioFile
        self.Format = Format

        # 服务请求地址
        self.domain = 'nls-meta.cn-shanghai.aliyuncs.com'
        self.host = 'nls-gateway.cn-shanghai.aliyuncs.com'
        self.url = 'http://' + self.host + '/stream/v1/asr'
        self.tokenFile = 'ali.token'
        self.token = ""
        self.result = ""

    def getToken(self, refresh=False):
        if False == refresh:
            if os.path.exists(self.tokenFile):
                with open(self.tokenFile, "r") as fd:
                    info = fd.readline().split(":")
                    if len(info) == 2:
                        token = info[0]
                        expire = info[1]
                        ctime = int(time.time())
                        logger.info("expire: %d" % int(expire))
                        logger.info("curtime: %d" % ctime)
                        if (int(expire) > ctime) :
                            logger.info("use local token in the ali.token file")
                            self.token = token
                            return True
                        else:
                            logger.info("local token expire, get again...")
        # 创建AcsClient实例
        client = AcsClient(
            self.AccessKeyId,
            self.AccessKeySecret,
            "cn-shanghai"
        )
        # 创建request，并设置参数。
        req = CommonRequest()
        req.set_method('POST')
        req.set_domain(self.domain)
        req.set_version('2019-02-28')
        req.set_action_name('CreateToken')
        try:
            resp = client.do_action_with_exception(req)
        except Exception as e:
            logger.error("get token exception, msg: %s, file:%s" % (str(e), self.AudioFile))
        else:
            info = json.loads(resp)
            if info["ErrMsg"] != "":
                logger.error("get token failed, msg:%s, file:%s" % (info["ErrMsg"], self.AudioFile))
            else:
                print(resp)
                self.token = info["Token"]["Id"]
                expire = int(info["Token"]["ExpireTime"]) - 10*60 #提前10分钟
                with open(self.tokenFile, "w+") as fd:
                    fd.write(self.token + ":" + str(expire))
                return True
        return False

    def process(self, request):
        ret = False
        # 读取音频文件
        with open(self.AudioFile, mode='rb') as f:
            audioContent = f.read()

        # 设置HTTP请求头部
        httpHeaders = {
            'X-NLS-Token': self.token,
            'Content-type': 'application/octet-stream',
            'Content-Length': len(audioContent)
            }


        # Python 2.x使用httplib
        # conn = httplib.HTTPConnection(host)

        # Python 3.x使用http.client
        conn = http.client.HTTPConnection(self.host)

        conn.request(method='POST', url=request, body=audioContent, headers=httpHeaders)

        response = conn.getresponse()
        logger.info('Response status: %d , response reason: %s' % (response.status, response.reason))

        body = response.read()
        try:
            body = json.loads(body)
            logger.info('Response body: %s', json.dumps(body))

            status = body['status']
            if status == 20000000:
                ret = True
                self.result = body['result']
                logger.info('file:%s, result:%s' % (self.AudioFile, self.result))
            else:
                logger.error('status:%d is not 20000000, file:%s' % (status, self.AudioFile))

        except Exception as e:
            logger.error('get asr result exception, msg:%s, file:%s' % (str(e), self.AudioFile))

        conn.close()
        return ret

    def Recognition(self):
        # 设置RESTful请求参数
        request = self.url + '?appkey=' + self.AppKey
        request = request + '&format=' + self.Format
        request = request + '&sample_rate=' + str(sampleRate)

        if enablePunctuationPrediction :
            request = request + '&enable_punctuation_prediction=' + 'true'

        if enableInverseTextNormalization :
            request = request + '&enable_inverse_text_normalization=' + 'true'

        if enableVoiceDetection :
            request = request + '&enable_voice_detection=' + 'true'

        logger.info('Request: %s' % request)

        return self.process(request)


    def GetAsrResult(self):
        if False == self.getToken():
            print("getToken failed")
        elif False == self.Recognition():
            print("getAsrResult failed")
        return self.result


if __name__ == '__main__':
    audiofile = "./audio/16k.pcm"
    conf = ConfigParser()
    conf.read('./conf/config.ini', encoding='UTF-8')
    client = Http_Client(AppKey=conf['ali']['appkey'], AccessKeyId=conf['ali']['accesskeyid'], AccessKeySecret=conf['ali']['accesskeysecret'],
                         AudioFile=audiofile, Format='pcm')
    print("file:%s, result:%s" % (audiofile, client.GetAsrResult()))


