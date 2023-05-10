import npyscreen
import requests
import json

import globals

class LoginForm(npyscreen.ActionFormMinimal):
    def create(self):
        self.name('Login')
        self.email=self.add(npyscreen.TitleText, name='Email')
        self.password=self.add(npyscreen.TitlePassword, name='Password')
    def on_ok(self):
        if self.email.value and self.password.value:
            response = requests.post(f'{globals.apiEndpoint}/auth/account/login', data=json.dumps({'email': self.email.value, 'password': self.password.value})).json()
            globals.token = response

        return super().on_ok()