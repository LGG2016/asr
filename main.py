from multiprocessing import Pool
import log
from configparser import ConfigParser

#asr接入类
import baidu
import ali
import xunfei
import yitu

Providers = {'baidu', 'ali', 'xunfei', 'yitu'}
audioListFile = "./audio/sid.list"

logger = log.logging.getLogger('main')
conf = ConfigParser()
conf.read('./conf/config.ini', encoding='UTF-8')

def AsrRegonition(provide):
    flist = open(audioListFile, 'r')
    for line in flist:
        pcmfile = line.strip('\n')
        if provide == "baidu":
            client = baidu.Http_Client(AppId=conf[provide]['appid'], ApiKey=conf[provide]['apikey'], KeySecret=conf[provide]['keysecret'], AudioFile=pcmfile)
        elif provide == "ali":
            client = ali.Http_Client(AppKey=conf[provide]['appkey'], AccessKeyId=conf[provide]['accesskeyid'], AccessKeySecret=conf[provide]['accesskeysecret'], AudioFile=pcmfile)
        elif provide == "xunfei":
            client = xunfei.Ws_Client(APPID=conf[provide]['appid'], APIKey=conf[provide]['apikey'], APISecret=conf[provide]['apisecret'], AudioFile=pcmfile)
        elif provide == "yitu":
            client = yitu.Http_Client(DevId=conf[provide]['devid'], DevKey=conf[provide]['devkey'], AudioFile=pcmfile)
        else:
            print("provide is not support")
            return

        result = client.GetAsrResult()
        if result == "":
            logger.warning("provide:%s, file:%s, result is null" % (provide, pcmfile))
        outMsg = ("file:{0}, provide:{1}, result:{2}").format(pcmfile, provide, result)
        logger.info(outMsg)
        outfile = provide + ".txt"
        with open(outfile, 'a+') as out:
            out.write("{0}\n".format(outMsg))
        print(outMsg)
    flist.close()


if __name__ == '__main__':
    pool = Pool(len(Providers))
    pool.map(AsrRegonition, Providers)
    pool.close()
    pool.join()
    print('main over')
