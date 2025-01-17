############################################################################################
#
# The MIT License (MIT)
# 
# GeniSysAI LLMCore
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
# Title:         GeniSysAI LLMCore
# Description:   GeniSysAI LLMCore is the core AI assistant for the GeniSysAI Network.
# Configuration: configuration/confs.json
# Last Modified: 2025-01-12
#
# Example Usage:
#
#   $ python run.py INPUT 
#   $ python run.py SERVER 
#
############################################################################################
 
import sys

from uuid import uuid4

from threading import Event, Thread

import torch
import openvino_genai

from transformers import (
    StoppingCriteriaList,
    StoppingCriteria,
    TextIteratorStreamer,
)

from tools.helpers import Helpers
from tools.model import Model
from tools.history import History

class StopOnTokens(StoppingCriteria):
    def __init__(self, token_ids):
        self.token_ids = token_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_id in self.token_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False

class LLMCore:
    """
    LLMCore Class:
    Responsible for managing model loading, tokenizer setup, and logging for the GeniSysAI LLM system.
    """
    def __init__(self):
        """
        Initializes the LLMCore by setting up configurations, logging, and preparing the model components.
        """
        self.Helpers = Helpers()
        self._confs = self.Helpers.load_configs()
        self.user = {}
        
        self.prepare_history()
        self.prepare_logs()
        self.prepare_model()

    def prepare_history(self):
        """
        Sets up logging for LLM and chat activities.
        
        Creates log files in the paths specified in the configuration.
        """
        self.History = History()
        self.conversation_id = self.History.generate_conversation_id()

    def prepare_logs(self):
        """
        Sets up logging for LLM and chat activities.
        
        Creates log files in the paths specified in the configuration.
        """
        self.LogFile = self.Helpers.set_log_file(f"{self._confs['llm']['logs_path']}llm/")
        self.ChatLogFile = self.Helpers.set_log_file(f"{self._confs['llm']['logs_path']}chat/")

    def prepare_model(self):
        """
        Prepares and initializes the model, tokenizer, and related configurations.

        This function performs the following:
        1. Configures OpenVINO generation settings.
        2. Initializes the model object and loads the model definition.
        3. Loads the model configuration, tokenizer, and the model itself.
        4. Logs the success or failure of each step.

        Raises:
            Logs any issues encountered during the initialization process.
        """
        # Configure OpenVINO generation settings
        self.ovconfig = openvino_genai.GenerationConfig()
        self.ovconfig.max_new_tokens = self._confs['llm']['max_tokens']

        # Initialize and load the model and tokenizer
        self.Model = Model(self._confs)

        self.Model.load_model_definition()
        self.Helpers.log_message(
            self.LogFile, "Model", "Info", "Updated agent definition XML loaded for runtime"
        )
        
        self.Model.load_config()
        self.Model.load_tokenizer()
        
        if self.Model.llm_tokenizer is not None:
            self.Helpers.log_message(
                self.LogFile, "Model", "Info", f"{self._confs['llm']['model']} tokenizer loaded successfully."
            )
        else:
            self.Helpers.log_message(
                self.LogFile, "Model", "Error", f"Could not load {self._confs['llm']['model']} tokenizer"
            )

        self.Model.load_model()
        if self.Model.llm is not None:
            self.Helpers.log_message(
                self.LogFile, "Model", "Info", f"{self._confs['llm']['model']} loaded successfully."
            )
        else:
            self.Helpers.log_message(
                self.LogFile, "Model", "Error", f"Could not load {self._confs['llm']['model']}"
            )
            
    def query(self, prompt):
        """
        Generate chatbot responses using the current conversation context.
        """
        # Add messages to history
        self.History.add_message(self.conversation_id, "system", self._confs["llm"]["system"])
        self.History.add_message(self.conversation_id, "user", prompt)

        # Get history and convert to tokens
        history = self.History.get_history(self.conversation_id)
        input_ids = self.Model.convert_history_to_token(history)

        # Create attention mask (1s for all tokens since we want to attend to everything)
        attention_mask = torch.ones_like(input_ids)

        # Define maximum token limit for the input
        MAX_TOKENS = self._confs["llm"]["max_tokens"]  # Adjust based on model

        # Keep the system prompt separate
        system_prompt = [{"role": "system", "content": self._confs["llm"]["system"]}]

        # Ensure the latest user/assistant message is always included
        sliding_window = [history[-1]]  # Always include the latest message

        # Add older messages while respecting the token limit
        for message in reversed(history[:-1]):
            temp_window = [message] + sliding_window
            temp_input_ids = self.Model.convert_history_to_token(system_prompt + temp_window)
            
            if temp_input_ids.shape[1] > MAX_TOKENS:
                break  # Stop when token limit is reached
            
            sliding_window = [message] + sliding_window

        # Combine the system prompt with the sliding window
        full_context = system_prompt + sliding_window

        # Convert to tokens
        input_ids = self.Model.convert_history_to_token(full_context)
        attention_mask = torch.ones_like(input_ids)

        # Setup custom text processor
        def process_streamed_text(text):
            """Clean and process streamed text tokens."""
            # Remove any special tokens that might have leaked through
            text = text.replace("<|endoftext|>", "").replace("<|pad|>", "")
            
            # Remove any incomplete UTF-8 characters at the end
            try:
                text.encode('utf-8').decode('utf-8')
            except UnicodeError:
                # If there's an error, remove the last character and try again
                text = text[:-1]
            
            return text

        # Setup streamer and skip special tokens
        streamer = TextIteratorStreamer(
            self.Model.llm_tokenizer,
            timeout=60.0,  
            skip_prompt=True,
            skip_special_tokens=True
        )

        # Generation arguments
        generate_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,  
            "pad_token_id": 0,  
            "max_new_tokens": self._confs['llm']['max_tokens'],
            "streamer": streamer,
            "do_sample": True,
            "temperature": 0.1,
            "top_p": 1.0,
        }

        # Handle stop tokens
        stop_tokens = self.Model.model_definition.get("stop_tokens", None)
        if stop_tokens:
            if isinstance(stop_tokens[0], str):
                stop_tokens = self.Model.llm_tokenizer.convert_tokens_to_ids(stop_tokens)
            stop_tokens = [StopOnTokens(stop_tokens)]
            generate_kwargs["stopping_criteria"] = StoppingCriteriaList(stop_tokens)

        # Generate in separate thread
        stream_complete = Event()
        def generate_and_signal_complete():
            try:
                self.Model.llm.generate(**generate_kwargs)
            except Exception as e:
                self.Helpers.log_message(
                    self.LogFile, "Error", "ERROR", f"Generation error: {str(e)}"
                )
            finally:
                stream_complete.set()

        Thread(target=generate_and_signal_complete).start()

        full_response = ""
        buffer = ""
        
        try:
            # Stream text with buffering
            for new_text in streamer:
                # Add new text to buffer
                buffer += new_text
                
                # Process buffer when we have enough text or hit certain characters
                if len(buffer) >= 10 or any(c in buffer for c in '.!?,\n'):
                    processed_text = process_streamed_text(buffer)
                    if processed_text:
                        full_response += processed_text
                        yield processed_text
                    buffer = ""
            
            # Process any remaining text in buffer
            if buffer:
                processed_text = process_streamed_text(buffer)
                if processed_text:
                    full_response += processed_text
                    yield processed_text
                    
        except Exception as e:
            self.Helpers.log_message(
                self.LogFile, "Error", "ERROR", f"Streaming error: {str(e)}"
            )
            
        # Add final response to history only if we got something
        if full_response:
            self.History.add_message(self.conversation_id, "genisys", full_response)
            self.Helpers.log_message(
                self.ChatLogFile, "GeniSysAI", "Response", full_response, True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py [INPUT|SERVER] [model_path]")
        sys.exit(1)

    command = sys.argv[1].upper()
    if command == "INPUT":
        LLMCore = LLMCore()
        LLMCore.Helpers.log_message(
            LLMCore.LogFile, "Inference", "INFO", "Running in input mode")
        
        try:
            while True:
                prompt = input("\nUser> ")
                LLMCore.Helpers.log_message(
                    LLMCore.ChatLogFile, "User", "Prompt", prompt, True)
                
                print("\nGeniSysAI> ", end='', flush=True)
                response_text = ""
                
                try:
                    for text_chunk in LLMCore.query(prompt):
                        if text_chunk:  # Only print non-empty chunks
                            print(text_chunk, end='', flush=True)
                            response_text += text_chunk
                    
                except Exception as e:
                    print(f"\nError generating response: {str(e)}")
                    LLMCore.Helpers.log_message(
                        LLMCore.LogFile, "Error", "ERROR", str(e))
                
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"\nError: {str(e)}")
            LLMCore.Helpers.log_message(
                LLMCore.LogFile, "Error", "ERROR", str(e))