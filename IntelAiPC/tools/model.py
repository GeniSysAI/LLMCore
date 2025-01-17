############################################################################################
#
# The MIT License (MIT)
# 
# GeniSysAI LLMCore Model
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
# Title:         GeniSysAI LLMCore Model
# Description:   Class to manage model loading and tokenization for GeniSysAI LLMCore.
# Configuration: configuration/confs.json
# Last Modified: 2025-01-12
#
############################################################################################

import os
import json

from typing import List, Tuple

from optimum.intel.openvino import OVModelForCausalLM
from transformers import (
    AutoConfig,
    AutoTokenizer
)

import openvino.properties as props
import openvino.properties.hint as hints
import openvino.properties.streams as streams

from tools.definitions import AssistantDefinition

class Model:

    def __init__(self, confs):
        """
        Initializes the Model class to manage LLM loading, tokenization, and configuration.

        Args:
            confs (dict): Configuration dictionary containing model settings, such as paths and device information.
            
        Sets up paths, device configurations, and placeholders for model components.
        """
        self._confs = confs
        self.model_path = os.path.join(self._confs['llm']['model_path'], self._confs["llm"]["model_out"])
        self.llm_device = self._confs["llm"]["device"]

        self.llm = None  # LLM model instance placeholder
        self.llm_config = None  # Configuration placeholder for the LLM
        self.llm_tokenizer = None  # Tokenizer instance placeholder
        self.model_definition = None  # Model definition configuration placeholder

    def load_config(self):
        """
        Configures model settings for optimized OpenVINO performance.

        Applies performance tuning by setting properties like performance mode, stream count, and cache directory.
        """
        self.llm_config = {
            hints.performance_mode(): hints.PerformanceMode.LATENCY,
            streams.num(): "1",
            props.cache_dir(): ""
        }

    def load_model_definition(self):
        """
        Loads the model's core JSON definition from the specified configuration file.

        Reads and parses the JSON definition required for model behavior and parameters.
        """
        with open(self._confs['llm']['model_definition_json'], "r") as def_file:
            self.model_definition = json.load(def_file)

    def load_tokenizer(self):
        """
        Loads the tokenizer for the model.

        Ensures the model path is a directory and initializes the tokenizer using Hugging Face's AutoTokenizer.
        """
        if os.path.isdir(self.model_path):  # Ensure the path is valid
            self.llm_tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)

    def load_model(self):
        """
        Loads the LLM using OpenVINO.

        Ensures the model path is valid before initializing the model using OVModelForCausalLM.
        """
        if os.path.isdir(self.model_path):
            self.llm = OVModelForCausalLM.from_pretrained(
                self.model_path,
                device=self.llm_device,
                ov_config=self.llm_config,
                config=AutoConfig.from_pretrained(self.model_path, trust_remote_code=True),
                trust_remote_code=True
            )

    def convert_history_to_token(self, history: List[Tuple[str, str]]):
        """
        Converts conversation history into a token format suitable for the model.

        Args:
            history (List[Tuple[str, str]]): A list of user and assistant message pairs.
        
        Returns:
            torch.Tensor: Tokenized conversation history in a format expected by the LLM.
        """
        input_token = self.llm_tokenizer.apply_chat_template(
            history, add_generation_prompt=True, tokenize=True, return_tensors="pt"
        )
        return input_token

    def default_partial_text_processor(self, partial_text: str, new_text: str):
        """
        helper for updating partially generated answer, used by default

        Params:
        partial_text: text buffer for storing previosly generated text
        new_text: text update for the current step
        Returns:
        updated text string

        """
        partial_text += new_text
        return partial_text
