# -*- coding: utf-8 -*-
from __future__ import absolute_import, with_statement
import os
try:
    from ConfigParser import ConfigParser, DEFAULTSECT
except ImportError:  # python3
    from configparser import ConfigParser, DEFAULTSECT
from .api import select_random
from .exceptions import PortForException

DEFAULT_CONFIG_PATH = "/etc/port-for.conf"

class PortStore(object):
    def __init__(self, config_filename=DEFAULT_CONFIG_PATH):
        self._config = config_filename

    def bind_port(self, app, port=None):
        if "=" in app or ":" in app:
            raise Exception('invalid app name: "%s"' % app)

        if port is not None:
            port = str(port)

        parser = self._get_parser()

        # Check if app already has a port
        if parser.has_option(DEFAULTSECT, app):
            existing_port = parser.get(DEFAULTSECT, app)
            if port is not None and port != existing_port:
                # Trying to change port for existing app
                raise PortForException("Cannot change port for app '%s' from %s to %s" %
                                     (app, existing_port, port))
            return int(existing_port)

        # Get all currently bound ports
        app_by_port = dict((v, k) for k, v in parser.items(DEFAULTSECT))
        bound_port_numbers = list(map(int, app_by_port.keys()))

        if port is None:
            # Auto-select a port
            port = str(select_random(exclude_ports=bound_port_numbers))
        else:
            # Check if requested port is already used by another app
            if port in app_by_port:
                raise PortForException("Port %s is already used by app '%s'" % (port,
                                     app_by_port[port]))

        # Bind the port
        parser.set(DEFAULTSECT, app, port)
        self._save(parser)
        return int(port)

    def unbind_port(self, app):
        parser = self._get_parser()
        parser.remove_option(DEFAULTSECT, app)
        self._save(parser)

    def bound_ports(self):
        parser = self._get_parser()
        items = parser.items(DEFAULTSECT)
        # Return as list of tuples (app, port) with port as integer
        return [(app, int(port)) for app, port in items]

    def _ensure_config_exists(self):
        if not os.path.exists(self._config):
            with open(self._config, "w"):
                pass

    def _get_parser(self):
        self._ensure_config_exists()
        parser = ConfigParser()
        parser.read(self._config)
        return parser

    def _save(self, parser):
        with open(self._config, "w") as f:
            parser.write(f)
