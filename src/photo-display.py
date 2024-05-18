import os
import time
import random
import argparse
import subprocess
from PIL import Image

from immich_data import ImmichConnection
from image_database import ImageData
from image_database import ImageDatabase
from settings import Settings
from screen import Screen

def OpenImage(image, resolution):    
    print(f"Opening {image.file_path}")
    resizedimage = Image.open(image.file_path).resize(resolution.resolution)
    return resizedimage    

def main(args):
    settings = Settings(args.config)    

    immich = ImmichConnection(settings.ImmichServerUrl, settings.ApiKey)
    album_data = []
    for album_id in settings.Albums:
        album = immich.sync_album(album_id)
        if album is not None:
            album_data.append(album)

    screen = Screen(settings)

    if not args.no_screen:
        screen.init_inky()

    database = ImageDatabase(settings, screen.resolution)    
    database.process_albums(immich)
    database.purge_missing(immich)
        
    while True:            
        target_image = database.get_random_image()
        if target_image is not None:          
            image = OpenImage(target_image, screen.resolution)
            print(f"Displaying {target_image.file_path}")
            screen.set_image(image)
        
        print(f"Sleeping for {settings.SleepTime} seconds...")
        time.sleep(settings.SleepTime)
    
parser = argparse.ArgumentParser(description='Display photos from an Immich album onto an Inky Screen.')
parser.add_argument('--config', help='config json file', default="./config.json", required=False)
parser.add_argument('--no-screen', help='dont init inky screen. useful for debugging', action='store_true', required=False)
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
    
