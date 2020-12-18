# -*- coding: utf-8 -*-
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models
import base64
import io
import log
import utils
from configparser import ConfigParser
import sys
if sys.version_info[0] == 3:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')

logger = log.logging.getLogger('tengxun')

class Http_Client(object):
    # 初始化
    def __init__(self, SecretID, SecretKey, AudioFile, Format="pcm"):
        self.SecretID = SecretID
        self.SecretKey = SecretKey
        self.AudioFile = AudioFile
        self.Format = Format

        self.Url = "asr.tencentcloudapi.com"

    def GetAsrResult(self):
        #本地文件方式请求
        try:
            cred = credential.Credential(self.SecretID, self.SecretKey)
            httpProfile = HttpProfile()
            httpProfile.endpoint = self.Url
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            clientProfile.signMethod = "TC3-HMAC-SHA256"
            client = asr_client.AsrClient(cred, "ap-shanghai", clientProfile)
            #读取文件以及 base64
            with open(self.AudioFile, "rb") as f:
                audio = f.read()
                if self.Format == 'pcm':
                    audio = utils.PcmToWav(audio)
                if sys.version_info[0] == 2:
                    content = base64.b64encode(audio)
                else:
                    content = base64.b64encode(audio).decode('utf-8')
            #发送请求
            req = models.SentenceRecognitionRequest()
            params = {"ProjectId": 0, "SubServiceType": 2, "SourceType": 1, "UsrAudioKey": "session-123"}
            req._deserialize(params)
            req.DataLen = len(content)
            req.Data = content
            req.EngSerViceType = "16k_zh"
            req.VoiceFormat = "wav"
            resp = client.SentenceRecognition(req)
            logger.info("file:%s, result:%s, sid:%s", self.AudioFile, resp.Result, resp.RequestId)
            return resp.Result
        except TencentCloudSDKException as err:
            logger.error("code:%s, message:%s, sid:%s", err.code, err.message, err.requestId)
            return ""

if __name__ == "__main__":
    audiofile = './audio/16k.pcm'
    conf = ConfigParser()
    conf.read('./conf/config.ini', encoding='UTF-8')
    client = Http_Client(APPID=conf['tengxun']['appid'], SecretID=conf['tengxun']['secretid'], SecretKey=conf['tengxun']['secretkey'],
                       AudioFile=audiofile, Format='pcm')
    print("file:%s, result:%s" % (audiofile, client.GetAsrResult()))
