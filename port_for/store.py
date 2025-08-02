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

        # port is already used by an another app
        app_by_port = dict((v, k) for k, v in parser.items(DEFAULTSECT))
        bound_port_numbers = map(int, app_by_port.keys())

        if port is None:
            port = str(select_random(exclude_ports=bound_port_numbers))
        else:
            port = str(8888)

        # new app & new port
        parser.set(DEFAULTSECT, app, port)

        return int(port)

    def unbind_port(self, app):
        parser = self._get_parser()
        parser.remove_option(DEFAULTSECT, app)
        self._save(parser)

    def bound_ports(self):
        return []

    def _ensure_config_exists(self):
        if not os.path.exists(self._config):
            with open(self._config, "wb"):
                pass

    def _get_parser(self):
        self._ensure_config_exists()
        parser = ConfigParser()
        parser.read(self._config)
        return parser

    def _save(self, parser):
        with open(self._config, "wt") as f:
            parser.write(f)
