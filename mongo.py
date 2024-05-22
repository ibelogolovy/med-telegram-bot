import logging
import os

from collections import defaultdict
from telegram.ext import BasePersistence

from dotenv import load_dotenv
from pymongo import MongoClient
from telegram.ext._utils.types import BD, CD, UD, CDCData

load_dotenv()


class MongoPersistence(BasePersistence):
    """
    MongoDB persistence
    """

    async def update_callback_data(self, data: CDCData) -> None:
        pass

    async def drop_chat_data(self, chat_id: int) -> None:
        pass

    async def drop_user_data(self, user_id: int) -> None:
        pass

    async def refresh_user_data(self, user_id: int, user_data: UD) -> None:
        pass

    async def refresh_chat_data(self, chat_id: int, chat_data: CD) -> None:
        pass

    async def refresh_bot_data(self, bot_data: BD) -> None:
        pass

    async def flush(self) -> None:
        pass

    def __init__(self,
                 database):
        super().__init__(
        )

        self.client = MongoClient(database)
        self.db = self.client["chats"]
        logging.info(f"Connected to '{self.db}' on '{database}'")

    async def drop_table(self) -> None:
        self.db["launch_data"].drop()

    async def get_user_data(self) -> dict:
        data = defaultdict(dict)
        for item in self.db["user_data"].find():
            data[item["user_id"]] = item["data"]
        return data

    async def get_chat_data(self) -> dict:
        data = defaultdict(dict)
        for item in self.db["chat_data"].find():
            data[item["chat_id"]] = item["data"]
        return data

    async def get_launch_data(self) -> list:
        data = list()
        for item in self.db["launch_data"].find():
            data.append(item['launch_id'])
        return data

    async def get_bot_data(self) -> dict:
        data = {}
        for item in self.db["bot_data"].find():
            data[item["key"]] = item["value"]
        return data

    async def get_callback_data(self) -> dict:
        data = {}
        for item in self.db["callback_dat"].find():
            data[item["callback_dat"]] = item["data"]
        return data

    async def get_conversations(self, name: str) -> dict:
        data = {}
        for item in self.db[f"conversation.{name}"].find():
            data[tuple(item["conv"])] = item["state"]
        return data

    async def update_conversation(self, name, key, new_state):
        self.db[f"conversation.{name}"].update_one({"conv": key}, {"$set": {"state": new_state}}, upsert=True)

    async def update_user_data(self, user_id, data):
        self.db["user_data"].update_one({"user_id": user_id}, {"$set": {"data": data}}, upsert=True)

    async def update_chat_data(self, chat_id, data):
        self.db["chat_data"].update_one({"chat_id": chat_id}, {"$set": {"data": data}}, upsert=True)

    async def update_bot_data(self, data):
        for key, value in data.items():
            self.db["bot_data"].update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

    async def update_launch_data(self, data: dict):
        for key, value in data.items():
            self.db["launch_data"].update_one({"launch_id": key}, {"$set": {"launch_id": key}}, upsert=True)
            logging.debug(f"'launch_id': {key} added to 'launch_data'")


mongo_persistence = MongoPersistence(
    database=os.environ.get('MONGODB')
)


# from typing import Optional
#
# from telegram.ext import BasePersistence
# from collections import defaultdict
# from copy import deepcopy
#
# from telegram.ext._utils.types import BD, CD, UD, CDCData
# from telegram.utils.helpers import decode_user_chat_data_from_json, decode_conversations_from_json, \
#     encode_conversations_to_json
# import mongoengine
# import json
# import os
# from bson import json_util
#
#
# class Conversations(mongoengine.Document):
#     obj = mongoengine.DictField()
#     meta = {'collection': 'Conversations', 'ordering': ['-id']}
#
#
# class UserData(mongoengine.Document):
#     obj = mongoengine.DictField()
#     meta = {'collection': 'UserData', 'ordering': ['-id']}
#
#
# class ChatData(mongoengine.Document):
#     obj = mongoengine.DictField()
#     meta = {'collection': 'ChatData', 'ordering': ['-id']}
#
#
# class BotData(mongoengine.Document):
#     obj = mongoengine.DictField()
#     meta = {'collection': 'BotData', 'ordering': ['-id']}
#
#
# class DBHelper():
#     """Class to add and get documents from a mongo database using mongoengine
#     """
#
#     def __init__(self, dbname="persistencedb"):
#         mongoengine.connect(host=os.environ.get('MONGODB'), db=dbname)
#
#     def add_item(self, data, collection):
#         if collection == "Conversations":
#             document = Conversations(obj=data)
#         elif collection == "UserData":
#             document = UserData(obj=data)
#         elif collection == "chat_data_collection":
#             document = ChatData(obj=data)
#         else:
#             document = BotData(obj=data)
#         document.save()
#
#     def get_item(self, collection):
#         if collection == "Conversations":
#             document = Conversations.objects()
#         elif collection == "UserData":
#             document = UserData.objects()
#         elif collection == "ChatData":
#             document = ChatData.objects()
#         else:
#             document = BotData.objects()
#         if document.first() == None:
#             document = {}
#         else:
#             document = document.first()['obj']
#
#         return document
#
#     def close(self):
#         mongoengine.disconnect()
#
#
# class DBPersistence(BasePersistence):
#     """Uses DBHelper to make the bot persistant on a database.
#        It's heavily inspired on PicklePersistence from python-telegram-bot
#     """
#
#     async def get_callback_data(self) -> Optional[CDCData]:
#         pass
#
#     async def update_callback_data(self, data: CDCData) -> None:
#         pass
#
#     async def drop_chat_data(self, chat_id: int) -> None:
#         pass
#
#     async def drop_user_data(self, user_id: int) -> None:
#         pass
#
#     async def refresh_user_data(self, user_id: int, user_data: UD) -> None:
#         pass
#
#     async def refresh_chat_data(self, chat_id: int, chat_data: CD) -> None:
#         pass
#
#     async def refresh_bot_data(self, bot_data: BD) -> None:
#         pass
#
#     def __init__(self):
#         super(DBPersistence, self).__init__(store_user_data=True,
#                                             store_chat_data=True,
#                                             store_bot_data=True)
#         self.persistdb = "persistancedb"
#         self.conversation_collection = "Conversations"
#         self.user_data_collection = "UserData"
#         self.chat_data_collection = "ChatData"
#         self.bot_data_collection = "BotData"
#         self.db = DBHelper()
#         self.user_data = None
#         self.chat_data = None
#         self.bot_data = None
#         self.conversations = None
#         self.on_flush = False
#
#     def get_conversations(self, name):
#         if self.conversations:
#             pass
#         else:
#             conversations_json = json_util.dumps(self.db.get_item(self.conversation_collection))
#             self.conversations = decode_conversations_from_json(conversations_json)
#         return self.conversations.get(name, {}).copy()
#
#     def update_conversation(self, name, key, new_state):
#         if self.conversations.setdefault(name, {}).get(key) == new_state:
#             return
#         self.conversations[name][key] = new_state
#         if not self.on_flush:
#             conversations_json = json_util.loads(encode_conversations_to_json(self.conversations))
#             self.db.add_item(conversations_json, self.conversation_collection)
#
#     def get_user_data(self):
#         if self.user_data:
#             pass
#         else:
#             user_data_json = json_util.dumps(self.db.get_item(self.user_data_collection))
#             if user_data_json != '{}':
#                 self.user_data = decode_user_chat_data_from_json(user_data_json)
#             else:
#                 self.user_data = defaultdict(dict, {})
#         return deepcopy(self.user_data)
#
#     def update_user_data(self, user_id, data):
#         if self.user_data is None:
#             self.user_data = defaultdict(dict)
#         # comment next line if you want to save to db every time this function is called
#         if self.user_data.get(user_id) == data:
#             return
#         self.user_data[user_id] = data
#         if not self.on_flush:
#             user_data_json = json_util.loads(json.dumps(self.user_data))
#             self.db.add_item(user_data_json, self.user_data_collection)
#
#     def get_chat_data(self):
#         if self.chat_data:
#             pass
#         else:
#             chat_data_json = json_util.dumps(self.db.get_item(self.chat_data_collection))
#             if chat_data_json != "{}":
#                 self.chat_data = decode_user_chat_data_from_json(chat_data_json)
#             else:
#                 self.chat_data = defaultdict(dict, {})
#         return deepcopy(self.chat_data)
#
#     def update_chat_data(self, chat_id, data):
#         if self.chat_data is None:
#             self.chat_data = defaultdict(dict)
#         # comment next line if you want to save to db every time this function is called
#         if self.chat_data.get(chat_id) == data:
#             return
#         self.chat_data[chat_id] = data
#         if not self.on_flush:
#             chat_data_json = json_util.loads(json.dumps(self.chat_data))
#             self.db.add_item(chat_data_json, self.chat_data_collection)
#
#     def get_bot_data(self):
#         if self.bot_data:
#             pass
#         else:
#             bot_data_json = json_util.dumps(self.db.get_item(self.bot_data_collection))
#             self.bot_data = json.loads(bot_data_json)
#         return deepcopy(self.bot_data)
#
#     def update_bot_data(self, data):
#         if self.bot_data == data:
#             return
#         self.bot_data = data.copy()
#         if not self.on_flush:
#             bot_data_json = json_util.loads(json.dumps(self.bot_data))
#             self.db.add_item(self.bot_data, self.bot_data_collection)
#
#     def flush(self):
#         if self.conversations:
#             conversations_json = json_util.loads(encode_conversations_to_json(self.conversations))
#             self.db.add_item(conversations_json, self.conversation_collection)
#         if self.user_data:
#             user_data_json = json_util.loads(json.dumps(self.user_data))
#             self.db.add_item(user_data_json, self.user_data_collection)
#         if self.chat_data:
#             chat_data_json = json_util.loads(json.dumps(self.chat_data))
#             self.db.add_item(chat_data_json, self.chat_data_collection)
#         if self.bot_data:
#             bot_data_json = json_util.loads(json.dumps(self.bot_data))
#             self.db.add_item(self.bot_data, self.bot_data_collection)
#         self.db.close()
