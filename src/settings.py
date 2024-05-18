import os
import json
from pathlib import Path

class Settings:
    def __init__(self, file_path):
        self.load_settings(file_path)

    def __getattr__(self, name):
        return self.settings_dict['Settings'].get(name)

    def get(self, name, default):
        return self.settings_dict.get(name, default)
    
    def load_settings(self, file_path):
        try:
            with open(file_path, 'r') as file:
                self.settings_dict = json.load(file)

                print("Settings loaded successfully")
                print(json.dumps(self.settings_dict, indent=2))

                print(f"Verifying {self.DataPath}")
                Path(self.DataPath).mkdir(parents=True, exist_ok=True)

                print(f"Verifying {self.ImageCachePath}")
                Path(self.ImageCachePath).mkdir(parents=True, exist_ok=True)
                return True
            
        except FileNotFoundError:
            print(f"File '{file_path}' not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON in '{file_path}'.")
        return False
            