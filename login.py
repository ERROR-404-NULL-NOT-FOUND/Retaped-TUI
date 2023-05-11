import npyscreen
import requests
import json
import yaml

import globals
class LoginForm(npyscreen.ActionForm):
    def create(self):
        self.name = 'Login'
        self.email=self.add(npyscreen.TitleText, name='Email')
        self.password=self.add(npyscreen.TitlePassword, name='Password')
        self.add(npyscreen.FixedText, value='Advanced options')
        self.apiEnd=self.add(npyscreen.TitleText, name='API endpoint')
        self.wsEnd=self.add(npyscreen.FixedText, name='WS endpoint')
        self.edit()
    def on_ok(self):
        if self.apiEnd.value and self.wsEnd.value:
            globals.apiEndpoint=self.apiEnd.value
            globals.wsEndpoint=self.wsEnd.value
        if self.email.value and self.password.value:
            response = requests.post(f'{globals.apiEndpoint}/auth/session/login', data=json.dumps({'email': self.email.value, 'password': self.password.value}))
            if response.status_code != 200:
                exit(1)
            globals.token = response.json()['token']
            config = open(f'{globals.configPath}/Retaped.yaml', 'w')
            config.write(yaml.safe_dump({'token': globals.token}))
        return super().on_ok()