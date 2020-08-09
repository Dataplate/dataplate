import ldap

from dataaccess.app import app, db
from dataaccess.models import *


class AuthenticationError(Exception):
    def __init__(self):
        super().__init__('Invalid username or password. Please try again.')


class InternalLDAPError(Exception):
    def __init__(self):
        super().__init__(
            'Internal LDAP connectivity issue occurred. Please try again later.'
        )


def ldap_login(username, email, password):
    l = ldap.initialize('ldap://127.0.0.1:389')
    try:
        l.protocol_version = ldap.VERSION3
        if (username is not None and len(username)>0 and len(username)<50):
            userauth = f'uid={username},ou=People,dc=my-domain,dc=com'
            l.simple_bind_s(userauth, password) #uid=amit,ou=People,dc=my-domain,dc=com
        else:
            raise AuthenticationError()
    except ldap.INVALID_CREDENTIALS:
        raise AuthenticationError()
    except ldap.LDAPError as e:
        app.logger.error(str(e))
        raise InternalLDAPError()

    # basedn = 'OU=Employees,OU=User Accounts,DC=ad,DC=my-domain,DC=com'
    # searchFilter = '(|(ou=People)(ou=Group))'
    basedn = userauth #'OU=Peple,DC=my-domain,DC=com' #userauth #'CN=Manager,DC=my-domain,DC=com'
    #searchScope = 'OU=Peple,DC=my-domain,DC=com'
    #searchFilter = f'(|(uid=*{username}*)(displayName=*{username}*)(cn=*{username}*)(sn=*{username}*)(mail=*{username}*))'
    searchFilter = '(uid=*amit*)'
    searchAttribute = ['sAMAccountName', 'displayName', 'mail'] #['mail'] #['sAMAccountName', 'displayName', 'mail']
    searchScope = ldap.SCOPE_SUBTREE
    try:
        ldap_result = l.search_s(basedn, searchScope, searchFilter, searchAttribute)
        for record in dict(ldap_result).values():
            if record['mail'][0].decode('utf-8') == email:
                user = User.query.filter_by(username=email).one_or_none()
                if not user:
                    fullname = record['displayName'][0].decode(
                        'utf-8').replace(',', '')
                    user = User(username, fullname)
                    db.session.add(user)
                    db.session.commit()
                return user
        raise AuthenticationError()
    except ldap.LDAPError as e:
        app.logger.error(str(e))
        raise InternalLDAPError()
    finally:
        l.unbind_s()
