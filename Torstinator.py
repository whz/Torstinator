#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
""" Torstinator.py - The ultimate Python bark detector """

__author__ = 'Tero Heino'
__version__ = 2.0



import os
import sys

import urllib2
import cookielib
import wave
import audioop
import ConfigParser
import socket


import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s\t%(levelname)s\t%(message)s')

import time
import os
import sys
from time import strftime

__sqliteenabled__ = False
try:
  import sqlite3
  __sqliteenabled__ = True
except ImportError:
  logging.warning("Could not import sqlite module")
  pass



try:
  import pyaudio
except ImportError:
  logging.critical("You need to have pyaudio library "+ \
        "(http://people.csail.mit.edu/hubert/pyaudio/)")
  sys.exit(1)

class TConfig(object):
  config = None


  sample_rate = 44100
  buffer_size = 30
  remote_host = '127.0.0.1'
  remote_port = 1337

  def __init__(self):
    try:
      self.config = ConfigParser.ConfigParser()
      self.config.readfp(open('Torstinator.conf'))
    except IOError:
      logging.critical("Config file not found, please take ", \
               "copy of Torstinator.conf.sample and ", \
               "rename it as Torstinator.conf")
      sys.exit(2)

    self.sample_rate = self.config.getint('Monitoring','sample_rate')
    self.buffer_size = self.config.getint('Monitoring','buffer_size')


class AudioBank(object):
  """ AudioBank class holds the noise level and raw audio
      data """
  con = None
  day = None
  config = None
  
  audio_data = []
  noise_levels = []

  rolling_average = 0
  silence = 70
  noise = 20000

  def __init__ (self):
    """ init """
    database_name = "archives/noise_archive/noise.%s.db" % \
            strftime("%Y-%m-%d")
    self.day = strftime("%d")


    if os.path.isdir("archives/noise_archive"):
      logging.debug("noise_archive folder found")
    else:
      os.mkdir("archives/noise_archive")
      logging.info("created archive folder for sqlite files")

    if os.path.isdir("archives/record_archive"):
      logging.debug("record_archive folder found")
    else:
      os.mkdir("archives/record_archive")
      logging.info("created archive folder for wave record files")

    if __sqliteenabled__:
      logging.debug("Connecting to database")
      if not os.path.isfile(database_name):
        logging.warning("Database file not found")
        self.con = sqlite3.connect(database_name, isolation_level = None)
        cursor = self.con.cursor()
        cursor.execute('create table noise (datetime text, noise real);')
      else:
        logging.debug("Database file found")
        self.con = sqlite3.connect(database_name, isolation_level = None)
        logging.debug("Database connected")


  def push(self, newsounds, levels):
    """ push(rawsounddata, soundlevel) pushes raw data and
        noise levels to arrays for further processing """
    self.audio_data.append(newsounds)
    self.noise_levels.append(levels)
    self.rolling_average = (self.rolling_average+levels)/2
    if len(self.audio_data) >  config.buffer_size:
      self.audio_data.pop(0)
      self.noise_levels.pop(0)
    
  def buffer_size(self):
    """ buffer_size() returns the size of buffer in seconds """
    return len(self.audio_data)
  
  def get_data(self):
    """ get_data() returns raw audio data for the 
      duration of BUFFER_SIZE """
    return ''.join(self.audio_data)
  
  def noiseleveltopercentage(self, level):
    """ noiseleveltoprecentage(noiselevel) transforms
      your noise level into percentage value """
    percentage = (float(level) - float(self.silence))
    percentage = (percentage / float(self.noise)) * 100
    if percentage < 0:
      return 0
    elif percentage > 100:
      return 100
    else:
      return percentage
      
  def status(self):
    """ status() brings up a status of the data that bank 
      currently holds """
    if os.name == "posix":
      os.system('clear')
    if os.name == "nt":
      os.system('cls')

    print "| AudioBank now has %d/%d seconds stored" % (len(self.audio_data), config.buffer_size) 
    print "|-----------------------------------"
    print "| Max noise: %d" % max(self.noise_levels)
    print "| Average noise: %d" % self.rolling_average
    print "|-----------------------------------"
    for i in self.noise_levels:
      output = ""
      for level in range(0, int(self.noiseleveltopercentage(i)/2)):
        output = output+"|"
      if i == max(self.noise_levels):
        output = output + " (MAX)"
      print "|%s" % output


class Torstinator:
  """ Class for doing all the work of Torstinator - The bark detector"""
  paudio = None
  stream = None
  audiobank = None
  
  def __init__(self):
    """ Constructor, set the defaults, read config etc """
    try:
      logging.debug("Setting up PyAudio")
      self.paudio = pyaudio.PyAudio()

      self.audiobank = AudioBank()
      
      logging.debug("Setting up audiostream")
      self.stream = self.paudio.open(format = pyaudio.paInt16,
              channels = 1,
              rate =  config.sample_rate,
              input = True,
          frames_per_buffer =  config.sample_rate)

    except:
      print "Unexpected error:", sys.exc_info()[0]

    if self.stream == None:
      logging.critical("Failed to open microphone")
      return
    
    self.monitor()

  def remote_log(self, level):
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect((config.remote_host, config.remote_port))
      send_string = '{"user":"%s","level":%d}' % ("test", level)
      s.send(send_string)
      data = s.recv(1024)
      s.close()
    except:
      print "Unexpected error:", sys.exc_info()[0]
      pass
      
  def save_buffer(self, filename):
    """ save_buffer(filename) saves current audiobank buffer
      to hard disk """
    wavefile = wave.open(filename, 'wb')
    wavefile.setnchannels(1)
    wavefile.setsampwidth(self.paudio.get_sample_size(pyaudio.paInt16))
    wavefile.setframerate(config.sample_rate)
    wavefile.writeframes(self.audiobank.get_data())
    wavefile.close()

  def monitor(self):
    """ monitor() receive data from microphone
      and act accordingly """
    while True:
      try:
        data = self.stream.read(config.sample_rate)
        level = int(audioop.max(data, 2))
        self.remote_log(level)
        self.audiobank.push(data, level)
        self.audiobank.status()
        # logging.info("Noise: %d" % level)
      except IOError:
        logging.warning("PyAudio failed to read device, skipping")
    
      except KeyboardInterrupt:
        # self.audiobank.save_buffer("poo.wav")
        logging.info("Interrupted by ctrl-c")
        break
    


  def __del__(self):
    self.stream.close()
    self.paudio.terminate()



if __name__ == "__main__":
  config = TConfig()
  T = Torstinator()
