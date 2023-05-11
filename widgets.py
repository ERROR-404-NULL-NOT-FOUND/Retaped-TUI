import npyscreen
import curses
from structures import *
import globals
import threading
import requests


def fetchUsername(userID, index):
    if not userID in globals.cache['users'].keys():
        userData = requests.get(f'{globals.apiEndpoint}/users/{userID}', headers={
                                'x-session-token': globals.token}).json()
        tmpUser = user()
        tmpUser.id = userData['_id']
        tmpUser.username = userData['username']
        tmpUser.status = userData['status'] if 'status' in userData.keys() else False
        tmpUser.online = userData['online']
        globals.cache['users'].update({userData['_id']: tmpUser})
    else:
        tmpUser = globals.cache['users'][userID]
    globals.messageBox.values[index].author = tmpUser.username
    globals.messageBox.update()


class ServerMultiLineAction(npyscreen.MultiLineAction):
    def __init__(self, screen, values=None, value=None, slow_scroll=False, scroll_exit=False, return_exit=False, select_exit=False, exit_left=False, exit_right=False, widgets_inherit_color=False, always_show_cursor=False, allow_filtering=True, **keywords):
        super().__init__(screen, values, value, slow_scroll, scroll_exit, return_exit, select_exit,
                         exit_left, exit_right, widgets_inherit_color, always_show_cursor, allow_filtering, **keywords)

    def actionHighlighted(self, act_on_this, key_press):
        globals.currentServer = globals.serverIDList[globals.serverList.values.index(act_on_this)]
        globals.channelList.name = act_on_this
        globals.channelList.fetchChannels(globals.cache['servers'][globals.currentServer])


class ChannelMultiLineAction(npyscreen.MultiLineAction):
    def __init__(self, screen, values=None, value=None, slow_scroll=False, scroll_exit=False, return_exit=False, select_exit=False, exit_left=False, exit_right=False, widgets_inherit_color=False, always_show_cursor=False, allow_filtering=True, **keywords):
        super().__init__(screen, values, value, slow_scroll, scroll_exit, return_exit, select_exit,
                         exit_left, exit_right, widgets_inherit_color, always_show_cursor, allow_filtering, **keywords)

    def actionHighlighted(self, act_on_this, key_press):
        globals.currentChannel = globals.channelIDList[globals.channelList.values.index(act_on_this)]
        globals.messageBox.values = []
        globals.messageBox.name = act_on_this
        globals.messageBox.update()
        messages = globals.messageBox.fetchMessages(globals.currentChannel)
        for i in messages['users']:
            if not i['_id'] in globals.cache['users'].keys():
                tmpUser = user()
                tmpUser.id = i['_id']
                tmpUser.username = i['username']
                tmpUser.status = i['status'] if 'status' in i.keys() else False
                tmpUser.online = i['online']
                globals.cache['users'].update({i['_id']: tmpUser})
        for i in reversed(range(len(messages['messages']))):
            messageData = messages['messages'][i]
            globals.messageBox.renderMessage(messageData)
        globals.messageBox._contained_widget.cursor_line = len(globals.messageBox.values)
        globals.messageBox.update()
        self.editing=False


class serverBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = ServerMultiLineAction


class channelBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = ChannelMultiLineAction

    def fetchChannels(self, server: server):
        globals.channelList.values = []
        globals.channelIDList = []
        for i in server.channels:
            if i in globals.cache['channels'].keys():
                channel = globals.cache['channels'][i]
                globals.channelList.values.append(channel.name)
                globals.channelIDList.append(channel.id)
        globals.channelList.update()


class multiLineMessages(npyscreen.MultiSelectFixed):
    def __init__(self, screen, values=None, value=None, slow_scroll=False, scroll_exit=False, return_exit=False, select_exit=False, exit_left=False, exit_right=False, widgets_inherit_color=False, always_show_cursor=False, allow_filtering=True, **keywords):
        self.allow_filtering = False
        self.check_cursor_move = True
        self._contained_widget = npyscreen.MultiLineEdit
        self._contained_widgets.editable = False
        self._contained_widgets.False_box = ''
        self._contained_widgets.True_box = ''
        super().__init__(screen, values, value, slow_scroll, scroll_exit, return_exit, select_exit,
                         exit_left, exit_right, widgets_inherit_color, always_show_cursor, allow_filtering, **keywords)

    def display_value(self, vl: message):
        output = ''
        mentioned = False
        for i in vl.replies:
            if i in globals.cache['messages']:
                output += f'> {globals.cache["messages"][i].content}\n'
            else:
                output += f'>Unloaded Message'
        if globals.localUser.id in vl.mentions:
            mentioned = True
        output += f'[{vl.author}] '
        output += f'{vl.content}'
        return [output, mentioned]

    def when_cursor_moved(self):
        globals.highlightedIndex = self.cursor_line
        return super().when_cursor_moved()



class messageBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = multiLineMessages
    def renderMessage(self, messageData):
        reply = []
        mentions=[]
        author = ''
        if 'replies' in messageData.keys():
            for i in messageData['replies']:
                reply.append(i)
        if 'mentions' in messageData.keys():
            for i in messageData['mentions']:
                mentions.append(i)
        if 'masquerade' in messageData.keys():
            author = messageData['masquerade']['name']
        else:
            if messageData['author'] in globals.cache['users'].keys():
                author = globals.cache['users'][messageData['author']].username
            else:
                author=messageData['author']
                threading.Thread(target=fetchUsername, args=[messageData['author'], len(globals.messageBox.values)-1]).start()
        renderedMessage = message()
        renderedMessage.id = messageData['_id']
        renderedMessage.author = author
        renderedMessage.content = messageData['content'] if 'content' in messageData.keys(
        ) else None
        renderedMessage.replies = reply
        renderedMessage.mentions = mentions
        globals.cache['messages'].update({renderedMessage.id: renderedMessage})
        self.values.append(renderedMessage)
        self.update()
        if globals.localUser.id in renderedMessage.mentions:
            test = self._my_widgets[0]._my_widgets[4]
            test.highlight=True
            test.do_colors()
            test.update()

    def fetchMessages(self, id: str):
        r = requests.get(
            f'{globals.apiEndpoint}/channels/{id}/messages?include_users=true', headers={'x-session-token': globals.token})
        return r.json()


class inputTextBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = npyscreen.MultiLineEdit
