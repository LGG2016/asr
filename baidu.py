# coding=utf-8

import sys
import json
import time
import os

import log
from configparser import ConfigParser

logger = log.logging.getLogger('baidu')

IS_PY3 = sys.version_info.major == 3

if IS_PY3:
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.error import URLError
    from urllib.parse import urlencode

    timer = time.perf_counter
else:
    import urllib2
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib2 import URLError
    from urllib import urlencode

    if sys.platform == "win32":
        timer = time.clock
    else:
        # On most other platforms the best timer is time.time()
        timer = time.time

# 需要识别的文件
#AUDIO_FILE = './audio/16k.pcm'  # 只支持 pcm/wav/amr 格式，极速版额外支持m4a 格式
# 文件格式
#FORMAT = AUDIO_FILE[-3:];  # 文件后缀只支持 pcm/wav/amr 格式，极速版额外支持m4a 格式
#FORMAT = "wav"


CUID = 'orion-test';
# 采样率
RATE = 16000;  # 固定值

# 普通版

DEV_PID = 1537;  # 1537 表示识别普通话，使用输入法模型。根据文档填写PID，选择语言及识别模型
#ASR_URL = 'http://vop.baidu.com/server_api'
SCOPE = 'audio_voice_assistant_get'  # 有此scope表示有asr能力，没有请在网页里勾选，非常旧的应用可能没有

#测试自训练平台需要打开以下信息， 自训练平台模型上线后，您会看见 第二步：“”获取专属模型参数pid:8001，modelid:1234”，按照这个信息获取 dev_pid=8001，lm_id=1234
# DEV_PID = 8001 ;
# LM_ID = 1234 ;

# 极速版 打开注释的话请填写自己申请的appkey appSecret ，并在网页中开通极速版（开通后可能会收费）

#DEV_PID = 80001
#ASR_URL = 'http://vop.baidu.com/pro_api'
#SCOPE = 'brain_enhanced_asr'  # 有此scope表示有asr能力，没有请在网页里开通极速版

# 忽略scope检查，非常旧的应用可能没有
# SCOPE = False


# 极速版


class Http_Client(object):
    def __init__(self, AppId, ApiKey, KeySecret, AudioFile, Format='pcm'):
        self.AppId = AppId
        self.ApiKey = ApiKey
        self.KeySecret = KeySecret
        self.AudioFile = AudioFile
        self.Format = Format
        self.TokenUrl = 'http://openapi.baidu.com/oauth/2.0/token'
        self.AsrUrl = 'http://vop.baidu.com/server_api'
        self.TokenFile = 'baidu.token'

        self.Token = ''
        self.Result = ''


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
                        logger.info("expire:%d" % int(expire))
                        logger.info("curtime:%d" % ctime)
                        if (int(expire) > ctime) :
                            logger.info("use local token in the baidu.token file")
                            self.Token = token
                            return True
                        else:
                            logger.info("local token expire, get again...")

        params = {'grant_type': 'client_credentials',
                  'client_id': self.ApiKey,
                  'client_secret': self.KeySecret}
        post_data = urlencode(params)
        if (IS_PY3):
            post_data = post_data.encode('utf-8')
        req = Request(self.TokenUrl, post_data)
        try:
            f = urlopen(req)
            result_str = f.read()
        except URLError as err:
            logger.info('token http response http code : ' + str(err.code))
            result_str = err.read()
        if (IS_PY3):
            result_str = result_str.decode()

        logger.info(result_str)
        result = json.loads(result_str)
        logger.info(result)
        if ('access_token' in result.keys() and 'scope' in result.keys()):
            if SCOPE and (not SCOPE in result['scope'].split(' ')):  # SCOPE = False 忽略检查
                logger.warning('scope is not correct')
            logger.info('SUCCESS WITH TOKEN: %s ; EXPIRES IN SECONDS: %s' % (result['access_token'], result['expires_in']))
            expire = int(time.time()) + int(result['expires_in']) - 10*60 #提前十分钟
            with open(self.TokenFile, 'w+') as fd:
                fd.write(result['access_token'] + ":" + str(expire))
            self.Token = result['access_token']
            ret = True
        else:
            logger.error('MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response')
        return ret

    def Recognition(self):
        """
        httpHandler = urllib2.HTTPHandler(debuglevel=1)
        opener = urllib2.build_opener(httpHandler)
        urllib2.install_opener(opener)
        """

        ret = False
        speech_data = []
        with open(self.AudioFile, 'rb') as speech_file:
            speech_data = speech_file.read()
        length = len(speech_data)
        if length == 0:
            logger.warning("file is empty")
            return ret

        params = {'cuid': CUID, 'token': self.Token, 'dev_pid': DEV_PID}
        #测试自训练平台需要打开以下信息
        #params = {'cuid': CUID, 'token': token, 'dev_pid': DEV_PID, 'lm_id' : LM_ID}
        params_query = urlencode(params);

        headers = {
            'Content-Type': 'audio/' + self.Format + '; rate=' + str(RATE),
            'Content-Length': length
        }

        #url = self.AsrUrl + "?" + params_query
        #print("url is", url);
        #print("header is", headers)
        # print post_data
        req = Request(self.AsrUrl + "?" + params_query, speech_data, headers)
        try:
            begin = timer()
            f = urlopen(req)
            resp = f.read()
            logger.info("Request time cost %f" % (timer() - begin))
        except  URLError as err:
            logger.error('asr http response http code : ' + str(err.code))
            return ret

        if (IS_PY3):
            body = json.loads(resp)
            logger.info("Response body:%s" % json.dumps(body))
            if body["err_no"] == 0:
                ret = True
                self.Result = body["result"][0]
        #with open("result.txt", "w") as of:
        #    of.write(result)
        return ret

    def GetAsrResult(self):
        if False == self.fetch_token():
            logger.error("get token failed, file: %s" % self.AudioFile)
        else:
            if False == self.Recognition():
                logger.error("recognition failed, file: %s" % self.AudioFile)
        return self.Result


if __name__ == '__main__':
    audiofile = "./audio/16k.pcm"
    conf = ConfigParser()
    conf.read('./conf/config.ini', encoding='UTF-8')
    client = Http_Client(AppId=conf['baidu']['appid'], ApiKey=conf['baidu']['apikey'], KeySecret=conf['baidu']['keysecret'], AudioFile=audiofile, Format='pcm')
    print("file:%s, result:%s" % (audiofile, client.GetAsrResult()))

