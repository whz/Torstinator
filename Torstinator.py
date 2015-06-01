#!/usr/bin/env python
# -*- coding: utf-8 -*-
####################################
# SETTINGS, CHANGE THESE IF REQUIRED

# Percentage value from 1-100, used to detect noise
RECORD_SENSITIVITY = 40

# How many seconds should we wait for new noise
RECORDING_STOP_AFTER_SILENCE = 3

####################################

try:
  import pyaudio
except ImportError:
  print("You need to have pyaudio library "+ \
        "(http://people.csail.mit.edu/hubert/pyaudio/) or pip install --allow-unverified pyaudio --allow-external PyAudio pyaudio")
  sys.exit(1)

import wave
import sys
import time
import os
from time import strftime
import audioop


TORSTINATOR_VERSION = 2.0
MAX_LEVEL = 32677

audio_bank = []
current_silence = 10000000000000

def process_audio(data):
	global current_silence, audio_bank
	should_record = False
	level = audioop.max(data, 2)
	level_char = u'▁'
	alert_level = MAX_LEVEL*(float(RECORD_SENSITIVITY)/float(100))
	if level > alert_level*0.05:
	 	level_char = u'▂'
	if level > alert_level*0.1:
	 	level_char = u'▃'
	if level > alert_level*0.25:
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

	if current_silence <= RECORDING_STOP_AFTER_SILENCE:
		should_record = True 
	
	if should_record == False and len(audio_bank) > 0:
		filename = 'wav/%s.wav' % strftime("%Y-%m-%d_%H%M%S")
		wavefile = wave.open(filename, 'w')
		wavefile.setparams((1, 2, 44100, 44100, 'NONE', 'not compressed'))
		wavefile.writeframes(''.join(audio_bank))
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

p = pyaudio.PyAudio()
stream = p.open(
	format = pyaudio.paInt16,
	channels = 1,
	rate =  44100,
	frames_per_buffer = 44100,
	stream_callback = read_stream,
	input = True
	)


if not os.path.isdir("csv"):
	os.mkdir("csv")
if not os.path.isdir("wav"):
	os.mkdir("wav")

print "TORSTINATOR %.1f" % (TORSTINATOR_VERSION)
last_second = 0
print_time()
while stream.is_active():
	time.sleep(1)
	if strftime("%S") < last_second:
		print_time()
	last_second = strftime("%S")


stream.close()
p.terminate()
