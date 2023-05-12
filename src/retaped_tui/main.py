import npyscreen
import requests
from websockets.sync.client import connect
from math import floor
import curses.ascii
import threading
import asyncio

import json
import yaml
from yaml import Loader
import os
import time

from . import login
from . import globals

globals.init()
from . import structures, widgets



def buildServerCache(data: dict):
    global serverIDList
    for i in data:
        tmpServer = structures.server()
        tmpServer.serverName = i['name']
        tmpServer.owner = i['owner']
        tmpServer.serverID = i['_id']
        tmpServer.categories = i['catagories'] if 'catagories' in i.keys(
        ) else False
        tmpServer.channels = i['channels']
        globals.cache['servers'].update({i['_id']: tmpServer})
        globals.serverIDList.append(i['_id'])


def buildUserCache(data: dict):
    for i in data:
        tmpUser = structures.user()
        tmpUser.id = i['_id']
        tmpUser.username = i['username']
        tmpUser.status = i['status'] if 'status' in i.keys() else False
        tmpUser.online = i['online']
        globals.cache['users'].update({i['_id']: tmpUser})


def buildChannelCache(data: dict):
    for i in data:
        tmpChannel = structures.channel()
        tmpChannel.id = i['_id']
        tmpChannel.name = i['name'] if 'name' in i.keys() else False
        tmpChannel.desc = i['description'] if 'description' in i.keys() else False
        tmpChannel.server = i['server'] if 'server' in i.keys() else False
        tmpChannel.type = i['channel_type']
        globals.cache['channels'].update({i['_id']: tmpChannel})



def boilerplate():
    try:
        asyncio.run(ws())
    except KeyboardInterrupt:
        exit(0)

def wsInit():
    globals.websocket = connect(globals.wsEndpoint)
    globals.websocket.send(json.dumps({"type": "Authenticate", "token": globals.token}))


async def ws():
    try:
        wsInit()
    except TimeoutError:
        npyscreen.notify('Connection FAILED')
        time.sleep(1)
        exit()
    while True:
        try:
            message = globals.websocket.recv()
        except TimeoutError:
            npyscreen.notify('Reconnecting', title='Disconnected')
            failed=True
            while failed==True:
                try:
                    wsInit()
                except TimeoutError:
                    failed=True
        message = json.loads(message)
        match(message['type']):
            case 'Message':
                if message['channel'] == globals.currentChannel:
                    globals.messageBox.renderMessage(message)
                    globals.messageBox.update(globals.messageBox)
            case 'MessageUpdate':
                if message['channel'] == globals.currentChannel:
                    globals.messageBox.updateMessage(message)
                    globals.messageBox.update(globals.messageBox)
            case 'Ready':
                buildUserCache(message['users'])
                buildServerCache(message['servers'])
                buildChannelCache(message['channels'])
                globals.serverList.values = []
                for i in message['servers']:
                    globals.serverList.values.append(i['name'])
                globals.serverList.name = globals.localUser.username
                globals.serverList.edit()






def sendMessage(totallyanargument):
    input = globals.inputBox.value
    if not globals.editingMessage:
        message = requests.post(f'{globals.apiEndpoint}/channels/{globals.currentChannel}/messages', headers={
            'x-session-token': globals.token}, data=json.dumps({'content': input, 'replies': globals.replies}))
        if message.status_code != 200:
            npyscreen.notify(title='Failed to send')
            return 1
    else:
        message = requests.patch(f'{globals.apiEndpoint}/channels/{globals.currentChannel}/messages/{globals.editingMessageMsg.id}', headers={'x-session-token': globals.token}, data=json.dumps({'content': input}))
        if message.status_code != 200:
                npyscreen.notify(title='Failed to send')
                return 1
    globals.inputBox.value = ''
    clearReplies()

def clearReplies():
    if globals.editingMessage:
        globals.inputBox.value=''
        globals.editingMessage=False
    globals.replies=[]
    globals.inputBox.name = ''
    globals.inputBox.update()

def addReply(totallyanargument):
    if not globals.editingMessage:
        message = globals.messageBox.values[globals.highlightedIndex]
        globals.replies.append({'id': message.id, 'mention': False})
        globals.inputBox.name+="> "+message.content+"\n"
        globals.inputBox.update()

def editMessage(totallyanargument):
    message = globals.messageBox.values[globals.highlightedIndex]
    if message.authorID == globals.localUser.id:
        globals.editingMessageMsg=message
        globals.inputBox.value=message.content
        globals.editingMessage=True
        globals.inputBox.name='Editing message'
        globals.inputBox.edit()
    else:
        npyscreen.notify('Not your message', title='Failed to edit')
        time.sleep(2)

class TestApp(npyscreen.NPSAppManaged):
    def onStart(self):
        npyscreen.setTheme(npyscreen.Themes.ElegantTheme)
        globals.app=self
        try:
            if "XDG_CONFIG_DIR" in os.environ:
                globals.configPath = os.environ['XDG_CONFIG_HOME']
            else:
                globals.configPath = f'{os.environ["HOME"]}/.config'
            if os.path.exists(f'{globals.configPath}/Retaped.yaml'):
                self.registerForm("MAIN", MainForm())
            else:
                self.registerForm("LOGIN", login.LoginForm())
                self.setNextForm("MAIN", MainForm())
        except KeyboardInterrupt:
            exit(0)

class MainForm(npyscreen.FormBaseNew):
    def create(self):
        config = open(f'{globals.configPath}/Retaped.yaml', 'r')
        config = yaml.load(config, Loader=Loader)
        globals.token=config['token']
        globals.apiEndpoint=config['api-endpoint']
        globals.wsEndpoint=config['ws-endpoint']
        globals.form=self
        self.name = 'Retaped TUI'
        self.FIX_MINIMUM_SIZE_WHEN_CREATED = True
        globals.serverList = self.add(widgets.serverBox, relx=1, rely=1, width=floor(
            self.max_x/6), height=floor(self.max_y/2)-1)
        globals.channelList = self.add(widgets.channelBox, relx=1, width=floor(
            self.max_x/6), height=floor(self.max_y/2))
        globals.messageBox = self.add(widgets.messageBox, relx=floor(self.max_x/6)+1, rely=1,
                              height=floor(self.max_y)-6, width=self.max_x-floor(self.max_x/6)-2)
        globals.inputBox = self.add(widgets.inputTextBox,relx=floor(
            self.max_x/6)+1, name='', rely=-5, height=4, width=self.max_x-floor(self.max_x/6)-2)
        globals.inputBox.add_handlers({"!s": sendMessage, curses.ascii.ESC: clearReplies})
        globals.messageBox.add_handlers({"r": addReply})
        globals.messageBox.add_handlers({"e": editMessage})

        try:
            tmpUser = requests.get(
                    f'{globals.apiEndpoint}/users/@me', headers={'x-session-token': globals.token})
            if tmpUser.status_code == 401:
                os.remove(f'{globals.configPath}/Retaped.yaml')
                self.notify('Invalid token')
                time.sleep(1)
                exit(1)
        except KeyboardInterrupt:
            exit(0)
        except:
            npyscreen.notify('Failed to request user profile', title='Failed to connect')
            time.sleep(1)
            exit(1)
        tmpUser=tmpUser.json()
        globals.localUser = structures.user()
        globals.localUser.id = tmpUser['_id']
        globals.localUser.username = tmpUser['username']
        
        threading.Thread(target=boilerplate).start()
        script_dir = os.path.dirname(__file__)
        for i in open(f'{script_dir}/aboutRT-tui.txt', 'r'):
            tmpFakeMessage = structures.message()
            tmpFakeMessage.content = i
            tmpFakeMessage.replies = []
            tmpFakeMessage.author = ''
            tmpFakeMessage.mentions = []
            globals.messageBox.values.append(tmpFakeMessage)
        try:
            self.edit()
        except npyscreen.NotEnoughSpaceForWidget:
            failed = True
            while failed:
                try:
                    self.edit()
                    failed=False
                except npyscreen.NotEnoughSpaceForWidget:
                    pass
                except KeyboardInterrupt:
                    exit(0)

    def resize(self):
        self.refresh()
        globals.serverList.height, globals.serverList.width = floor(
            self.max_y/2)-1, floor(self.max_x/6)
        globals.channelList.height, globals.channelList.width = floor(
            self.max_y/2), floor(self.max_x/6)

        globals.messageBox.relx, globals.messageBox.height, globals.messageBox.width = floor(
            self.max_x/6)+1, floor(self.max_y)-6, self.max_x-floor(self.max_x/6)-2
        globals.inputBox.relx, globals.inputBox.width = floor(
            self.max_x/6)+1, self.max_x-floor(self.max_x/6)-2
        self.display()

try:
    TestApp().run()
except KeyboardInterrupt:
    exit(0)
except Exception as e:
    print(e)
    exit()
# asyncio.run(ws())
