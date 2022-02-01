#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

import os

from logging import *
import tempfile

tempDir = tempfile.gettempdir()
user = os.environ['USER']

FORMAT = "%(asctime)s : %(pathname)s : %(funcName)s - %(levelname)s - %(lineno)d - %(message)s"
basicConfig(filename=tempDir + os.sep + "Blender_Manager_" + user + ".log",filemode='a', format=FORMAT, level=INFO)
