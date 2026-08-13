"""Base Scraping Class"""
from __future__ import print_function
from __future__ import absolute_import
from lxml import etree
from bs4 import BeautifulSoup
from . import proxygrabber
from dotenv import dotenv_values

import requests
import random
import json
import builtins as bi

# monkey patch socket to use only IPv4 (guard against double-patching)
import socket
if not getattr(socket, '_skiptracer_patched', False):
    og = socket.getaddrinfo

    def ng(*args, **kwargs):
        res = og(*args, **kwargs)
        return [r for r in res if r[0] == socket.AF_INET]

    socket.getaddrinfo = ng
    socket._skiptracer_patched = True


def _package_path(*parts):
    """Resolve a path inside the installed skiptracer.data package."""
    try:
        try:
            from importlib.resources import files
            return str(files('skiptracer.data').joinpath(*parts))
        except Exception:
            import pkg_resources
            return pkg_resources.resource_filename('skiptracer', 'data/' + '/'.join(parts))
    except Exception:
        import os
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', *parts)


def random_line():
    """Get a random User-Agent string from the local DB file."""
    afile = open(_package_path('user-agents.db'))
    line = next(afile)
    for num, aline in enumerate(afile):
        if random.randrange(num + 2):
            continue
        line = aline
    return line.strip()


class PageGrabber:
    """Base PageGrabber Class. Import request functionality in modules."""

    def __init__(self):
        self.env = dotenv_values()
        self.info_dict = {}
        self.info_list = []
        self.ua = random_line()
        self.proxy = {}
        self.soup = None
        self.source = None

    def get_source(self, url):
        """Return source code from given URL."""
        headers = {"User-Agent": self.ua}
        reqcom = 0
        requests.packages.urllib3.disable_warnings()
        results = ""

        while reqcom < 5:
            try:
                if bi.proxy != '':
                    proxy = str(bi.proxy).split(":")[1].strip()
                    xproto = str(bi.proxy).split(":")[0].strip()
                    self.proxy = {str(xproto): str(proxy).strip()}
                    results = requests.get(
                        url,
                        headers=headers,
                        proxies=self.proxy,
                        timeout=10,
                        verify=False,
                        allow_redirects=True
                    ).text
                else:
                    results = requests.get(
                        url,
                        headers=headers,
                        timeout=10,
                        verify=False,
                        allow_redirects=True
                    ).text
                reqcom = 5
            except Exception as failedreq:
                if bi.webproxy:
                    bi.proxy = proxygrabber.new_proxy()
                    reqcom = reqcom + 1
                else:
                    print(failedreq)
                    reqcom = reqcom + 1
        return results.encode('ascii', 'ignore').decode("utf-8")

    def post_data(self, url, data):
        """Send POST request of given DATA, URL."""
        headers = {"User-Agent": self.ua}
        reqcom = 0
        requests.packages.urllib3.disable_warnings()
        while reqcom < 5:
            try:
                results = requests.post(
                    url,
                    headers=headers,
                    proxies=self.proxy,
                    timeout=10,
                    verify=False,
                    allow_redirects=True,
                    data=data
                ).text
                return results.encode('ascii', 'ignore').decode("utf-8")
            except Exception as failedreq:
                if bi.webproxy:
                    bi.proxy = proxygrabber.new_proxy()
                reqcom = reqcom + 1
        return

    def get_dom(self, source):
        """Return BeautifulSoup DOM (lxml parser)."""
        return BeautifulSoup(source, 'lxml')

    def get_html(self, source):
        """Return BeautifulSoup DOM (html.parser)."""
        return BeautifulSoup(source, 'html.parser')
