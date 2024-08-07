import os
import csv
import random
import zipfile
import tempfile
import subprocess
from tqdm import tqdm
from datetime import datetime

from immich_data import ImmichConnection, ImmichAlbum, ImmichAssetData
from settings import Settings
from screen import ScreenResolution
from helpers import Orientation

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
    
    def enforce_exif_rotation(self, force_jpg):

        # Use the identify command to get image dimensions and then strif the exif data
        command = ['convert', self.file_path, "-auto-orient", "-strip"]
        if force_jpg:
            print(f"\tIt was HEIC so we will force it to be a jpg.  fuck apple")
            command.append(self.file_path + ".jpg")
        else:
            command.append(self.file_path)
        command_output = subprocess.check_output(command, universal_newlines=True)

        if force_jpg:
            os.remove(self.file_path) # remove the old file type because it wasnt replaced during the command
            self.file_path = self.file_path + ".jpg"
            
            
    
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

    def get_orientation(self, asset_info : ImmichAssetData) -> Orientation:

        if asset_info is not None:
            exif_info = asset_info.asset_dict["exifInfo"]
            if exif_info is not None:
                value = exif_info["orientation"]
                if value is not None:
                    if value in [1, 2, 3, 4]:
                        return Orientation.LANDSCAPE
                    elif value in [5, 6, 7, 8]:
                        return Orientation.PORTRAIT

        # if not part of the asset data, return based on the resolution
        resolution = self.get_resolution()
        return resolution.orientation


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

    def get_resize_command(self, image_data : ImageData, asset_info : ImmichAssetData = None):
        command = [
            'convert',
            image_data.file_path, # input path
            '-strip',
            '-auto-orient'
        ]

        # handle needed rotations
        asset_orientation = image_data.get_orientation(asset_info)
        preferred_orientation = self.settings.get_preferred_orientation()
        target_orientation = self.target_resolution.orientation


        if self.settings.ForceOrientation:
            
            if preferred_orientation == Orientation.LANDSCAPE and target_orientation == Orientation.PORTRAIT:
                if asset_orientation == Orientation.LANDSCAPE:
                    command.extend(['-rotate', "-90"])
                if asset_orientation == Orientation.PORTRAIT:
                    command.extend(['-rotate', "-90"])
            elif preferred_orientation == Orientation.PORTRAIT and target_orientation == Orientation.LANDSCAPE:
                if asset_orientation == Orientation.LANDSCAPE:
                    command.extend(['-rotate', "-90"])
                if asset_orientation == Orientation.PORTRAIT:
                    command.extend(['-rotate', "-90"])
        else:
            # Rotate based on current and target orientation
            if target_orientation == Orientation.LANDSCAPE and asset_orientation == Orientation.PORTRAIT:
                command.extend(['-rotate', "90"])
            elif target_orientation == Orientation.PORTRAIT and asset_orientation == Orientation.LANDSCAPE:
                command.extend(['-rotate', "-90"])

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

        assets_to_download = []
        for album_id, album in immich.albums.items():
            for asset_id, asset in album.image_assets.items():

                # check if an image exists
                image_data = self.get_image(album_id, asset_id)
                if image_data is None:
                    image_data = ImageData(album_id, asset_id)
                    self.data.append(image_data)

                if image_data.file_path is not None and os.path.exists(image_data.file_path):
                    continue

                output_file = os.path.join(self.image_directory, asset.originalFileName)
                if os.path.exists(output_file):
                    print(f"Asset already exists {asset.originalFileName}")
                    continue

                assets_to_download.append({'asset':asset, 'album_id':album_id, 'asset_id':asset_id})

        if len(assets_to_download) == 0:
            print("No new Assets to download")
            return
        
        # Create a temporary file
        temp_file_name = ""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_name = temp_file.name  

        download_success = immich.download_assets(assets_to_download, temp_file_name, False)
        if not download_success:
            print("Failed to download assets")
        else:
            print(f"Extracting new assets to {self.image_directory}")
            with zipfile.ZipFile(temp_file_name, 'r') as zip_ref:
                
                file_list = zip_ref.namelist()
                with tqdm(total=len(file_list), 
                          desc=f"Extracting to {self.image_directory}", 
                          unit='file') as progress_bar:
                    for file in file_list:
                        zip_ref.extract(file, self.image_directory)
                        progress_bar.update(1)

            for asset in assets_to_download:
                print(f"Processing new image {asset['asset'].originalFileName}")
                image_data = self.get_image(asset['album_id'], asset['asset_id'])
                if image_data is None:
                    image_data = ImageData(asset['album_id'], asset['asset_id'])
                    self.data.append(image_data)
                image_data.file_path = f"{self.image_directory}/{asset['asset'].originalFileName}"

                # HACK: Force heic to be jpg
                force_jpg = False
                if asset['asset'].originalMimeType == 'image/heic':
                    force_jpg = True

                image_data.enforce_exif_rotation(force_jpg) # apply exif rotation and then wipe exif

                # ensure the image is the proper size
                asset_info = immich.get_asset_info(asset['asset_id'])
                cur_resolution = image_data.get_resolution()
                if cur_resolution != self.target_resolution:
                    resize_command = self.get_resize_command(image_data, asset_info)
                    print(f"Resizing {image_data.file_path} to {self.target_resolution.resolution_string}")
                    subprocess.run(resize_command)


                    
        os.remove(temp_file_name)
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

    def purge_all(self):
        # purge database from disk and memory
        while len(self.data) > 0:
            image_data = self.data[0]
            if os.path.exists(image_data.file_path):
                os.remove(image_data.file_path)
                print(f"Deleted: {image_data.file_path}.")
            else:
                print(f"Missing: {image_data.file_path}.")
            self.data.remove(image_data)

        # purge all remaining files from disk
        for filename in os.listdir(self.settings.ImageCachePath):
            file_path = os.path.join(self.settings.ImageCachePath, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed: {file_path}.")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
                
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
