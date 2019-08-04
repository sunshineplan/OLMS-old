import requests
from flask import Markup, current_app, request, url_for

SCRIPT = "<script src='https://www.recaptcha.net/recaptcha/api.js?render={}'></script>"
READY = "grecaptcha.ready(function() {{grecaptcha.execute('{}', {{action: '{}'}}).then(function(token) {{$('form').append($('<input>').prop('type', 'hidden').prop('name', 'g-recaptcha-response').val(token));}});}});"


class reCAPTCHA:
    def __init__(self, app=current_app):
        self.site_key = app.config.get('RECAPTCHA_SITE_KEY') or ''
        self.secret_key = app.config.get('RECAPTCHA_SECRET_KEY')
        self.VERIFY_URL = 'https://www.recaptcha.net/recaptcha/api/siteverify'
        if self.site_key:
            self.is_enabled = True
        else:
            self.is_enabled = False

    @property
    def key(self):
        return self.site_key

    @property
    def verify(self):
        if self.site_key and self.secret_key:
            data = {
                'secret': self.secret_key,
                'response': request.form.get('g-recaptcha-response'),
                'remoteip': request.remote_addr
            }
            r = requests.get(self.VERIFY_URL, params=data)
            print(r.text)
            return r.json()['success'] if r.status_code == 200 else False
        return True

    @property
    def script(self):
        if self.site_key:
            return Markup(SCRIPT.format(self.site_key))
        else:
            return ''

    @property
    def ready(self):
        if self.site_key:
            return Markup(READY.format(self.site_key, url_for(request.endpoint)))
        else:
            return ''
