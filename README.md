# Telegram bot for Radarr and Sonarr

## Requirements
* A telegram bot configured in a group chat
* A Radarr or Sonarr server
* A system user named `tgrsbot`


## Installation
Download the code
```shell
git clone https://github.com/sildur/TGRSBot.git tgrsbot
```
Move the files to `/opt/`
```shell
mv tgrsbot /opt/
```

Copy the configuration example:
```shell
cp /opt/tgrsbot/arrbot.ini.example /opt/tgrsbot/arrbot.ini
```

Populate `/opt/tgrsbot/arrbot.ini` with your settings

```shell
Ensure ownership of the binary directory.
```shell
sudo chown tgrsbot:nogroup -R /opt/tgrsbot
```    
Configure systemd so tgrsbot can autostart at boot.
```shell
cat << EOF | sudo tee /etc/systemd/system/tgrsbot.service > /dev/null
[Unit]
Description=TGRSBot Daemon
After=syslog.target network.target

[Service]
WorkingDirectory=/opt/tgrsbot/
User=tgrsbot
Group=nogroup
Type=simple

ExecStart=/opt/tgrsbot/bot.py
TimeoutStopSec=20
KillMode=process
Restart=on-failure
[Install]
WantedBy=multi-user.target
EOF
```

Enable the service.
```shell
sudo systemctl enable tgrsbot.service
```
Start the service.
```shell
sudo systemctl start tgrsbot.service
```
