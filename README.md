Telegram Bot Hooked Into Raddarr and Sonarr
===========================================



Installation:
-------------

    git clone ssh://git@git.nave.ws:7999/tel/full_bot.git

Usage:
-----

First you will need to change the dlconfig.example to hold your configuration. Bot keys
sonarr/radarr keys/url etc. Once that is done you can run the bot and send it commands. 
The two commands available are /tv and /movie inside of telegram. This will log to tgbot\*log. 
This is desgined to be easy to use for the end user and not a tool for an administrator to 
control their sonarr/radarr. If you want you can modify it to hold more administravtive commands
such as profile and limits on downloads delete of items etc.  
