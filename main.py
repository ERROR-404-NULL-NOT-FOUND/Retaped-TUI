import npyscreen
import requests
from websockets.sync.client import connect
from math import floor
import curses.ascii
import threading

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

serverIDList = []
channelIDList = []
currentChannel = ''
currentServer = ''
token = ''


class server:
    serverName: str
    serverID: str
    owner: str

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


cache = {
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
        tmpServer.categories = i['catagories'] if 'catagories' in i.keys(
        ) else False
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

def renderMessage(message):
    global messageBox
    string: str
    if message['author'] in cache['users'].keys():
        author = cache['users'][message['author']].username
        if message['content']:
            string=f'[{author}]: {message["content"]}'
        else:
            string=f'[{author}]:<No content>'
    else:
        string=f'[{message["author"]}]: {message["content"]}'
        threading.Thread(fetchUsername, args=[message['author']])
    messageBox.values.append(string)

def fetchUsername(userID, index, message):
    global token
    global messageBox
    user = requests.get(f'https://api.revolt.lea.pet/users/{userID}', headers={'x-session-token': token}).json()
    tmpUser = user()
    tmpUser.id = user['_id']
    tmpUser.username = user['username']
    tmpUser.status = user['status'] if 'status' in user.keys() else False
    tmpUser.online = user['online']
    cache['users'].update({user['_id']: tmpUser})
    #messageBox.values[index] = 

def ws():
    global messageBox
    global currentChannel
    global websocket
    global localUser
    while True:
        message = websocket.recv()
        message = json.loads(message)
        match(message['type']):
            case 'Message':
                if message['channel'] == currentChannel:
                    renderMessage(message)
                    messageBox.update()
            case 'Ready':
                buildUserCache(message['users'])
                buildServerCache(message['servers'])
                buildChannelCache(message['channels'])
                for i in message['servers']:
                    serverList.values.append(i['name'])
                tmpUser = requests.get(
                    'https://api.revolt.lea.pet/users/@me', headers={'x-session-token': token}).json()
                localUser = user()
                localUser.id = tmpUser['_id']
                localUser.username = tmpUser['username']
                serverList.name = localUser.username
                serverList.update()


def fetchMessages(id: str):
    r = requests.get(
        f'https://api.revolt.lea.pet/channels/{id}/messages', headers={'x-session-token': token})
    return r.json()


def fetchChannels(server: server):
    global channelList
    global channelIDList
    channelList.values = []
    channelIDList = []
    for i in server.channels:
        if i in cache['channels'].keys():
            channel = cache['channels'][i]
            channelList.values.append(channel.name)
            channelIDList.append(channel.id)
    channelList.update()


class ServerMultiLineAction(npyscreen.MultiLineAction):
    def __init__(self, screen, values=None, value=None, slow_scroll=False, scroll_exit=False, return_exit=False, select_exit=False, exit_left=False, exit_right=False, widgets_inherit_color=False, always_show_cursor=False, allow_filtering=True, **keywords):
        super().__init__(screen, values, value, slow_scroll, scroll_exit, return_exit, select_exit,
                         exit_left, exit_right, widgets_inherit_color, always_show_cursor, allow_filtering, **keywords)

    def actionHighlighted(self, act_on_this, key_press):
        global serverList
        global serverIDList
        global currentServer
        currentServer = serverIDList[serverList.values.index(act_on_this)]
        channelList.name = act_on_this
        fetchChannels(cache['servers'][currentServer])


class ChannelMultiLineAction(npyscreen.MultiLineAction):
    def __init__(self, screen, values=None, value=None, slow_scroll=False, scroll_exit=False, return_exit=False, select_exit=False, exit_left=False, exit_right=False, widgets_inherit_color=False, always_show_cursor=False, allow_filtering=True, **keywords):
        super().__init__(screen, values, value, slow_scroll, scroll_exit, return_exit, select_exit,
                         exit_left, exit_right, widgets_inherit_color, always_show_cursor, allow_filtering, **keywords)

    def actionHighlighted(self, act_on_this, key_press):
        global channelList
        global channelIDList
        global currentChannel
        global messageBox
        global inputBox
        currentChannel = channelIDList[channelList.values.index(act_on_this)]
        messageBox.values = []
        messageBox.name = act_on_this
        messageBox.update()
        messages = fetchMessages(currentChannel)
        for i in reversed(range(len(messages))):
            renderMessage(messages[i])
        messageBox.update()
        inputBox.edit()


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
    _contained_widget = npyscreen.MultiLine


class inputBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    __contained_widget = npyscreen.Textfield


class TestApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())


def sendMessage(totallyanargument):
    global inputBox
    global currentChannel
    global token
    input = inputBox.value
    inputBox.value = ''
    requests.post(f'https://api.revolt.lea.pet/channels/{currentChannel}/messages', headers={
                  'x-session-token': token}, data=json.dumps({'content': input}))


class MainForm(npyscreen.FormBaseNew):
    def create(self):

        global messageBox
        global websocket
        global token
        global channelList
        global serverList
        global inputBox
        token = "bENKddDm_C75Yez6MCM_xrmNu2zDTtSME2pqUsxH9GTG_0ma_t6FgozDX3gxbvM7"
        self.name = 'Retaped TUI'
        self.FIX_MINIMUM_SIZE_WHEN_CREATED = True
        serverList = self.add(serverBox, relx=1, rely=1, width=floor(
            self.max_x/6), height=floor(self.max_y/2)-1)
        channelList = self.add(channelBox, relx=1, width=floor(
            self.max_x/6), height=floor(self.max_y/2))
        messageBox = self.add(messageBox, relx=floor(self.max_x/6)+1, rely=1,
                              height=floor(self.max_y)-6, width=self.max_x-floor(self.max_x/6)-2)
        inputBox = self.add(npyscreen.BoxTitle, contained_widget_arguments={"Editable": True}, relx=floor(
            self.max_x/6)+1, rely=-5, height=4, width=self.max_x-floor(self.max_x/6)-2)
        inputBox.add_handlers({curses.ascii.CR: sendMessage})
        inputBox.value = 'test'
        inputBox.update()

        websocket = connect("wss://ws.revolt.lea.pet")
        websocket.send(json.dumps({"type": "Authenticate", "token": token}))
        self.keypress_timeout = 1
        threading.Thread(target=ws).start()
        self.edit()

    def resize(self):
        global serverList
        global channelList
        global messageBox
        global inputBox
        self.refresh()
        serverList.height, serverList.width = floor(
            self.max_y/2)-1, floor(self.max_x/6)
        channelList.height, channelList.width = floor(
            self.max_y/2), floor(self.max_x/6)

        messageBox.relx, messageBox.height, messageBox.width = floor(
            self.max_x/6)+1, floor(self.max_y)-6, self.max_x-floor(self.max_x/6)-2
        inputBox.relx, inputBox.width = floor(
            self.max_x/6)+1, self.max_x-floor(self.max_x/6)-2
        self.display()


TestApp().run()
# asyncio.run(ws())