#!/home/jnave/tgbot/bin/python
import os, configparser, logging
from telegram import *
from sonarr import *
from telegram.ext import *

class tgBot():
    def __init__(self):
        self.log = logging
        self.log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename='tgbot_api.log', filemode='w',
                level=logging.INFO)
        self.config = configparser.ConfigParser()
        self.tgbot_token = ""
        self.tv = sonarrApi()
        self.tv.load_config('dlconfig.cfg')

    def load_config(self, configfile):
        """
        the config here should be in
        windows ini format at min it
        needs common and tgbot sections
        """
        try:
            self.config.read(configfile)
            self.tgbot_token = self.config['COMMON']['bot_token']
        except:
            self.log.error("Error reading config file {}".format(configfile))
            sys.exit(1)

    def initBot(self):
        self.updater = Updater(token=self.tgbot_token)
        self.dispatcher = self.updater.dispatcher

    def searchTV(self, bot, update, args):
        self.keyboard = []
        self.search_param = ""
        self.showlist = {}
        for x in args:
            self.search_param += x + " "
        self.showlist = self.tv.search_series(self.search_param)
        for show in self.showlist:
            self.keyboard.append([InlineKeyboardButton(show, callback_data=self.showlist[show])])
        reply_markup = InlineKeyboardMarkup(self.keyboard)
        update.message.reply_text('Found:', reply_markup=reply_markup)

    def button(self, bot, update):
        query = update.callback_query
        self.tvdbId = str(query.data)
        if self.tv.in_library(self.tvdbId):
            bot.edit_message_text(text="Sorry in library already", chat_id=query.message.chat_id, message_id=query.message.message_id)
        else:
            print("running add_series on {}".format(self.tvdbId))
            if self.tv.add_series(self.tvdbId):
                bot.edit_message_text(text="Added, should be available in about an hour", chat_id=query.message.chat_id, message_id=query.message.message_id)
        """
            bot.edit_message_text(text="Selected option: {}".format(query.data),
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
        """

    def startBot(self):
        self.updater.start_polling()

    def addHandlers(self):
        self.searchTV_handler = CommandHandler('searchTV', self.searchTV, pass_args = True)
        self.dispatcher.add_handler(self.searchTV_handler)
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.button))

if __name__ == "__main__":
    bot = tgBot()
    bot.load_config('dlconfig.cfg')
    bot.initBot()
    bot.addHandlers()
    bot.startBot()
