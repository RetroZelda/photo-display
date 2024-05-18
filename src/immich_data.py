
import requests
import json
import os

class ImmichAssetData:
    def __init__(self, asset_dict):
        self.asset_dict = asset_dict

    def __getattr__(self, name):
        return self.asset_dict.get(name)
    
class ImmichAlbum(ImmichAssetData):
    def __init__(self, asset_dict):
        super().__init__(asset_dict)
        self.album_id = self.id
        self.image_assets = {}

        for asset_data in self.assets:
            asset = ImmichAssetData(asset_data)
            if asset.type== "IMAGE":
                self.add_asset(asset)
            else:
                print(f"Ignoring asset {asset.id} from Album {self.album_id} - we dont handle \"{asset.type}\" types")

    def add_asset(self, asset : ImmichAssetData):
        self.image_assets[asset.id] = asset

    def get_asset(self, asset_id) -> ImmichAssetData:
        return self.image_assets.get(asset_id)
            

class ImmichConnection:
    def __init__(self, server_url, api_key):
        self.server_url = server_url
        self.api_key = api_key
        self.albums = {}
    
    def get_album(self, album_id) -> ImmichAlbum:
        return self.albums.get(album_id)
    
    def sync_album(self, album_id) -> ImmichAlbum:
        url = f"{self.server_url}/api/album/{album_id}"

        payload = {}
        headers = {
        'Accept': 'application/json',
        'x-api-key': self.api_key
        }

        print(f"Fetching album {album_id}")
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            album_info = ImmichAlbum(json.loads(response.text))
            self.albums[album_id] = album_info
            return album_info            
        else:
            print(f"Failed to fetch album. Status code: {response.status_code}")

        return None
    
    def download_asset(self, image_asset : ImmichAssetData, target_dir, force = False):

        url = f"{self.server_url}/api/download/asset/{image_asset.id}"
        output_file = os.path.join(target_dir, image_asset.originalFileName)

        if os.path.exists(output_file):
            print(f"Asset already exists {image_asset.originalFileName}")
            if not force:
                return output_file

        payload = {}
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }

        print(f"Downloading {image_asset.originalFileName}")
        with requests.post(url, headers=headers, data=payload, stream=True) as response:
            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"Asset downloaded to: {output_file}")
                return output_file
            else:
                print(f"Failed to download asset. Status code: {response.status_code}:\n{response.text}")


        return None




