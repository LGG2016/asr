import wave
import threading
import os

def PcmToWav(indata):
    outdata = None
    tid = threading.current_thread()
    tmpfile = str(os.getpid()) + "." + str(tid) + '.tmp.wav'
    with wave.open(tmpfile, 'wb') as wavfile:
        wavfile.setparams((1, 2, 16000, 0, 'NONE', 'NONE'))
        wavfile.writeframes(indata)
    with open(tmpfile, 'rb') as file:
        outdata = file.read()
    os.remove(tmpfile)
    return outdata
