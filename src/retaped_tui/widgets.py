from . import npyscreen
from . import globals, structures
import threading
import requests


def fetchUsername(userID, index):
    userData = requests.get(f'{globals.apiEndpoint}/users/{userID}', headers={
                            'x-session-token': globals.token}).json()
    tmpUser = structures.user()
    tmpUser.id = userData['_id']
    tmpUser.username = userData['username']
    tmpUser.status = userData['status'] if 'status' in userData.keys() else False
    tmpUser.online = userData['online']
    globals.cache['users'].update({userData['_id']: tmpUser})

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
        if not messages: return
        for i in messages['users']:
            if not i['_id'] in globals.cache['users'].keys():
                tmpUser = structures.user()
                tmpUser.id = i['_id']
                tmpUser.username = i['username']
                tmpUser.status = i['status'] if 'status' in i.keys() else False
                tmpUser.online = i['online']
                globals.cache['users'].update({i['_id']: tmpUser})
        for i in reversed(range(len(messages['messages']))):
            messageData = messages['messages'][i]
            globals.messageBox.renderMessage(messageData)
        globals.messageBox.update()
        self.editing=False
        #globals.messageBox.reset_cursor()


class serverBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = ServerMultiLineAction


class channelBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = ChannelMultiLineAction

    def fetchChannels(self, server: structures.server):
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
        self._contained_widgets=npyscreen.TitleFixedText
        self._contained_widgets.allow_override_begin_entry_at=False 
        self._contained_widgets.use_two_lines=False
        self._contained_widgets.height = 1
        self._contained_widget_height=1
        super().__init__(screen, values, value, slow_scroll, scroll_exit, return_exit, select_exit,
                         exit_left, exit_right, widgets_inherit_color, always_show_cursor, allow_filtering, **keywords)

    def display_value(self, vl: structures.message):
        output = ''
        mentioned = False

        if globals.localUser.id in vl.mentions:
            mentioned = True
        #if vl.author:
        #    output += f'[{vl.author}] '
        output += f'{vl.content}'
        return [output, mentioned, vl.author]

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
                if i in globals.cache['messages']:
                    replyContent=f'> {globals.cache["messages"][i].content}'
                else:
                    replyContent=f'>Unloaded Message'
                reply=structures.message()
                reply.content=replyContent
                reply.author=''
                reply.id=''
                reply.mentions=[]
                self.values.append(reply)
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
        renderedMessage = structures.message()
        renderedMessage.id = messageData['_id']
        renderedMessage.author = author
        renderedMessage.authorID = messageData['author']
        renderedMessage.content = messageData['content'] if 'content' in messageData.keys(
        ) else None
        renderedMessage.replies = reply
        renderedMessage.mentions = mentions
        globals.cache['messages'].update({renderedMessage.id: renderedMessage})
        self.values.append(renderedMessage)

        
    def updateMessage(self, message):
        for i in self.values:
            if i.id == message['id']:
                i.content = message['data']['content']
                break

    def fetchMessages(self, id: str):
        try:
            r = requests.get(
            f'{globals.apiEndpoint}/channels/{id}/messages?include_users=true', headers={'x-session-token': globals.token})
        except Exception:
            npyscreen.notify('Failed to request messages',title='Error')
            return False
        return r.json()
#    def resize(self):
#        self.relx, self.height, self.width = globals.form.max_x//6+1, globals.form.max_y-6, globals.form.max_x-globals.form.max_x//6-2
#        self.entry_widget.relx, self.entry_widget.height, self.entry_widget.width = globals.form.max_x//6+2, globals.form.max_y-6, globals.form.max_x-globals.form.max_x//6-2
#        self.entry_widget.request_height, self.entry_widget.request_width=True, True
#        self.update(clear=True)


class inputTextBox(npyscreen.BoxTitle):
    def __init__(self, screen, contained_widget_arguments=None, *args, **keywords):
        super().__init__(screen, contained_widget_arguments, *args, **keywords)
    _contained_widget = npyscreen.MultiLineEdit
    def resize(self):
        self.relx, self.width = globals.form.max_x//6+1, globals.form.max_x-globals.form.max_x//6-4
        self.entry_widget.relx = globals.form.max_x//6+2
        self.update(clear=True)
