"""everything the viewer's modules share: the standard imports, settings, data classes and tooltips"""
import csv
from datetime import datetime
import glob
import json
import math
import os
import queue
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

import numpy as np

from viewer.settings import *
from viewer.data import *
from viewer.tooltips import *
