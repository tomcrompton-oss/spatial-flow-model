"""the old files here import constants directly: it now lives in engine/constants.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
from engine.constants import *
