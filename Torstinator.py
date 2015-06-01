#!/usr/bin/env python
# -*- coding: utf-8 -*-

TORSTINATOR_VERSION = 2.0

import pyaudio
import wave
import sys
import time
from time import strftime
import audioop


MAX_LEVEL = 32677
RECORDING_STOP_AFTER_SILENCE = 5

def output_level(level):
	level_char = u'▁'
	if level > MAX_LEVEL*0.01:
	 	level_char = u'▂'
	if level > MAX_LEVEL*0.05:
	 	level_char = u'▃'
	if level > MAX_LEVEL*0.1:
	 	level_char = u'▅'
	if level > MAX_LEVEL*0.5:
	 	level_char = u'▇'
	if level > MAX_LEVEL*0.7:
		level_char = u'█'
	sys.stdout.write(level_char)
	sys.stdout.flush()

def read_stream(in_data, frame_count, time_info, status_flags):
	output_level(audioop.max(in_data, 2))
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
