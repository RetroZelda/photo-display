# photo-display
Connect a Raspberry Pi to an Immich Server to display an album on an Inky Impression display

## Installation:
make sure you have SPI enabled on your pi.  To enable it run `sudo raspi-config` and find it in "Interface Options"

**./setup.sh install** - to install <br/> 
**./setup.sh install cron** - to install a cron job <br/> 
**./setup.sh install systemd** - to install a timed systemd service <br/> 
**./setup.sh uninstall** - to uninstall<br/> 

installation will attempt to sync, build, and - with dkms - install https://github.com/RetroZelda/inky-impression-btn-driver

## Running:
**./run.sh** will run everything.  <br/> 
**./run_with_wifi.sh** will attempt to startup wifi and shutdown wifi before running the script.  If it cant connect to wifi then it will run with --offline <br/> 

## Args:
**--config** to point to a config.json file <br/> 
**--offline** to make it run offline.  Make sure to run it once online so it can sync with immich <br/> 
**--no-screen** to run without connecting to a screen.  useful for testing and debugging <br/> 
**--force-refresh** to clean all local data and redownload everything.  Use this if you change your config.json.  Must be online. <br/> 
**--clean** to clean all local data <br/> 

## Configuration:

modify **./config.json** to add your immich server url, api key, and desired albums.  <br/> 
modify **./scripts/monitor_inky_impression.sh** to change what each of the buttons will do when pressed.  <br/> 

**ImmichServerUrl** - Server Address to your Immich instance <br/> 
**ApiKey** - API Key for your immich instance <br/> 
**Albums** - Array of album Ids <br/> 
**SleepTime** - Time to wait between each photo update.  Set to 0 to have it run once - useful for cron scheduling <br/> 
**Saturation** - Saturation value for the image <br/> 
**ImageCachePath** - folder path where downloaded and resized images get cached <br/> 
**ImageDatabaseFile** - location to place photos.db file <br/> 
**PreferredOrientation** - What is the preferred orientation the screen will reside in.  can be "landscape" or "portrait" <br/> 
**ForceOrientation** - Will images get rotated to match the preferred orientation. <br/> 
**PreserveAspect** - Will image aspect ratio be preserved <br/> 
**Letterbox** - Will we letterbox scaled images when their aspect ratios dont match the screen <br/> 
**LetterboxColor** - Background color of the letterbox <br/> 
