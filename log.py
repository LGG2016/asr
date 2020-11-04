import logging

logging.basicConfig(level=logging.INFO, filename='asr.log', filemode='a+', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('chardet.charsetprober')
logger.setLevel(logging.INFO)
