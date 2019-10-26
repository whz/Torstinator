#!/usr/bin/env python3
# -*- coding: utf-8 -*-
####################################
# SETTINGS, CHANGE THESE IF REQUIRED

# Percentage value from 1-100, used to detect noise
RECORD_SENSITIVITY = 10


####################################

import sys
import time
import os
from time import strftime
import argparse

try:
    import pyaudio
except ImportError:
    print("You need to have pyaudio library\nInstall homebrew: https://brew.sh/\nInstall portaudio: brew install portaudio\nInstall pyaudio: pip3 install pyaudio")
    sys.exit(1)

import wave
import audioop


TORSTINATOR_VERSION = 2.1

audio_bank = []
current_silence = 10000000000000


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--stop-after", 
                    type = int,
                    help = "How many seconds should we wait for new noise before stopping recording", 
                    default = 3)
parser.add_argument("-m", "--max-level", 
                    type = int,
                    help = "Max value that can be read from the audio device", 
                    default = 32677)
parser.add_argument("-r", "--record-sensitivity", 
                    type = int,
                    help = "What amount of noise should trigger the recording", 
                    default = 10,
                    choices=[10, 20, 30, 40, 50, 60, 70, 80, 90])
args = parser.parse_args()



def process_audio(data):
    global current_silence, audio_bank
    should_record = False
    level = audioop.max(data, 2)
    level_char = u'▁'
    alert_level = args.max_level*(float(args.record_sensitivity)/float(100))
    if level > alert_level*0.1:
        level_char = u'▂'
    if level > alert_level*0.2:
        level_char = u'▃'
    if level > alert_level*0.3:
        level_char = u'▅'
    if level > alert_level*0.5:
        level_char = u'▇'
    if level > alert_level*0.75:
        level_char = u'█'

    if level > alert_level:
        level_char = u'♬'
        current_silence = 0
        should_record = True
    else:
        current_silence = current_silence + 1

    if current_silence <= args.stop_after:
        should_record = True 
    
    if should_record == False and len(audio_bank) > 0:
        filename = 'wav/%s.wav' % strftime("%Y-%m-%d_%H%M%S")
        wavefile = wave.open(filename, 'w')
        wavefile.setparams((1, 2, 44100, 44100, 'NONE', 'not compressed'))
        wavefile.writeframes(b''.join(audio_bank))
        wavefile.close()
        audio_bank = []
        sys.stdout.write(u'┆')
        sys.stdout.flush()

    if should_record:
        audio_bank.append(data)

    f = open('csv/%s.csv' % strftime("%Y-%m-%d"), 'a')
    f.write("%s,%d,%s\n" % (strftime("%Y-%m-%d %H:%M:%S"),level,should_record))
    f.close()

    sys.stdout.write(level_char)
    sys.stdout.flush()


def read_stream(in_data, frame_count, time_info, status_flags):
    process_audio(in_data)
    return ("", 0)

def print_time():
    da_msg = "\n%s " % (strftime("%Y-%m-%d %H:%M"))
    sys.stdout.write(da_msg)
    sys.stdout.flush()

def create_directories():
    if not os.path.isdir("csv"):
        os.mkdir("csv")
    if not os.path.isdir("wav"):
        os.mkdir("wav")


def main():
    create_directories()

    p = pyaudio.PyAudio()
    stream = p.open(
        format = pyaudio.paInt16,
        channels = 1,
        rate =  44100,
        frames_per_buffer = 44100,
        stream_callback = read_stream,
        input = True
        )

    print("TORSTINATOR %.1f" % TORSTINATOR_VERSION)
    last_second = 0
    print_time()
    while stream.is_active():
        time.sleep(1)
        if int(strftime("%S")) < int(last_second):
            print_time()
        last_second = strftime("%S")


    stream.close()
    p.terminate()


main()