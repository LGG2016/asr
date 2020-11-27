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

def PcmFileToWavFile(pcmfile):
    wavfile = pcmfile + ".wav"
    with open(pcmfile, 'rb') as infile:
        indata = infile.read()
    with wave.open(wavfile, 'wb') as outfile:
        outfile.setparams((1, 2, 16000, 0, 'NONE', 'NONE'))
        outfile.writeframes(indata)
    return wavfile
