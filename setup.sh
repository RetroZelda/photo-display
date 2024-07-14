#!/bin/bash

venv_name="venv"
current_user=$(whoami)
current_directory=$(pwd)
systemd_directory="/etc/systemd/system"
timer_directory="/etc/systemd/system/timers.target.wants"
wifi_script="$current_directory/run_with_wifi.sh"

# timers
cron="0 * * * * "
timer_rule="OnBootSec=1s
OnUnitActiveSec=1h"

unit_file="$systemd_directory/photo-display.service"
timer_file="$systemd_directory/photo-display.timer"

install_application() {
    echo "Installing environment..."
    
    # Create virtual environment
    python3 -m venv "$venv_name" >> /dev/null

    # Activate virtual environment
    source "$venv_name/bin/activate" >> /dev/null

    # Install dependencies
    pip3 install inky[rpi,example-depends] >> /dev/null
    pip3 install Pillow >> /dev/null
    pip3 install requests >> /dev/null
}

uninstall_application() {
    echo "Uninstalling application..."
    rm -drf $venv_name
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

generate_systemd_service() {
    unit_content="[Unit]
Description=Photo Display service

[Service]
WorkingDirectory=$current_directory
ExecStart=$wifi_script
Type=simple
User=$current_user

[Install]
WantedBy=multi-user.target
"

    timer_content="[Unit]
Description=Run Photo Display service every hour

[Timer]
$timer_rule
Persistent=true

[Install]
WantedBy=timers.target
"

    # Write the unit content to the unit file
    echo "Creating systemd service"
    echo "$unit_content" | sudo tee "$unit_file" > /dev/null
    echo "$timer_content" | sudo tee "$timer_file" > /dev/null

    echo "Reloading systemd daemon"
    sudo systemctl daemon-reload

    echo "Starting timer"
    sudo systemctl enable --now photo-display.timer

    echo "Running Once"
    sudo systemctl restart photo-display.timer
    sudo systemctl start photo-display.service
}

remove_systemd_service() {

    echo "Removing systemd services and timers"
    sudo systemctl stop photo-display.timer
    sudo systemctl disable photo-display.timer
    sudo rm -f $timer_file
    sudo rm -f $unit_file

    echo "Reloading systemd daemon"
    systemctl daemon-reload
}

if [[ "$1" == "install" ]]; then
    install_application

    if [[ "$2" == "cron" ]]; then
        create_cron_job
        echo "Cron setup complete."
        echo "Make sure to edit your config to have a SleepTime of 0!"
    elif [[ "$2" == "systemd" ]]; then
        generate_systemd_service
        echo "Systemd service created."
        echo "Make sure to edit your config to have a SleepTime of 0!"
    fi
    sleep 3
    echo "Setup complete."

elif [[ "$1" == "uninstall" ]]; then
    remove_cron_job
    uninstall_application
    remove_systemd_service
    echo "Uninstallation complete."
else
    echo "Usage: $0 [install|uninstall]"
    echo "          optionally [install cron] to setup as a cron job"
    echo "          optionally [install systemd] to setup as a systemd service"
    exit 1
fi
