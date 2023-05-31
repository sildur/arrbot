#!/usr/bin/env python3

import configparser
import json
import logging
import sys
from time import sleep

from pyarr import RadarrAPI, SonarrAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
)


def reply_message(text, context, query):
    context.bot.edit_message_text(
        text=text,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )


class ArrBot:
    def __init__(self, config_file):
        self.available_connectors = [
            {"name": "radarr", "api_class": RadarrAPI},
            {"name": "sonarr", "api_class": SonarrAPI},
        ]
        self.log = logging
        self.log.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO,
        )
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        sections = self.config.sections()
        if "common" not in sections:
            self.log.error("no common section found in config")
            sys.exit(1)

        if self.config.get("common", "bot_token") is None:
            self.log.error("no bot_token found in config")
            sys.exit(1)
        self.bot_token = self.config["common"]["bot_token"]
        self.allowed_chats = self.config["common"]["allowed_chats"].split(",")
        self.connectors = {}
        for available_connector in self.available_connectors:
            connector = self.initialize_arr(
                available_connector["name"], available_connector["api_class"]
            )
            if connector is not None:
                self.connectors[available_connector["name"]] = connector
        self.updater = Updater(token=self.bot_token)
        self.set_up_handlers()

    def start(self):
        self.updater.start_polling()
        self.updater.idle()

    def set_up_handlers(self):
        self.updater.dispatcher.add_handler(
            CommandHandler(
                ["movie", "tv"], self.search_items_handler, pass_args=True
            )
        )
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(self.process_download_request)
        )

    def library_contains_item(self, item_id, connector_name: str):
        connector = self.connectors[connector_name]
        items = connector["action_list"]()
        for entry in items:
            if entry[connector["id_field"]] == int(item_id):
                return True
        return False

    def download_item(self, item_id, connector_name, context, query):
        connector = self.connectors[connector_name]
        create_params = {
            "root_dir": connector["root_dir"], "quality_profile_id": 1
        }
        create_params.update(connector["create_params"])
        item_data = connector["action_create"](
            item_id, **create_params
        )
        if connector["tags"]:
            available_tags = connector["api_class"].get_tag()
            tag_ids = []
            for tag in connector["tags"]:
                for available_tag in available_tags:
                    if tag == available_tag["label"]:
                        tag_ids.append(available_tag["id"])
                        break
            item_data["tags"] = tag_ids
            sleep(2)
            connector["action_update"](item_data)
        reply_message("Downloading...", context, query)

    def process_download_request(
        self, update: Update, context: CallbackContext
    ):
        query = update.callback_query
        data = json.loads(query.data)
        item_id = data["item_id"]
        connector_name = data["connector_name"]
        if self.library_contains_item(item_id, connector_name):
            reply_message("Item already in library", context, query)
            self.log.info(f"item {item_id} already in library")
            return
        self.download_item(item_id, connector_name, context, query)

    def search_items_handler(self, update: Update, context: CallbackContext):
        command = update.message.text.split(" ")[0]
        command = command[1:]
        for available_connector in self.available_connectors:
            connector_name = available_connector["name"]
            connector = self.connectors[connector_name]
            if command == connector["command"]:
                self.search_items(update, context, connector_name)
                return

    def search_items(
        self, update: Update, context: CallbackContext, connector_name: str
    ):
        connector = self.connectors[connector_name]
        arguments = context.args
        if arguments is not None:
            terms = " ".join(arguments)
        else:
            terms = ""
        if str(update.message.chat_id) not in self.allowed_chats:
            update.message.reply_text("You are not allowed to use this bot")
            self.log.info(f"{update.message.chat_id} not in allowed_chats")
            return

        results = connector["action_search"](terms)
        results = results[:15]
        if len(results) == 0:
            update.message.reply_text("No results found")
            self.log.info(f"no results found for {terms}")
            return
        keyboard = []
        for result in results:
            entry_id = result.get(connector["id_field"])
            if entry_id is None:
                continue
            button = InlineKeyboardButton(
                f"{result['title']} ({result['year']})",
                callback_data=json.dumps(
                    {"item_id": entry_id, "connector_name": connector_name}
                ),
            )
            keyboard.append([button])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "Please select an option", reply_markup=reply_markup
        )

    def initialize_arr(self, section_name, class_name):
        if section_name not in self.config.sections():
            return None
        section = self.config[section_name]
        api_key = section.get("api_key")
        if api_key is None:
            self.log.error(f"no {section_name} api_key found in config")
            sys.exit(1)

        url = section.get("url")
        if url is None:
            self.log.error(f"no {section_name} url found in config")
            sys.exit(1)

        root_dir = section.get("root_dir")
        if root_dir is None:
            self.log.error(f"no {section_name} root_dir found in config")
            sys.exit(1)

        api_class = class_name(url, api_key)
        tags = section.get("tags")
        if tags is not None:
            tags = tags.split(",")
        else:
            tags = []
        basic_username = section.get("basic_username")
        basic_password = section.get("basic_password")
        if basic_username and basic_password:
            api_class.basic_auth(basic_username, basic_password)

        if section_name == "radarr":
            command = "movie"
            id_field = "tmdbId"
            action_list = api_class.get_movie
            action_create = api_class.add_movie
            action_update = api_class.upd_movie
            action_search = api_class.lookup_movie
            create_params = {"search_for_movie": True}
        elif section_name == "sonarr":
            command = "tv"
            id_field = "tvdbId"
            action_list = api_class.get_series
            action_create = api_class.add_series
            action_update = api_class.upd_series
            action_search = api_class.lookup_series
            create_params = {"search_for_missing_episodes": True}
        else:
            self.log.error(f"unknown section {section_name}")
            sys.exit(1)

        return {
            "api_class": api_class,
            "tags": tags,
            "root_dir": root_dir,
            "action_list": action_list,
            "action_create": action_create,
            "action_update": action_update,
            "action_search": action_search,
            "command": command,
            "id_field": id_field,
            "create_params": create_params,
        }


if __name__ == "__main__":
    bot = ArrBot("arrbot.ini")
    bot.start()
