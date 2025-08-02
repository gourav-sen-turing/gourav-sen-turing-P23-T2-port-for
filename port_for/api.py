# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, with_statement
import contextlib
import socket
import errno
import random
from itertools import chain
from port_for import ephemeral, utils
from ._ranges import UNASSIGNED_RANGES
from .exceptions import PortForException


SYSTEM_PORT_RANGE = (0, 1024)


def select_random(ports=None, exclude_ports=None):
    """
    Returns random unused port number.
    """
    if ports is None:
        ports = available_good_ports()

    if exclude_ports is None:
        exclude_ports = set()

    ports = set(ports)
    ports.difference_update(set(exclude_ports))

    # Find an available port
    available = [port for port in ports if not port_is_used(port)]

    if available:
        return random.choice(available)

    raise PortForException("Can't select a port")


def is_available(port):
    """
    Returns if port is good to choose.
    """
    return port in available_ports() and not port_is_used(port)


def available_ports(low=1024, high=65535, exclude_ranges=None):
    """
    Returns a set of possible ports (excluding system,
    ephemeral and well-known ports).
    Pass ``high`` and/or ``low`` to limit the port range.
    """
    if exclude_ranges is None:
        exclude_ranges = []
    available = utils.ranges_to_set(UNASSIGNED_RANGES)
    exclude = utils.ranges_to_set(
        ephemeral.port_ranges()
        + exclude_ranges
        + [SYSTEM_PORT_RANGE, (SYSTEM_PORT_RANGE[1], low), (high, 65536)]
    )
    return available.difference(exclude)


def good_port_ranges(ports=None, min_range_len=20, border=3):
    """
    Returns a list of 'good' port ranges.
    Such ranges are large and don't contain ephemeral or well-known ports.
    Ranges borders are also excluded.
    """
    if ports is None:
        ports = available_ports()
    ranges = utils.to_ranges(list(ports))

    # Filter ranges that are long enough AFTER applying borders
    good_ranges = []
    for start, end in ranges:
        # Length after trimming borders
        trimmed_length = (end - border) - (start + border) + 1
        # Must be GREATER than min_range_len, not equal
        if trimmed_length > min_range_len:
            good_ranges.append((start + border, end - border))

    # Sort by length (descending), then by start port
    good_ranges.sort(key=lambda r: (-(r[1] - r[0]), r[0]))

    return good_ranges


def available_good_ports(min_range_len=20, border=3):
    """
    Returns a set of available good ports.
    """
    ranges = good_port_ranges(min_range_len=min_range_len, border=border)
    return utils.ranges_to_set(ranges)


def port_is_used(port, host="127.0.0.1"):
    """
    Returns if port is used. Port is considered used if the current process
    can't bind to it or the port doesn't refuse connections.
    """
    unused = _can_bind(port, host) and _refuses_connection(port, host)
    return not unused


def _can_bind(port, host):
    sock = socket.socket()
    with contextlib.closing(sock):
        try:
            sock.bind((host, port))
        except socket.error:
            return False
    return True


def _refuses_connection(port, host):
    sock = socket.socket()
    with contextlib.closing(sock):
        sock.settimeout(1)
        err = sock.connect_ex((host, port))
        return err == errno.ECONNREFUSED


def filter_by_type(lst, type_of):
    """Returns a list of elements with given type."""
    return [e for e in lst if isinstance(e, type_of)]


def get_port(ports):
    """
    Returns a random available port. If there's only one port passed
    (e.g. 5000 or '5000') function does not check if port is available.
    If there's -1 passed as an argument, function returns None.

    :param str|int|tuple|set|list ports:
        exact port (e.g. '8000', 8000)
        randomly selected port (None) - any random available port
        [(2000,3000)] or (2000,3000) - random available port from a given range
        [{4002,4003}] or {4002,4003} - random of 4002 or 4003 ports
        [(2000,3000), {4002,4003}] -random of given range and set
    :returns: a random free port
    :raises: ValueError
    """
    # Special case: -1 returns None
    if ports == -1:
        return None

    # Special case: None returns a random available port
    if ports is None:
        return select_random(None)

    # Special case: exact port number (int or string)
    if isinstance(ports, (int, str)):
        try:
            port_num = int(ports)
            return port_num
        except (ValueError, TypeError):
            pass

    # Handle tuple (port range)
    if isinstance(ports, tuple) and len(ports) == 2:
        start, end = ports
        port_range = set(range(start, end + 1))
        return select_random(port_range)

    # Handle set (specific ports)
    if isinstance(ports, set):
        return select_random(ports)

    # Handle list (mixed formats)
    if isinstance(ports, list):
        # Collect all possible ports
        all_ports = set()

        for item in ports:
            if isinstance(item, tuple) and len(item) == 2:
                # Port range
                start, end = item
                all_ports.update(range(start, end + 1))
            elif isinstance(item, set):
                # Set of ports
                all_ports.update(item)
            elif isinstance(item, (int, str)):
                # Single port
                try:
                    all_ports.add(int(item))
                except (ValueError, TypeError):
                    pass

        if all_ports:
            return select_random(all_ports)

    # Fallback: try to return a random port
    return select_random(None)
