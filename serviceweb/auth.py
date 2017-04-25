from functools import wraps
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask import session, abort, g
from flask.helpers import url_for


class NotRegisteredError(Exception):
    pass


def oidc2dbuser(oidc_user):
    if 'nickname' not in oidc_user:
        raise NotImplementedError()

    login = oidc_user['nickname']
    filters = [{'name': 'github',
                'op': 'eq',
                'val': login}]

    # XXX this call should have an internal cache
    res = g.db.get_entries('user', filters=filters)

    if len(res) == 1:
        db_user = res[0]

    elif len(res) > 1:
        raise ValueError(res)
    else:
        # not creating entries automatically for now
        raise NotRegisteredError(login)

    return db_user


def get_user(app):
    if 'user' in session:
        return session['user']

    if 'userinfo' not in session:
        return None

    try:
        return oidc2dbuser(session['userinfo'])
    except NotRegisteredError:
        return None


def only_for_editors(func):
    @wraps(func)
    def _only_for_editors(*args, **kw):
        user = g.user

        if user is None:
            if g.debug:
                print('Anonymous rejected')
            abort(401)
            return

        if not user['editor']:
            if g.debug:
                print('%r rejected' % user)
            abort(401)
            return

        return func(*args, **kw)
    return _only_for_editors


class OIDConnect(object):
    def __init__(self, app, **config):
        self.domain = config['domain']
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.redirect_uri = config.get('redirect_uri', '/auth0')
        self.login_url = "https://%s/login?client=%s" % (
            self.domain, self.client_id

        )
        self.auth_endpoint = "https://%s/authorize" % self.domain
        self.token_endpoint = "https://%s/oauth/token" % self.domain
        self.userinfo_endpoint = "https://%s/userinfo" % self.domain
        provider = self.provider_info()
        client = self.client_info()
        oidc = OIDCAuthentication(app, provider_configuration_info=provider,
                                  client_registration_info=client)
        app.add_url_rule(self.redirect_uri, 'redirect_oidc',
                         oidc._handle_authentication_response)
        with app.app_context():
            url = url_for('redirect_oidc')
            oidc.client_registration_info['redirect_uris'] = url
            oidc.client.registration_response['redirect_uris'] = url

        app.oidc = oidc

    def client_info(self):
        return {'client_id': self.client_id,
                'client_secret': self.client_secret}

    def provider_info(self):
        return {'issuer': self.domain,
                'authorization_endpoint': self.auth_endpoint,
                'token_endpoint': self.token_endpoint,
                'userinfo_endpoint': self.userinfo_endpoint}
