#!/usr/bin/env python
import configparser
import json
import logging
import sys
from pyarr import RadarrAPI, SonarrAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler


def reply_message(text, context, query):
    context.bot.edit_message_text(
        text=text,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )


class ArrBot:
    def __init__(self, config_file):
        self.log = logging
        self.log.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        sections = self.config.sections()
        if 'common' not in sections:
            self.log.error("no common section found in config")
            sys.exit(1)

        if self.config.get('common', 'bot_token') is None:
            self.log.error("no bot_token found in config")
            sys.exit(1)
        self.bot_token = self.config['common']['bot_token']
        self.allowed_chats = self.config['common']['allowed_chats'].split(',')
        self.sonarr_api = self.initialize_arr('sonarr', SonarrAPI)
        self.radarr_api = self.initialize_arr('radarr', RadarrAPI)
        self.updater = Updater(token=self.bot_token)
        self.set_up_handlers()

    def start(self):
        self.updater.start_polling()
        self.updater.idle()

    def set_up_handlers(self):
        self.updater.dispatcher.add_handler(CommandHandler('movie', self.search_movies, pass_args=True))
        self.updater.dispatcher.add_handler(CommandHandler('tv', self.search_tv_shows, pass_args=True))
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.download_item))

    def library_contains_item(self, item_id, item_type):
        if item_type == 'movie':
            existing_items = self.sonarr_api['api_class'].get_movie(item_id, tmdb=True)
            if len(existing_items) == 0:
                return False
            return True
        elif item_type == 'tv':
            items = self.sonarr_api['api_class'].get_series()
            for entry in items:
                if entry['tvdbId'] == int(item_id):
                    return True
            return False
        else:
            self.log.error(f"unknown type {item_type}")
            return False

    def download_item(self, update: Update, context: CallbackContext):
        query = update.callback_query
        data = json.loads(query.data)
        item_id = data['item_id']
        item_type = data['item_type']
        if item_type == 'movie':
            if self.library_contains_item(item_id, item_type):
                reply_message("Movie already in library", context, query)
                self.log.info(f"movie {item_id} already in library")
                return

            self.radarr_api['api_class'].add_movie(
                item_id,
                root_dir=self.radarr_api['root_dir'],
                quality_profile_id=1
            )
            reply_message("Downloading...", context, query)
        elif item_type == 'tv':
            if self.library_contains_item(item_id, item_type):
                reply_message("TV show already in library", context, query)
                self.log.info(f"tv show {item_id} already in library")
                return
            self.sonarr_api['api_class'].add_series(
                item_id,
                root_dir=self.sonarr_api['root_dir'],
                quality_profile_id=1
            )
            reply_message("Downloading...", context, query)
        else:
            self.log.error(f"unknown type {item_type}")
            return

    def search_movies(self, update: Update, context: CallbackContext):
        arguments = context.args
        terms = ' '.join(arguments)
        if str(update.message.chat_id) not in self.allowed_chats:
            update.message.reply_text("You are not allowed to use this bot")
            self.log.info(f"{update.message.chat_id} not in allowed_chats")
            return

        results = self.radarr_api['api_class'].lookup_movie(terms)
        if len(results) == 0:
            update.message.reply_text("No results found")
            self.log.info(f"no results found for {terms}")
            return
        keyboard = []
        for result in results:
            entry_id = result.get('tmdbId')
            if entry_id is None:
                continue
            button = InlineKeyboardButton(
                result['title'],
                callback_data=json.dumps({'item_id': entry_id, 'item_type': 'movie'})
            )
            keyboard.append([button])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Please select a movie", reply_markup=reply_markup)

    def search_tv_shows(self, update: Update, context: CallbackContext):
        arguments = context.args
        terms = ' '.join(arguments)
        if str(update.message.chat_id) not in self.allowed_chats:
            update.message.reply_text("You are not allowed to use this bot")
            self.log.info(f"{update.message.chat_id} not in allowed_chats")
            return

        results = self.sonarr_api['api_class'].lookup_series(terms)
        if len(results) == 0:
            update.message.reply_text("No results found")
            self.log.info(f"no results found for {terms}")
            return
        keyboard = []
        for result in results:
            entry_id = result.get('tvdbId')
            if entry_id is None:
                continue
            button = InlineKeyboardButton(
                result['title'],
                callback_data=json.dumps({'item_id': entry_id, 'item_type': 'tv'})
            )
            keyboard.append([button])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Please select a tv show", reply_markup=reply_markup)

    def initialize_arr(self, section_name, class_name):
        if section_name not in self.config.sections():
            return None
        section = self.config[section_name]
        api_key = section.get('api_key')
        if api_key is None:
            self.log.error(f"no {section_name} api_key found in config")
            sys.exit(1)

        url = section.get('url')
        if url is None:
            self.log.error(f"no {section_name} url found in config")
            sys.exit(1)

        root_dir = section.get('root_dir')
        if root_dir is None:
            self.log.error(f"no {section_name} root_dir found in config")
            sys.exit(1)

        api_class = class_name(url, api_key)

        basic_username = section.get('basic_username')
        basic_password = section.get('basic_password')
        if basic_username and basic_password:
            api_class.basic_auth(basic_username, basic_password)

        return {"api_class": api_class, "root_dir": root_dir}


if __name__ == '__main__':
    bot = ArrBot('arrbot.ini')
    bot.start()
