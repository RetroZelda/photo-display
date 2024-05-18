#!/bin/bash

venv_name="venv"
current_directory=$(pwd)
wifi_script="$current_directory/run_with_wifi.sh"
cron="0 * * * * "

install_application() {
    echo "Installing application..."
    
    # Create virtual environment
    python3 -m venv "$venv_name"

    # Activate virtual environment
    source "$venv_name/bin/activate"

    # Install dependencies
    pip3 install inky[rpi,example-depends]
    pip3 install Pillow
    pip3 install requests
}

uninstall_application() {
    echo "Uninstalling application..."
    rm -drf $venv_name
    rm -drf ./data
}

create_cron_job() {
    echo "Creating cron job..."
    # Add a cron job to run ./run_with_wifi.sh every hour
    (crontab -l ; echo "$cron $wifi_script") | crontab -
    echo "Cron job created."
}

remove_cron_job() {
    echo "Removing cron job..."
    # Use `grep -v` to remove the line containing the command
    (crontab -l | grep -v "$wifi_script") | crontab -
    echo "Cron job removed."
}

if [[ "$1" == "install" ]]; then
    install_application

    if [[ "$2" == "cron" ]]; then
        create_cron_job
        echo "Cron setup complete."
        echo "Make sure to edit your config to have a SleepTime of 0!"
    else
        echo "Setup complete."
    fi
elif [[ "$1" == "uninstall" ]]; then
    remove_cron_job
    uninstall_application
    echo "Uninstallation complete."
else
    echo "Usage: $0 [install|uninstall]"
    echo "          optionally [install cron] to setup as a cron job"
    exit 1
fi