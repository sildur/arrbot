#!/usr/bin/env python
import configparser
import logging
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler

from radarr import RadarrApi
from sonarr import SonarrApi


def bot_respond(telegram_bot, txt, query):
    """
    responds to a download query
    split for readability
    """
    telegram_bot.edit_message_text(
        text=txt, chat_id=query.message.chat_id, message_id=query.message.message_id
    )


def build_keyboard(rlist):
    """
    this builds a keyboard telegram object
    from a list passed to args
    """
    keyboard = []
    for r in rlist:
        keyboard.append([InlineKeyboardButton(r, callback_data=rlist[r])])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


class TgBot:
    def __init__(self, config_file):
        self.log = logging
        self.log.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='tgbot_api.log',
            filemode='w',
            level=logging.INFO
        )
        self.config = configparser.ConfigParser()
        self.tgbot_token = ""
        self.tv = SonarrApi()
        self.movie = RadarrApi()
        self.movie.load_config(config_file)
        self.tv.load_config(config_file)
        self.type_search = 'movie'
        self.allowed_chat = []
        self.load_config(config_file)
        self.updater = Updater(token=self.tgbot_token)
        self.dispatcher = self.updater.dispatcher
        self.add_handlers()

    def load_config(self, configfile):
        """
        the config here should be in
        windows ini format at min it
        needs common and tgbot sections
        """
        try:
            self.config.read(configfile)
            self.tgbot_token = self.config['common']['bot_token']
            group = int(self.config['common']['allowed_chat'])
            self.allowed_chat.append(group)
        except KeyError:
            self.log.error("Error reading config file {}".format(configfile))
            sys.exit(1)

    def searcher(self, terms):
        """
        blanket searcher takes self.type_search
        and searches either radarr or sonarr
        """
        search_param = ""
        for x in terms:
            search_param += x + " "
        if self.type_search == 'movie':
            result_list = self.movie.search_movie(search_param)
        else:
            result_list = self.tv.search_series(search_param)
        return build_keyboard(result_list)

    def search_tv(self, update: Update, context: CallbackContext):
        """
        this will search a sonarr server defined in sonarr.py
        it returns an inline keyboard to the user with the results
        """
        self.type_search = 'TV'
        reply_markup = self.searcher(context.args)

        update.message.reply_text('Found:', reply_markup=reply_markup)

    def download_button(self, update: Update, context: CallbackContext):
        """
        this will be called once a user press's
        an inline keyboard button, it will call 
        in_library and add_series from sonarr.py
        or radarr.py, and then it will inform the
        user of the status
        """
        query = update.callback_query
        item_id = str(query.data)
        if self.type_search == 'movie':
            if self.movie.in_library(item_id):
                bot_respond(context.bot, "sorry in library already", query)
            else:
                if self.movie.add_movie(item_id):
                    bot_respond(context.bot, "added, please wait a few hours", query)
        else:
            if self.tv.in_library(item_id):
                bot_respond(context.bot, "sorry in library already", query)
            else:
                if self.tv.add_series(item_id):
                    bot_respond(context.bot, "added, please wait a few hours", query)

    def search_movies(self, update: Update, context: CallbackContext):
        """
        this will search a radarr server defined in radarr.py
        it returns an inline keyboard to the user with the results
        """
        self.type_search = 'movie'
        reply_markup = self.searcher(context.args)
        update.message.reply_text('Found:', reply_markup=reply_markup)

    def start_bot(self):
        self.updater.start_polling()

    def add_handlers(self):
        search_tv_handler = CommandHandler('tv', self.search_tv, pass_args=True)
        search_movie_handler = CommandHandler('movie', self.search_movies, pass_args=True)
        self.dispatcher.add_handler(search_tv_handler)
        self.dispatcher.add_handler(search_movie_handler)
        self.dispatcher.add_handler(CallbackQueryHandler(self.download_button))


if __name__ == "__main__":
    bot = TgBot(config_file='dlconfig.cfg')
    bot.start_bot()
