
import os
import sys
import time
import fcntl
import atexit
import argparse
import subprocess
from PIL import Image
from urllib.parse import urlparse

from immich_data import ImmichConnection
from image_database import ImageDatabase
from settings import Settings
from screen import Screen

def sanitize_host(url):
    """
    Strip URL components and extract the host.
    
    :param url: The URL to sanitize.
    :return: The sanitized host.
    """
    parsed_url = urlparse(url)
    host = parsed_url.netloc or parsed_url.path
    # Remove 'www.' if present
    if host.startswith('www.'):
        host = host[4:]
    return host

def ping_server(url, count=4, timeout=2):
    """
    Ping a server to check if a connection can be made.

    :param host: The hostname or IP address of the server.
    :param count: Number of ping requests to send.
    :param timeout: Timeout for each ping request in seconds.
    :return: True if the server is reachable, False otherwise.
    """
    host = sanitize_host(url)
    print(f"Checking connection to {host}")
    try:
        # Perform the ping command
        output = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Check the return code
        if output.returncode == 0:
            print(f"Ping to {host} was successful.")
            return True
        else:
            print(f"Ping to {host} failed.")
            return False

    except Exception as e:
        print(f"An error occurred while pinging {host}: {e}")
        return False
    
def OpenImage(image, resolution):    
    print(f"Opening {image.file_path}")
    resizedimage = Image.open(image.file_path).resize(resolution.resolution)
    return resizedimage    

def main(args):
    settings = Settings(args.config)    
    screen = Screen(settings)

    if args.clean:
        database = ImageDatabase(settings, screen.resolution)
        database.purge_all()
        return

    if not args.no_screen:
        screen.init_inky()

    immich = ImmichConnection(settings.ImmichServerUrl, settings.ApiKey)
    database = ImageDatabase(settings, screen.resolution)

    if not args.offline:

        # ping hte server to ensure we have a connection
        if not ping_server(settings.ImmichServerUrl):
            print("Unable to connect to Immich server.  Running offline.")
        else:
            no_connection = False

            # wipe everything local before we start
            if args.force_refresh:
                database.purge_all()

            for album_id in settings.Albums:

                # bit of a hack so we dont purge everything if we fail to get an album
                # TODO: fix this up so we only attempt to purge successful albums
                if immich.sync_album(album_id) is None:
                    no_connection = True
                    break
            
            if not no_connection:
                database.purge_missing(immich)
                database.process_albums(immich)
      
    while True:            
        target_image = database.get_random_image()
        if target_image is not None:          
            image = OpenImage(target_image, screen.resolution)
            print(f"Displaying {target_image.file_path}")
            screen.set_image(image)

        if settings.SleepTime > 0:
            print(f"Sleeping for {settings.SleepTime} seconds...")
            time.sleep(settings.SleepTime)
        else:
            print(f"Sleep time set for {settings.SleepTime} seconds... Exiting")
            break
    
parser = argparse.ArgumentParser(description='Display photos from an Immich album onto an Inky Screen.')
parser.add_argument('--config', help='config json file', default="./config.json", required=False)
parser.add_argument('--offline', help='dont connect to the network and use what is in the database', action='store_true', required=False)
parser.add_argument('--no-screen', help='dont init inky screen. useful for debugging', action='store_true', required=False)
parser.add_argument('--force-refresh', help='Force refresh by clearing everything local and redownloading all photos. Must be online.', action='store_true', required=False)
parser.add_argument('--clean', help='Clear everything local', action='store_true', required=False)


lock_file_path = "/tmp/photo_display.lock"
lock_file = None

def release_lock():
    if lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
            os.remove(lock_file_path)
            print("Lock released.")
        except Exception as e:
            print(f"Failed to release lock: {e}")
            
if __name__ == "__main__":
    args = parser.parse_args()

    # handle the file lock
    atexit.register(release_lock) # ensure we release the lock
    try:
        lock_file = open(lock_file_path, "w")
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("Another instance of the script is already running.")
        sys.exit(1)

    try:
        main(args)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        release_lock()
    
