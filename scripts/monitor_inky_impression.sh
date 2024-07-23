#!/bin/bash

# Paths to the sysfs files to monitor for each inky impression button
declare -A MONITOR_FILES=(
    ["/sys/kernel/inky-impression/btn_a"]="handle_btn_a"
    ["/sys/kernel/inky-impression/btn_b"]="handle_btn_b"
    ["/sys/kernel/inky-impression/btn_c"]="handle_btn_c"
    ["/sys/kernel/inky-impression/btn_d"]="handle_btn_d"
)

# Last known values of the buttons
declare -A LAST_VALUES=(
    ["/sys/kernel/inky-impression/btn_a"]=""
    ["/sys/kernel/inky-impression/btn_b"]=""
    ["/sys/kernel/inky-impression/btn_c"]=""
    ["/sys/kernel/inky-impression/btn_d"]=""
)

# The systemd services to start with buttons
PHOTO_CHANGE_NAME="photo-display-update" # btn_a
PHOTO_SYNC_NAME="photo-display-sync" # btn_b
NETWORKING_NAME="NetworkManager" # btn_b

handle_btn_a() {
    local value=$1
    echo "Button A value is $value."

    if [ "$value" -eq 1 ]; then
        if ! systemctl is-active --quiet "$PHOTO_CHANGE_NAME" && ! systemctl is-active --quiet "$PHOTO_SYNC_NAME"; then
            echo "Starting $PHOTO_CHANGE_NAME because btn_a value is 1"
            systemctl start "$PHOTO_CHANGE_NAME"
        else
            echo "$PHOTO_CHANGE_NAME is already running"
        fi
    fi
}

handle_btn_b() {
    local value=$1
    echo "Button B value is $value."

    if [ "$value" -eq 1 ]; then
        if ! systemctl is-active --quiet "$PHOTO_CHANGE_NAME" && ! systemctl is-active --quiet "$PHOTO_SYNC_NAME"; then
            echo "Starting $PHOTO_SYNC_NAME because btn_b value is 1"
            systemctl start "$PHOTO_SYNC_NAME"
        else
            echo "$PHOTO_SYNC_NAME is already running"
        fi
    fi
}

handle_btn_c() {
    local value=$1
    echo "Button C value is $value."

    # TODO: add custom logic here
}

handle_btn_d() {
    local value=$1
    echo "Button D value is $value."
    
    if [ "$value" -eq 1 ]; then
        if ! systemctl is-active --quiet "$NETWORKING_NAME"; then
            echo "Starting $NETWORKING_NAME because btn_d value is 1"
            systemctl start "$NETWORKING_NAME"
        else
            echo "$NETWORKING_NAME is already running"
        fi
    fi
}

# get initial state
for filepath in "${!MONITOR_FILES[@]}"; do
    value=$(cat $filepath | tr -d '\n')
    LAST_VALUES[$filepath]=$value
done

# Start monitoring the files
while true; do
    for filepath in "${!MONITOR_FILES[@]}"; do
        value=$(cat $filepath | tr -d '\n')
        if [ "${LAST_VALUES[$filepath]}" != "$value" ]; then
            LAST_VALUES[$filepath]=$value
            ${MONITOR_FILES[$filepath]} "$value"
        fi
    done
    sleep 1
done