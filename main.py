from multiprocessing import Pool
import log
import asr

logger = log.logging.getLogger('main')
Providers = {'baidu', 'ali', 'xunfei', 'yitu', 'sbc'}
audioListFile = "./audio/sid.list"


def AsrRegonition(provider):
    flist = open(audioListFile, 'r')
    for line in flist:
        pcmfile = line.strip('\n')
        client = asr.Asr(provider=provider, audioFile=pcmfile)
        if None == client:
            logger.error("init asr client failed")
            return
        result = client.GetAsrResult()
        if result == "":
            logger.warning("provider:%s, file:%s, result is null" % (provider, pcmfile))
        outMsg = ("file:{0}, provider:{1}, result:{2}").format(pcmfile, provider, result)
        logger.info(outMsg)
        outfile = provider + ".txt"
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
