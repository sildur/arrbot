#Telegram Bot Hooked Into Raddarr and Sonarr

##Goals:
The goal of this bot is to let users download movies or TV shows with out admins
having to go and add them to sonarr. This is useful in medium to large enviornments
or you just don't have time to go and get something for every little request a user has. 

## Requirements:

* Telegram bot already in a group chat
* Radarr Install
* Sonarr Install
* Python3 modules: telegram, requests, json, functools, configparser, logging

**tested on linux only. It should work on ALL OS's**

##Installation
###Installation Prerequisites
The below instructions are based on the following prerequisites. Change the instructions as needed to suit your specific needs if necessary.
* The user tgrsbot is created
* You created the directory /var/lib/tgrsbot and ensured the user tgrsbot has read/write permissions for it
```shell
git clone https://github.com/sildur/TGRSBot.git
mv TGRSBot /opt
cd /opt/TGRSBot
sudo python3 -m pip install -r requirements.txt
```
###Install
Download the code
```shell
git clone https://github.com/sildur/TGRSBot.git tgrsbot
```
Move the files to ```/opt/```
```shell
mv tgrsbot /opt/
```
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
##Usage:
First you will need to change the dlconfig.example to hold your configuration. Bot keys
sonarr/radarr keys/url etc. Once that is done you need to populate allowed_chat. This will be the 
group_id that you had the bot join, you can get this by sending a message to the group chat the bot 
is in, then going to the following url https://api.telegram.org/botAPITOKENHERE/getUpdates
You will get some json that has the chat_id in it. Put this into the dlconfig as well. Then rename 
dlconfig.example to dlconfig.cfg. Then you can start using the bot. Just run
the program with:

```shell
nohup python3 bot.py 
```

It will then log to tgbot\_api.log.  
The two commands available are /tv and /movie inside of telegram. This will log to tgbot\*log. 
This is desgined to be easy to use for the end user and not a tool for an administrator to 
control their sonarr/radarr. If you want you can modify it to hold more administravtive commands
such as profile and limits on downloads delete of items etc.  
