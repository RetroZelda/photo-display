
import requests
import json
import os

API_ADDR = "/api"
GET_ALBUMS_API = f"/albums"
GET_ASSETINFO_API = f"/assets"
POST_DOWNLOADARCHIVE_API = f"/download/archive"

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
        self.server_url = f"{server_url}{API_ADDR}"
        self.api_key = api_key
        self.albums = {}
    
    def get_album(self, album_id) -> ImmichAlbum:
        return self.albums.get(album_id)
    
    def sync_album(self, album_id) -> ImmichAlbum:
        url = f"{self.server_url}{GET_ALBUMS_API}/{album_id}"

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
    
    def get_asset_info(self, asset_id):
        url = f"{self.server_url}{GET_ASSETINFO_API}/{asset_id}"

        payload = {}
        headers = {
        'Accept': 'application/json',
        'x-api-key': self.api_key
        }

        print(f"Fetching asset info {asset_id}")
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            asset_info = ImmichAssetData(json.loads(response.text))
            return asset_info            
        else:
            print(f"Failed to fetch asset info. Status code: {response.status_code}")

        return None
    
    def download_assets(self, assets_to_download, output_file, force = False):

        if len(assets_to_download) == 0:
            print(f"Downloading 0 assets.... dumbass")
            return False
        
        url = f"{self.server_url}{POST_DOWNLOADARCHIVE_API}"
        payload = json.dumps({
            "assetIds": [d['asset_id'] for d in assets_to_download]
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'octet-stream',
            'x-api-key': self.api_key
        }

        print(f"Downloading {len(assets_to_download)} assets")
        with requests.post(url, headers=headers, data=payload, stream=True) as response:
            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"Assets downloaded to: {output_file}")
                return True
            else:
                print(f"Failed to download assets. Status code: {response.status_code}:\n{response.text}")

        return False




