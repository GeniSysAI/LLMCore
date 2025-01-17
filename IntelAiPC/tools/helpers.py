############################################################################################
#
# The MIT License (MIT)
# 
# GeniSysAI LLMCore Helpers
# Copyright (C) CogniTech Systems LTD (CogniTech.systems)
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Title:         GeniSysAI LLMCore Helpers
# Description:   Helper class for GeniSysAI LLMCore.
# Configuration: configuration/confs.json
# Last Modified: 2025-01-12
#
############################################################################################

import os
import time
import json
from datetime import datetime

class Helpers:

    def __init__(self):
        """
        Initialization method for Helpers class.
        Currently, no setup is required.
        """
        pass

    def load_configs(self):
        """
        Loads the core JSON configuration from 'required/confs.json'.

        Returns:
            dict: Parsed JSON configuration.
        """
        with open("configuration/confs.json", "r") as config_file:
            return json.load(config_file)

    def timer_start(self):
        """
        Starts a timer and captures the current timestamp.

        Returns:
            tuple: Current timestamp string and start time in seconds.
        """
        return str(datetime.now()), time.time()

    def timer_end(self, start_time):
        """
        Ends the timer and calculates the elapsed time.

        Args:
            start_time (float): Start time in seconds.

        Returns:
            tuple: End time in seconds, elapsed time, and end timestamp string.
        """
        end_time = time.time()
        return end_time, (end_time - start_time), str(datetime.now())

    def set_log_file(self, path):
        """
        Generates a timestamped log file path.

        Args:
            path (str): Directory path for the log file.

        Returns:
            str: Full log file path with timestamp.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d-%H')
        return os.path.join(path, f"{timestamp}.txt")

    def log_message(self, logfile, process, message_type, message, hide=False):
        """
        Logs a message to a log file and optionally prints it to the console.

        Args:
            logfile (str): Path to the log file.
            process (str): Process name or identifier.
            message_type (str): Type of message (e.g., INFO, ERROR).
            message (str): Message content to log.
            hide (bool, optional): If True, suppress console output. Defaults to False.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp}|{process}|{message_type}: {message}"
        with open(logfile, "a") as log_file:
            log_file.write(log_entry + '\n')
        if not hide:
            print(log_entry)