import requests
from flask import Markup, current_app, request, url_for

BRANDING = '''<small class='form-text text-muted'>This site is protected by reCAPTCHA and the Google\n
<a href='https://policies.google.com/privacy'>Privacy Policy</a> and\n
<a href='https://policies.google.com/terms'>Terms of Service</a> apply.</small>'''
SCRIPT = "<script src='https://www.recaptcha.net/recaptcha/api.js?render={}'></script>"
READY = '<script>grecaptcha.ready(function() {{{}}})</script>'
EXECUTE = "grecaptcha.execute('{}', {{action: '{}'}}).then(function(token) {{$('.recaptcha').val(token)}})"
INTERVAL = 'setInterval(function(){{{}}}, 100000)'
INPUT = "<input type='hidden' class='recaptcha' name='recaptcha'>"


class reCAPTCHA:
    def __init__(self, app=current_app):
        self.site_key = app.config.get('RECAPTCHA_SITE_KEY') or ''
        self.secret_key = app.config.get('RECAPTCHA_SECRET_KEY')
        self.level = app.config.get('RECAPTCHA_LEVEL') or 0.3
        self.failed = 'reCAPTCHA validation failed.'
        self.VERIFY_URL = 'https://www.recaptcha.net/recaptcha/api/siteverify'

    @property
    def branding(self):
        if self.site_key:
            return Markup(BRANDING)
        else:
            return ''

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
