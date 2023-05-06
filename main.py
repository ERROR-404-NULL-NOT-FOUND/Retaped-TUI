import npyscreen
import requests
from websockets.sync.client import connect
from math import floor

import json

global websocket

global inputBox
global messageBox
global channelList
global serverList

global currentServer
global currentChannel

global channelIDList
global serverIDList

global token
global localUser

serverIDList=[]
channelIDList=[]
currentChannel = ''
currentServer = ''
token=''
class server:
    serverName: str
    serverID: str
    owner:str
    
    categories: dict
    channels: list
    members: dict

class user:
    id: str
    username: str
    status: str
    profile: str
    online: bool

class channel:
    id: str
    name: str
    desc: str
    type: str
    server: str

cache={
    "servers": {},
    "users": {},
    "channels": {},
}

def buildServerCache(data: dict):
    global serverIDList
    for i in data:
        tmpServer = server()
        tmpServer.serverName = i['name']
        tmpServer.owner = i['owner']
        server.serverID = i['_id']
        tmpServer.categories = i['catagories'] if 'catagories' in i.keys() else False
        tmpServer.channels = i['channels']
        cache['servers'].update({i['_id']: tmpServer})
        serverIDList.append(i['_id'])

def buildUserCache(data: dict):
    for i in data:
        tmpUser = user()
        tmpUser.id = i['_id']
        tmpUser.username = i['username']
        tmpUser.status = i['status'] if 'status' in i.keys() else False
        tmpUser.online = i['online']
        cache['users'].update({i['_id']: tmpUser})

def buildChannelCache(data: dict):
    global channelIDList
    channelIDList = []
    for i in data:
        tmpChannel = channel()
        tmpChannel.id = i['_id']
        tmpChannel.name = i['name'] if 'name' in i.keys() else False
        tmpChannel.desc = i['description'] if 'description' in i.keys() else False
        tmpChannel.server = i['server'] if 'server' in i.keys() else False
        tmpChannel.type = i['channel_type']
        cache['channels'].update({i['_id']: tmpChannel})


def ws():
    global messageBox
    global currentChannel
    global websocket
    global localUser
    message = websocket.recv()
    message = json.loads(message)
    match(message['type']):
        case 'Message':
            if message['channel'] != currentChannel: return
            messageBox.values.insert(0, npyscreen.FixedText(value=f'[{cache["users"][message["author"]].username if message["author"] in cache["users"].keys() else message["author"]}]: {message["content"] if "content" in message.keys() else ""}'))
        case 'Ready':
            buildUserCache(message['users'])
            buildServerCache(message['servers'])
            buildChannelCache(message['channels'])
            for i in message['servers']:
                serverList.values.append(i['name'])
            tmpUser = requests.get('https://api.revolt.lea.pet/users/@me', headers={'x-session-token': token}).json()
            localUser = user()
            localUser.id = tmpUser['_id']
            localUser.username = tmpUser['username']
            serverList.name = localUser.username
            serverList.update()
            #for i in message['servers']:
            #   messageBox.values.append(i['name'])
def fetchMessages(id: str):
    r = requests.get(f'https://api.revolt.lea.pet/channels/{id}/messages', headers={'x-session-token': 'mlacYQRjkaMqw4Hssau9ISlprYbUfYf_6psD77fG-DeLKcQvJHUulMGsnDDbcpxE'})
    return r.json()

def fetchChannels(server: server):
    global channelList
    global channelIDList
    channelList.values=[]
    channelIDList=[]
    for i in server.channels:
        if i in cache['channels'].keys():
            channel = cache['channels'][i]
            channelList.values.append(channel.name)
            channelIDList.append(channel.id)
    channelList.update()
        
class ServerMultiLineAction(npyscreen.MultiSelectAction):
    def __init__(self, screen, values=None, value=None, slow_scroll=False, scroll_exit=False, return_exit=False, select_exit=False, exit_left=False, exit_right=False, widgets_inherit_color=False, always_show_cursor=False, allow_filtering=True, **keywords):
        super().__init__(screen, values, value, slow_scroll, scroll_exit, return_exit, select_exit, exit_left, exit_right, widgets_inherit_color, always_show_cursor, allow_filtering, **keywords)
    def actionHighlighted(self, act_on_this, key_press):
        global serverList
        global serverIDList
        global currentServer
        currentServer = serverIDList[serverList.values.index(act_on_this)]
        channelList.name=act_on_this
        fetchChannels(cache['servers'][currentServer])

class ChannelMultiLineAction(npyscreen.MultiSelectAction):
    def __init__(self, screen, values=None, value=None, slow_scroll=False, scroll_exit=False, return_exit=False, select_exit=False, exit_left=False, exit_right=False, widgets_inherit_color=False, always_show_cursor=False, allow_filtering=True, **keywords):
        super().__init__(screen, values, value, slow_scroll, scroll_exit, return_exit, select_exit, exit_left, exit_right, widgets_inherit_color, always_show_cursor, allow_filtering, **keywords)
    def actionHighlighted(self, act_on_this, key_press):
        global channelList
        global channelIDList
        global currentChannel
        global messageBox
        currentChannel = channelIDList[channelList.values.index(act_on_this)]
        messageBox.values = []
        messageBox.name = act_on_this
        messageBox.update()
        messages = fetchMessages(currentChannel)
        for i in range(len(messages)):
            messageBox.values.insert(0, npyscreen.FixedText(value=f'[{cache["users"][messages[i]["author"]].username if messages[i]["author"] in cache["users"].keys() else messages[i]["author"]}]: {messages[i]["content"] if "content" in messages[i].keys() else ""}'))
        messageBox.update()

class serverBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = ServerMultiLineAction
class channelBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = ChannelMultiLineAction
class messageBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = npyscreen.Pager
class inputBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    __contained_widget = npyscreen.Textfield
class TestApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())


class MainForm(npyscreen.FormBaseNew):
    def create(self):

        global messageBox
        global websocket
        global token
        global channelList
        global serverList
        global inputBox
        token = ""
        self.name = 'Retaped TUI'
        self.FIX_MINIMUM_SIZE_WHEN_CREATED=True
        serverList = self.add(serverBox, relx=1, rely=1, width=floor(self.max_x/6), height=floor(self.max_y/2)-1)
        channelList = self.add(channelBox, relx=1, width=floor(self.max_x/6), height=floor(self.max_y/2))
        messageBox = self.add(messageBox, relx=floor(self.max_x/6)+1,rely=1, height=floor(self.max_y)-6, width=self.max_x-floor(self.max_x/6)-2)
        inputBox = self.add(inputBox, relx=floor(self.max_x/6)+1, rely=-5, height=4,width=self.max_x-floor(self.max_x/6)-2)
        
        websocket = connect("wss://ws.revolt.lea.pet")
        websocket.send(json.dumps({"type": "Authenticate", "token": token}))
        messageBox.values.append('test')
        self.keypress_timeout = 1
        self.edit()
    def while_waiting(self, *args):
        ws()
    def resize(self):
        global serverList
        global channelList
        global messageBox
        global inputBox
        serverList.height, serverList.width = floor(self.max_y/2)-1, floor(self.max_x/6)
        channelList.height, channelList.width = floor(self.max_y/2), floor(self.max_x/6)
        
        messageBox.relx, messageBox.height = floor(self.max_x/6)+1, floor(self.max_y)-6
        inputBox.relx = floor(self.max_x/6)+1
        
TestApp().run()
#asyncio.run(ws())
