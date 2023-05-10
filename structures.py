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


class message:
    id: str
    author: str
    content: str
    replies: list
