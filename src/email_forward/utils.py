import asynchat
import logging
import smtpd
import ssl
from functools import wraps

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger('email-forward')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt='%(message)s'))
logger.addHandler(handler)

sentry_logging = LoggingIntegration(
    level=logging.INFO,          # Capture info and above as breadcrumbs
    event_level=logging.WARNING  # Send errors as events
)
sentry_sdk.init(integrations=[sentry_logging])


def with_sentry(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        with sentry_sdk.configure_scope() as scope:
            scope.set_extra('conn', getattr(self, 'conn', None))
            scope.set_extra('addr', getattr(self, 'addr', None))
            scope.set_extra('function', f.__name__)
            scope.set_extra('args', args)
            scope.set_extra('kwargs', kwargs)
            try:
                return f(self, *args, **kwargs)
            except Exception as e:
                logger.exception('error on %s: %s', f.__name__, e)
                raise
    return wrapper


class TLSChannel(smtpd.SMTPChannel):
    @with_sentry
    def smtp_RCPT(self, arg):
        """
        unchanged from super method, except where noted
        """
        if not self.seen_greeting:
            self.push('503 Error: send HELO first')
            return
        logger.debug('===> RCPT %s', arg)
        if not self.mailfrom:
            self.push('503 Error: need MAIL command')
            return
        syntaxerr = '501 Syntax: RCPT TO: <address>'
        if self.extended_smtp:
            syntaxerr += ' [SP <mail-parameters>]'
        if arg is None:
            self.push(syntaxerr)
            return
        arg = self._strip_command_keyword('TO:', arg)
        address, params = self._getaddr(arg)

        # changed {
        if not self.smtp_server.allow_address(address):
            self.push(f'454 "{address}" forwarding not permitted')
            logger.warning('forwarding not permitted for "%s"', address)
            return
        # }

        if not address:
            self.push(syntaxerr)
            return
        if not self.extended_smtp and params:
            self.push(syntaxerr)
            return
        self.rcpt_options = params.upper().split()
        params = self._getparams(self.rcpt_options)
        if params is None:
            self.push(syntaxerr)
            return
        # XXX currently there are no options we recognize.
        if len(params.keys()) > 0:
            self.push('555 RCPT TO parameters not recognized or not implemented')
            return
        self.rcpttos.append(address)
        logger.debug('recips: %s', self.rcpttos)
        self.push('250 OK')

    @with_sentry
    def smtp_EHLO(self, arg):
        """
        unchanged from super method, except where noted
        """
        if not arg:
            self.push('501 Syntax: EHLO hostname')
            return
        # See issue #21783 for a discussion of this behavior.
        if self.seen_greeting:
            self.push('503 Duplicate HELO/EHLO')
            return
        self._set_rset_state()
        self.seen_greeting = arg
        self.extended_smtp = True
        self.push('250-%s' % self.fqdn)

        # changed {
        if not isinstance(self.conn, ssl.SSLSocket):
            logger.info('EHLO from %s %s:%s', self.seen_greeting, *self.addr)
            self.push('250-STARTTLS')
        # }

        if self.data_size_limit:
            self.push('250-SIZE %s' % self.data_size_limit)
            self.command_size_limits['MAIL'] += 26
        if not self._decode_data:
            self.push('250-8BITMIME')
        if self.enable_SMTPUTF8:
            self.push('250-SMTPUTF8')
            self.command_size_limits['MAIL'] += 10
        self.push('250 HELP')

    @with_sentry
    def smtp_HELO(self, arg):
        super().smtp_HELO(arg)
        if self.seen_greeting and not isinstance(self.conn, ssl.SSLSocket):
            logger.info('HELO from %s %s:%s', self.seen_greeting, *self.addr)

    @with_sentry
    def smtp_STARTTLS(self, arg):
        if arg:
            self.push('501 Syntax error (no parameters allowed)')
        elif not isinstance(self.conn, ssl.SSLSocket):
            self.push('220 Ready to start TLS')
            self.conn.settimeout(30)
            self.conn = self.smtp_server.ssl_ctx.wrap_socket(self.conn, server_side=True)
            self.conn.settimeout(None)
            asynchat.async_chat.__init__(self, self.conn, self._map)
            # reset the channel after upgrading to tls
            self.received_lines = []
            self.smtp_state = self.COMMAND
            self.seen_greeting = 0
            self.mailfrom = None
            self.rcpttos = []
            self.received_data = ''
            logger.debug('peer %r negotiated TLS: %r', self.addr, self.conn.cipher())
        else:
            self.push('454 TLS not available due to temporary reason')

    def recv(self, buffer_size):
        # so recv with an ssl connection raises the same errors as without
        try:
            return super().recv(buffer_size)
        except ssl.SSLWantReadError:
            raise BlockingIOError()
