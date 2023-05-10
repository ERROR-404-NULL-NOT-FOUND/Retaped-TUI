def init():
    global websocket
    global apiEndpoint
    global wsEndpoint

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
    global replies
    global highlightedIndex

    global cache


    cache = {
        "servers": {},
        "users": {},
        "channels": {},
        "messages": {},
    }
    wsEndpoint = 'wss://ws.revolt.lea.pet'
    apiEndpoint = 'https://api.revolt.lea.pet'


    serverIDList = []
    channelIDList = []
    replies = []
    currentChannel = ''
    currentServer = ''
    token = ''