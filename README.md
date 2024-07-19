# photo-display
Connect a Raspberry Pi to an Immich Server to display an album on an Inky Impression display

## Running
make sure you have imagemagick installed on your pi

**./setup.sh install** - to install

**./setup.sh install cron** - to install a cron job

**./setup.sh install systemd** - to install a timed systemd service

**./setup.sh uninstall** - to uninstall

installation will attempt to sync, build, and - with dkms - install https://github.com/RetroZelda/inky-impression-btn-driver

modify ./config.json to add your immich server url, api key, and desired albums. 
modify ./scripts/monitor_inky_impression.sh to change what each of the buttons will do when pressed.  
  by default Button A will sync and choose another picture and Button B will turn on NetworkManager

./run.sh will run everything.  
use --config to point to a config.json file
use --offline to make it run offline.  Make sure to run it once online so it can sync with immich
use --no-screen to run without connecting to a screen.  useful for testing and debugging
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
