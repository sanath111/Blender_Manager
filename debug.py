#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

import sys
import os

import logging
from logging import *


FORMAT = "%(asctime)s : %(pathname)s : %(funcName)s - %(levelname)s - %(lineno)d - %(message)s"
basicConfig(format=FORMAT, level=INFO)
