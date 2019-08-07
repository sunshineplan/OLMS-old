import requests
from flask import Markup, current_app, request, url_for

SCRIPT = "<script src='https://www.recaptcha.net/recaptcha/api.js?render={}'></script>"
READY = '<script>grecaptcha.ready(function() {{{}}})</script>'
EXECUTE = "grecaptcha.execute('{}', {{action: '{}'}}).then(function(token) {{$('.recaptcha').val(token)}})"
INTERVAL = 'setInterval(function(){{{}}}, 100000)'
INPUT = "<input type='hidden' class='recaptcha' name='recaptcha'>"


class reCAPTCHA:
    def __init__(self, app=current_app):
        self.site_key = app.config.get('RECAPTCHA_SITE_KEY') or ''
        self.secret_key = app.config.get('RECAPTCHA_SECRET_KEY')
        self.VERIFY_URL = 'https://www.recaptcha.net/recaptcha/api/siteverify'

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
            return Markup(READY.format(EXECUTE.format(self.site_key, action)))
        else:
            return ''

    @property
    def interval(self):
        if self.site_key:
            try:
                action = url_for(request.endpoint)
            except:
                action = request.endpoint.replace('.', '/').replace('_', '/')
            return Markup(READY.format(INTERVAL.format(EXECUTE.format(self.site_key, action))))
        else:
            return ''

    @property
    def input(self):
        if self.site_key:
            return Markup(INPUT)
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
            r = requests.get(self.VERIFY_URL, params=data).json()
            try:
                action = url_for(request.endpoint)
            except:
                action = request.endpoint.replace('.', '/').replace('_', '/')
            return r['score'] if r.get('action') == action or r.get('action') == action.replace('delete', 'update') else False
        return True

    @property
    def level(self):
        return 0.5

    @property
    def failed(self):
        return 'reCAPTCHA validation failed.'
