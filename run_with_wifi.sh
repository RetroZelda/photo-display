#!/bin/bash

# Function to check if WiFi systemd service is active
check_wifi_status() {
    systemctl is-active NetworkManager.service
    return $?
}

# Function to start WiFi systemd service
start_wifi_service() {
    sudo systemctl start NetworkManager.service
}

# Function to stop WiFi systemd service
stop_wifi_service() {
    sudo systemctl stop NetworkManager.service
}

# Function to check internet access by pinging a known website
check_internet_access() {
    ping -c 1 google.com &> /dev/null
    return $?
}

# Main script
wifi_connected=false
internet_connected=false

# Check WiFi status
if ! check_wifi_status; then
    echo "WiFi is not active. Starting WiFi service..."
    start_wifi_service
    
    # Wait for WiFi to be active
    for ((i=0; i<30; i++)); do
        sleep 1
        if check_wifi_status; then
            echo "WiFi service is active."
            wifi_connected=true
            sleep 5
            break
        elif ((i == 29)); then
            echo "Failed to enable WiFi."
        fi
    done
else
    wifi_connected=true
fi

# Check internet access
echo "Checking for internet access..."
for ((i=0; i<30; i++)); do
    if check_internet_access; then
        echo "Internet is active."
        internet_connected=true
        sleep 1
        break
    elif ((i == 29)); then
        echo "Unable to connect to the internet."
    fi
    sleep 1
done

if $wifi_connected && $internet_connected; then
    echo "Connected to WiFi and internet access is available."
    ./run.sh
else
    echo "Cannot connect to WiFi or no internet access."
    ./run.sh --offline
fi

# Turn off WiFi
stop_wifi_service
echo "WiFi turned off."
