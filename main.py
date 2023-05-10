import npyscreen
import requests
from websockets.sync.client import connect
from math import floor
import curses.ascii
import threading
import asyncio

import json

import globals
globals.init()
from structures import *
from widgets import *



def buildServerCache(data: dict):
    global serverIDList
    for i in data:
        tmpServer = server()
        tmpServer.serverName = i['name']
        tmpServer.owner = i['owner']
        server.serverID = i['_id']
        tmpServer.categories = i['catagories'] if 'catagories' in i.keys(
        ) else False
        tmpServer.channels = i['channels']
        globals.cache['servers'].update({i['_id']: tmpServer})
        globals.serverIDList.append(i['_id'])


def buildUserCache(data: dict):
    for i in data:
        tmpUser = user()
        tmpUser.id = i['_id']
        tmpUser.username = i['username']
        tmpUser.status = i['status'] if 'status' in i.keys() else False
        tmpUser.online = i['online']
        globals.cache['users'].update({i['_id']: tmpUser})


def buildChannelCache(data: dict):
    for i in data:
        tmpChannel = channel()
        tmpChannel.id = i['_id']
        tmpChannel.name = i['name'] if 'name' in i.keys() else False
        tmpChannel.desc = i['description'] if 'description' in i.keys() else False
        tmpChannel.server = i['server'] if 'server' in i.keys() else False
        tmpChannel.type = i['channel_type']
        globals.cache['channels'].update({i['_id']: tmpChannel})



def boilerplate():
    asyncio.run(ws())

async def ws():
    while True:
        message = globals.websocket.recv()
        message = json.loads(message)
        match(message['type']):
            case 'Message':
                if message['channel'] == globals.currentChannel:
                    globals.messageBox.renderMessage(message)
                    messageBox.update()
            case 'Ready':
                buildUserCache(message['users'])
                buildServerCache(message['servers'])
                buildChannelCache(message['channels'])
                for i in message['servers']:
                    globals.serverList.values.append(i['name'])
                tmpUser = requests.get(
                    'https://api.revolt.lea.pet/users/@me', headers={'x-session-token': globals.token}).json()
                globals.localUser = user()
                globals.localUser.id = tmpUser['_id']
                globals.localUser.username = tmpUser['username']
                globals.serverList.name = globals.localUser.username
                globals.serverList.update()






def sendMessage(totallyanargument):
    input = globals.inputBox.value
    message = requests.post(f'https://api.revolt.lea.pet/channels/{globals.currentChannel}/messages', headers={
        'x-session-token': globals.token}, data=json.dumps({'content': input, 'replies': globals.replies}))
    if message.status_code != 200:
        print(message.status_code)
        return 0
    globals.inputBox.value = ''

def clearReplies():
    globals.replies=[]

def addReply(totallyanargument):
    message = globals.messageBox.values[globals.highlightedIndex]
    globals.replies.append({'id': message.id, 'mention': False})


class TestApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())

class MainForm(npyscreen.FormBaseNew):
    def create(self):
        globals.token = ""
        self.name = 'Retaped TUI'
        self.FIX_MINIMUM_SIZE_WHEN_CREATED = True
        globals.serverList = self.add(serverBox, relx=1, rely=1, width=floor(
            self.max_x/6), height=floor(self.max_y/2)-1)
        globals.channelList = self.add(channelBox, relx=1, width=floor(
            self.max_x/6), height=floor(self.max_y/2))
        globals.messageBox = self.add(messageBox, relx=floor(self.max_x/6)+1, rely=1,
                              height=floor(self.max_y)-6, width=self.max_x-floor(self.max_x/6)-2)
        globals.inputBox = self.add(inputTextBox, relx=floor(
            self.max_x/6)+1, rely=-5, height=4, width=self.max_x-floor(self.max_x/6)-2)
        globals.inputBox.add_handlers({"!a": sendMessage, curses.ascii.ESC: clearReplies})

        globals.messageBox.add_handlers({"r": addReply})

        globals.websocket = connect("wss://ws.revolt.lea.pet")
        globals.websocket.send(json.dumps({"type": "Authenticate", "token": globals.token}))
        threading.Thread(target=boilerplate).start()
        self.edit()

    def resize(self):
        self.refresh()
        globals.serverList.height, globals.serverList.width = floor(
            self.max_y/2)-1, floor(self.max_x/6)
        globals.channelList.height, globals.channelList.width = floor(
            self.max_y/2), floor(self.max_x/6)

        messageBox.relx, messageBox.height, messageBox.width = floor(
            self.max_x/6)+1, floor(self.max_y)-6, self.max_x-floor(self.max_x/6)-2
        globals.inputBox.relx, globals.inputBox.width = floor(
            self.max_x/6)+1, self.max_x-floor(self.max_x/6)-2
        self.display()


TestApp().run()
# asyncio.run(ws())
