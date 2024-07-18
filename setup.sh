#!/bin/bash

venv_name="venv"
current_user=$(whoami)
current_directory=$(pwd)
systemd_directory="/etc/systemd/system"
timer_directory="/etc/systemd/system/timers.target.wants"
wifi_script="$current_directory/run_with_wifi.sh"
monitor_script="$current_directory/scripts/monitor_inky_impression.sh"

# button driver repository URL and the directory name
REPO_URL="https://github.com/RetroZelda/inky-impression-btn-driver.git"
REPO_DIR="inky-impression-btn-driver"
MODULE_NAME="inky_impression_btn_driver"

# timers
cron="0 * * * * "
timer_rule="OnBootSec=1min
OnUnitInactiveSec=1h"

monitor_file="$systemd_directory/button-monitor.service"
unit_file="$systemd_directory/photo-display.service"
timer_file="$systemd_directory/photo-display.timer"

install_driver() {
    echo "Cloning the repository from $REPO_URL..."
    if git clone "$REPO_URL"; then
        echo "Repository cloned successfully."
    else
        echo "Failed to clone the repository."
        exit 1
    fi

    # Change to the repository directory
    cd "$REPO_DIR" || { echo "Failed to enter directory $REPO_DIR"; exit 1; }

    # Run make to build the kernel module
    echo "Building the kernel module..."
    if make; then
        echo "Build succeeded."
    else
        echo "Build failed."
        exit 1
    fi

    # Find the resulting .ko file
    MODULE=$(find . -name "*.ko" | head -n 1)
    if [ -z "$MODULE" ]; then
        echo "No kernel module file found."
        exit 1
    fi

    # Install the kernel module using insmod
    echo "Installing the kernel module $MODULE..."
    if sudo insmod "$MODULE"; then
        echo "Kernel module installed successfully."
    else
        echo "Failed to install the kernel module."
        exit 1
    fi

    echo "Button driver installed successfully."
}

uninstall_driver(){
    echo "Removing the kernel module $MODULE_NAME..."
    if sudo rmmod "$MODULE_NAME"; then
        echo "Kernel module removed successfully."
    else
        echo "Failed to remove the kernel module."
        exit 1
    fi

    # Change to the parent directory of the repository
    cd ..
    
    # Delete the repository directory
    echo "Deleting the repository directory $REPO_DIR..."
    if rm -drf "$REPO_DIR"; then
        echo "Repository directory deleted successfully."
    else
        echo "Failed to delete the repository directory."
        exit 1
    fi

    echo "Button driver uninstalled successfully."
}

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
    pip3 install tqdm >> /dev/null
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

generate_monitor_service() {
    monitor_content="[Unit]
Description=Monitor Inky Impression Buttons
After=network.target

[Service]
WorkingDirectory=$current_directory
ExecStart=$monitor_script
Restart=always
User=root
Group=root

[Install]
WantedBy=multi-user.target
"

    # Write the unit content to the unit file
    echo "Creating systemd service"
    echo "$monitor_content" | sudo tee "$monitor_file" > /dev/null

    echo "Reloading systemd daemon"
    sudo systemctl daemon-reload

    echo "Starting monitor"
    sudo systemctl enable button-monitor.service
    sudo systemctl start button-monitor.service
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

    sudo systemctl stop button-monitor.service
    sudo systemctl stop photo-display.timer

    sudo systemctl disable button-monitor.service
    sudo systemctl disable photo-display.timer

    sudo rm -f $monitor_file
    sudo rm -f $timer_file
    sudo rm -f $unit_file

    echo "Reloading systemd daemon"
    systemctl daemon-reload
}

if [[ "$1" == "install" ]]; then
    install_application
    install_driver

    if [[ "$2" == "cron" ]]; then
        create_cron_job
        echo "Cron setup complete."
        echo "Make sure to edit your config to have a SleepTime of 0!"
    elif [[ "$2" == "systemd" ]]; then
        generate_systemd_service
        echo "Systemd service created."
        echo "Make sure to edit your config to have a SleepTime of 0!"
    fi

    generate_monitor_service
    echo "Button Monitor service created."

    sleep 3
    echo "Setup complete."

elif [[ "$1" == "uninstall" ]]; then
    remove_cron_job
    uninstall_driver
    uninstall_application
    remove_systemd_service
    echo "Uninstallation complete."
else
    echo "Usage: $0 [install|uninstall]"
    echo "          optionally [install cron] to setup as a cron job"
    echo "          optionally [install systemd] to setup as a systemd service"
    exit 1
fi
