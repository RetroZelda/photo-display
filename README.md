# photo-display
Connect a Raspberry Pi to an Immich Server to display an album on an Inky Impression display

## Running
make sure you have SPI enabled on your pi.  To enable it run `sudo raspi-config` and find it in "Interface Options"

**./setup.sh install** - to install

**./setup.sh install cron** - to install a cron job

**./setup.sh install systemd** - to install a timed systemd service

**./setup.sh uninstall** - to uninstall


modify ./config.json to add your immich server url, api key, and desired albums. 

./run.sh will run everything.  
use --offline to make it run offline.  Make sure to run it once online so it can sync with immich
use --force-refresh to clean all local data and redownload everything.  Use this if you change your config.json.  Must be online.
use --clean to clean all local data

./run_with_wifi.sh will attempt to startup wifi and shutdown wifi before running the script.  If it cant connect to wifi then it will run with --offline

## Configuration:

**ImmichServerUrl** - Server Address to your Immich instance

**ApiKey** - API Key for your immich instance

**Albums** - Array of album Ids 

**SleepTime** - Time to wait between each photo update.  Set to 0 to have it run once - useful for cron scheduling

**Saturation** - Saturation value for the image

**ImageCachePath** - folder path where downloaded and resized images get cached

**ImageDatabaseFile** - location to place photos.db file

**PreferredOrientation** - What is the preferred orientation the screen will reside in.  can be "landscape" or "portrait"

**ForceOrientation** - Will images get rotated to match the preferred orientation.

**PreserveAspect** - Will image aspect ratio be preserved

**Letterbox** - Will we letterbox scaled images when their aspect ratios dont match the screen

**LetterboxColor** - Background color of the letterbox
