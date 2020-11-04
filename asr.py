from configparser import ConfigParser
import log

#asr接入类
import baidu
import ali
import xunfei
import yitu

logger = log.logging.getLogger('asr')
config = ConfigParser()
config.read('./conf/config.ini', encoding='UTF-8')

class Asr(object):
    def __init__(self, provider, audioFile):
        self.Provider = provider
        self.AudioFile = audioFile
        self.Client = None

    def GetAsrResult(self):
        if self.Provider == 'baidu':
            self.Client = baidu.Http_Client(AppId=config[self.Provider]['appid'], ApiKey=config[self.Provider]['apikey'],
                                       KeySecret=config[self.Provider]['keysecret'], AudioFile=self.AudioFile)
        elif self.Provider == 'ali':
            self.Client = ali.Http_Client(AppKey=config[self.Provider]['appkey'], AccessKeyId=config[self.Provider]['accesskeyid'],
                                     AccessKeySecret=config[self.Provider]['accesskeysecret'], AudioFile=self.AudioFile)
        elif self.Provider == 'xunfei':
            self.Client = xunfei.Ws_Client(APPID=config[self.Provider]['appid'], APIKey=config[self.Provider]['apikey'],
                                      APISecret=config[self.Provider]['apisecret'], AudioFile=self.AudioFile)
        elif self.Provider == 'yitu':
            self.Client = yitu.Http_Client(DevId=config[self.Provider]['devid'], DevKey=config[self.Provider]['devkey'], AudioFile=self.AudioFile)
        else:
            logger.error("provide is not support")
            return ""
        return self.Client.GetAsrResult()
