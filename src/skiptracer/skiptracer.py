# -*- coding: utf-8 -*-
#!/usr/bin/env python
from __future__ import print_function

from importlib.metadata import entry_points

import sys
import signal
import json
import ast

try:
    import __builtin__ as bi
except BaseException:
    import builtins as bi


class SkipTracer:
    """Kick off the SkipTracer program."""

    bi.lookup = ''
    bi.webproxy = ""
    bi.proxy = ""
    bi.debug = False

    inc_plugins = {}
    plugins_plugin = "skiptracer.plugins"
    menus_plugin = "skiptracer.menus"
    colors_plugin = "skiptracer.colors"
    loaded_plugins_plugin_dict = {}
    loaded_menus_plugin_dict = {}
    loaded_colors_plugin_dict = {}

    def __init__(self, plugins):
        """Load all the different types of plugin."""
        self.inc_plugins = plugins

        self.loaded_plugins_plugin_dict = self.load_plugins(
            self.plugins_plugin)

        self.loaded_menus_plugin_dict = self.load_plugins(
            self.menus_plugin)

        self.loaded_colors_plugin_dict = self.load_plugins(
            self.colors_plugin)

        # only supporting default menu for now
        self.loaded_menus_plugin_dict['default_menus'](
            self.loaded_plugins_plugin_dict).intromenu()

    @classmethod
    def load_plugins(cls, plugin):
        """Load the plugin and store object in a dict."""
        plugin_dict = {}
        if hasattr(entry_points(), 'select'):
            eps = entry_points().select(group=plugin)
        else:  # pragma: no cover - older importlib.metadata
            eps = entry_points().get(plugin, [])
        for p in eps:
            try:
                plugin_dict[p.name] = p.load()
            except Exception as loaderr:
                # A single broken plugin must not kill the whole app.
                print("  [X] plugin '%s' failed to load: %s" % (p.name, loaderr))
        return plugin_dict
