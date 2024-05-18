# photo-display
Connect a Raspberry Pi to an Immich Server to display an album on an Inky Impression display

modify ./config.json to add your immich server url, api key, and desired albums.

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
