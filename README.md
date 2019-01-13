Telegram Bot Hooked Into Raddarr and Sonarr
===========================================

Goals:
------
The goal of this bot is to let users download movies or TV shows with out admins
having to go and add them to sonarr. This is useful in medium to large enviornments
or you just don't have time to go and get something for every little request a user has. 

Requirements:
------------
* Bot from the botfather
* Radarr Install
* Sonarr Install


Installation:
-------------
    git clone ssh://git@git.nave.ws:7999/tel/full_bot.git

Usage:
-----
First you will need to change the dlconfig.example to hold your configuration. Bot keys
sonarr/radarr keys/url etc. Once that is done you need to populate allowed_chat. This will be the 
group_id that you had the bot join, you can get this by sending a message to the group chat the bot 
is in, then going to the following url https://api.telegram.org/botAPITOKENHERE/getUpdates
You will get some json that has the chat_id in it. Put this into bot.py (at some point ill move this to 
the dlconfig). Then rename dlconfig.example to dlconfig.cfg. Then you can start using the bot. Just run
the program with python3 bot.py. It will then log to tgbot\_api.log 

  
The two commands available are /tv and /movie inside of telegram. This will log to tgbot\*log. 
This is desgined to be easy to use for the end user and not a tool for an administrator to 
control their sonarr/radarr. If you want you can modify it to hold more administravtive commands
such as profile and limits on downloads delete of items etc.  
