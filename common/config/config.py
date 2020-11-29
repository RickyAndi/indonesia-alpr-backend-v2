
import os
import pathlib
import json

class Config:
    def __init__(self, json_config_path):
        with open(json_config_path) as f:
            self.config = json.load(f)

    def get(self, key_string):
        keys = key_string.split(".")
        
        selected_config = self.config

        for key in keys:
            selected_config = selected_config[key]

        return selected_config 