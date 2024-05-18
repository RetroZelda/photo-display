import os
import csv
import random
import subprocess
from datetime import datetime

from immich_data import ImmichConnection, ImmichAlbum, ImmichAssetData
from settings import Settings
from screen import ScreenResolution

class ImageData:
    def __init__(self, album_id, asset_id, file_path = None, last_used_date = '1993-12-29 00:00:00', use_count = '0'):
        self.album_id = album_id
        self.asset_id = asset_id
        self.file_path = file_path
        self.last_used_date = datetime.strptime(last_used_date, '%Y-%m-%d %H:%M:%S')
        self.use_count = int(use_count)

    def to_list(self):
        return [self.album_id, 
                self.asset_id, 
                self.file_path, 
                self.last_used_date.strftime('%Y-%m-%d %H:%M:%S'), 
                self.use_count]

    @classmethod
    def from_list(cls, data):
        return cls(*data)
    
    def get_resolution(self) -> ScreenResolution:
        # Use the identify command to get image dimensions
        identify_command = ['identify', '-format', '%w %h', self.file_path]
        identify_output = subprocess.check_output(identify_command, universal_newlines=True)
        width, height = map(int, identify_output.split())
        return ScreenResolution([width, height])

    def calculate_weight(self, now : datetime):
        time_difference = now - self.last_used_date
        hours = time_difference.total_seconds() / 3600 
        weight = (1 + hours) / (1 + self.use_count) 
        return weight
   
    # mark the image as used so we can track it
    def mark_used(self):
        current_datetime = datetime.now()
        self.last_used_date = current_datetime
        self.use_count = self.use_count + 1

class ImageDatabase:
    def __init__(self, settings : Settings, target_resolution : ScreenResolution):
        self.settings = settings
        self.database_file = settings.ImageDatabaseFile
        self.image_directory = settings.ImageCachePath
        self.data = []

        self.target_resolution = target_resolution

        # If the file doesn't exist, create an empty DataFrame as our header using ImageData members 
        if not os.path.exists(self.database_file):
            print("Creating database at ", self.database_file)
            self.save_changes()
        else:
            self.load_data()

    def get_resize_command(self, image_data : ImageData):
        command = [
            'convert',
            image_data.file_path, # input path
        ]

        # set the resolution
        resolution = self.target_resolution.resolution_string
        if self.settings.PreserveAspect:
            resolution+= '>'
        command.extend(['-resize', resolution])

        # handle if we need to use a letterbox
        if self.settings.Letterbox:
            command.extend(['-background', self.settings.LetterboxColor])
            command.extend(['-gravity', 'center'])
            command.extend(['-extent', self.target_resolution.resolution_string])

        command.append(image_data.file_path) # output path
        return command
                        
    def get_image(self, album_id, asset_id) -> ImageData:
        for image_data in self.data:
            if image_data.album_id == album_id and image_data.asset_id == asset_id:
                return image_data
        return None
    
    def process_albums(self, immich : ImmichConnection):

        for album_id, album in immich.albums.items():
            for asset_id, asset in album.image_assets.items():

                # check if an image exists
                image_data = self.get_image(album_id, asset_id)
                if image_data is None:
                    image_data = ImageData(album_id, asset_id)
                    self.data.append(image_data)
                    
                if image_data.file_path is None or not os.path.exists(image_data.file_path):
                    asset_file = immich.download_asset(asset, self.image_directory, False)
                    image_data.file_path = asset_file

                # ensure the image is the proper size
                cur_resolution = image_data.get_resolution()
                if cur_resolution != self.target_resolution:
                    resize_command = self.get_resize_command(image_data)
                    print(f"Resizing {image_data.file_path} to {self.target_resolution.resolution_string}")
                    subprocess.run(resize_command)
                    
        self.save_changes()
    
    def purge_missing(self, immich : ImmichConnection):

        # scan for albums and assets that are no longer in the immich data
        to_delete = []
        for image_data in self.data:
            album = immich.get_album(image_data.album_id)
            if album is None:
                print(f"Removing {image_data.file_path} because album {image_data.album_id} is missing")
                to_delete.append(image_data)
                continue
            asset = album.get_asset(image_data.asset_id)
            if asset is None:
                print(f"Removing {image_data.file_path} because asset {image_data.asset_id} is missing from album {image_data.album_id}")
                to_delete.append(image_data)
                continue

        # purge them from disk and memory
        for image_data in to_delete:
            self.data.remove(image_data)
            if os.path.exists(image_data.file_path):
                os.remove(image_data.file_path)
                print(f"{image_data.file_path} deleted successfully.")
                
        self.save_changes()
        
    def load_data(self):
        with open(self.database_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.data.append(ImageData.from_list(row))
            print("Database loaded successfully:")
                
    def save_changes(self):
        with open(self.database_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for image_data in self.data:
                writer.writerow(image_data.to_list())
            print("Database changes saved to ", self.database_file)
    
    def print(self):
        print(self.data)

    def get_random_image(self) -> ImageData:
        now = datetime.now()

        self.data = sorted(self.data, key=lambda x: x.calculate_weight(now), reverse=False)
        weights = [image.calculate_weight(now) for image in self.data]
        total_weight = sum(weights)

        # Generate a random number between 0 and the total weight
        rand_num = random.uniform(0, total_weight)
        cumulative_weight = 0

        # Iterate through the images and select one based on weighted probability
        for image, weight in zip(self.data, weights):
            cumulative_weight += weight
            if rand_num <= cumulative_weight:
                image.mark_used()
                self.save_changes()
                return image
