# Telegram bot for Radarr and Sonarr

## Requirements
* A telegram bot configured in a group chat
* A Radarr or Sonarr server


## Installation
Download the code
```shell
git clone https://github.com/sildur/arrbot.git arrbot
```
Move the files to `/opt/`
```shell
mv arrbot /opt/
```

Copy the configuration example:
```shell
cp /opt/arrbot/arrbot.ini.example /opt/arrbot/arrbot.ini
```
## Configuration
Edit the configuration file:
```shell
nano /opt/arrbot/arrbot.ini
```

Set the correct ownership and permissions:
```shell
sudo chown root:root -R /opt/arrbot
```    
Configure systemd so arrbot starts at boot.
```shell
cat << EOF | sudo tee /etc/systemd/system/arrbot.service > /dev/null
[Unit]
Description=Arrbot Daemon
After=syslog.target network.target

[Service]
DynamicUser=yes
WorkingDirectory=/opt/arrbot/
Type=simple
ExecStart=/opt/arrbot/arrbot.py
TimeoutStopSec=20
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

Enable the service.
```shell
sudo systemctl enable arrbot.service
```
Start the service.
```shell
sudo systemctl start arrbot.service
```
