import requests
from flask import Markup, current_app, request, url_for

SCRIPT = "<script src='https://www.recaptcha.net/recaptcha/api.js?render={}'></script>"
#INPUT = "grecaptcha.ready(function() {{grecaptcha.execute('{}', {{action: '{}'}}).then(function(token) {{$('form').append($('<input>').prop('type', 'hidden').prop('name', 'g-recaptcha-response').val(token));}});}});"
INPUT = '''<script>grecaptcha.ready(function() {{grecaptcha.execute('{}', {{action: '{}'}}).then(function(token) {{$('form').append("<input type='hidden' name='recaptcha' value='"+token+"'/>")}})}})</script>'''


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
    def script(self):
        if self.site_key:
            return Markup(SCRIPT.format(self.site_key))
        else:
            return ''

    @property
    def embed(self):
        if self.site_key:
            try:
                action = url_for(request.endpoint)
            except:
                action = request.endpoint.replace('.', '/').replace('_', '/')
            return Markup(INPUT.format(self.site_key, action))
        else:
            return ''

    @property
    def verify(self):
        if self.site_key and self.secret_key:
            data = {
                'secret': self.secret_key,
                'response': request.form.get('recaptcha'),
                'remoteip': request.remote_addr
            }
            r = requests.get(self.VERIFY_URL, params=data)
            try:
                action = url_for(request.endpoint)
            except:
                action = request.endpoint.replace('.', '/').replace('_', '/')
            return r.json()['score'] if r.json().get('action') == action else False
        return True

    @property
    def failed(self):
        return 'reCAPTCHA validation failed.'
