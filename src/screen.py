import os
import time
import random
import requests
import subprocess

from inky.auto import auto
from PIL import Image

from settings import Settings

class ScreenResolution:
    def __init__(self, resolution_tuple):
        self.update_resolution(resolution_tuple)
    
    def update_resolution(self, resolution_tuple):
        self.resolution = resolution_tuple
        self.width, self.height = resolution_tuple
        self.resolution_string = f"{self.width}x{self.height}"
        self.orientation = "portrait" if self.height > self.width else "landscape"

class Screen:
    def __init__(self, settings : Settings):
        self.inky = None
        self.resolution = ScreenResolution(resolution_tuple = [600, 448])

        self.settings = settings        
        self.saturation = settings.get("Saturation", 0.5)
        
    def init_inky(self):
        self.inky = auto()
        self.resolution = ScreenResolution(self.inky.resolution)

    def set_image(self, image : Image):
        if self.inky is not None:
            self.inky.set_image(image, saturation=self.saturation)
            self.inky.show()

