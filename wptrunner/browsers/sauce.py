# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import urlparse
from ConfigParser import SafeConfigParser

from .base import Browser, ExecutorBrowser, require_arg
from ..executors import executor_kwargs as base_executor_kwargs
from ..executors.executorseleniumremote import (SeleniumRemoteTestharnessExecutor,
                                                SeleniumRemoteRefTestExecutor)

from ..environment import RemoteServerEnvironment, subdomains

__wptrunner__ = {"product": "sauce",
                 "check_args": "check_args",
                 "browser": "SauceBrowser",
                 "executor": {"testharness": "SeleniumRemoteTestharnessExecutor",
                              "reftest": "SeleniumRemoteRefTestExecutor"},
                 "env": "RemoteServerEnvironment",
                 "browser_kwargs": "browser_kwargs",
                 "executor_kwargs": "executor_kwargs",
                 "env_options": "env_options"}

def read_sauce_config(config_path):
    config_path = os.path.abspath(config_path)

    config = SafeConfigParser()
    with open(config_path) as f:
        config.readfp(f)

    data = {"url": None,
            "browser": None,
            "capabilities": {"disablePopupHandler": True}}

    url = config.get("sauce", "url")

    credentials_path = os.path.join(os.path.dirname(config_path),
                                    config.get("sauce", "credentials"))

    with open(credentials_path) as f:
        config.readfp(f)
    username = config.get("credentials", "username")
    key = config.get("credentials", "key")

    url_parts = list(urlparse.urlsplit(url))
    full_netloc = "%s:%s@%s" % (username, key, url_parts[1])
    url_parts[1] = full_netloc
    data["url"] = urlparse.urlunsplit(url_parts)

    data["browser"] = config.get("capabilities", "browser")
    for key in ['os', 'os_version', 'browser', 'version']:
        data["capabilities"][key] = config.get("capabilities", key)

    '''
    data["browser"] = 'edge'
    data['capabilities'] = {
        'os': 'Windows',
        'os_version': '10',
        'browser': 'edge',
        'version': '14',
    }

    data["browser"] = 'safari'
    data['capabilities'] = {
        'os': 'OS X',
        'os_version': 'Sierra', # 10.12
        'browser': 'safari',
        'version': '10',
    }

    data["browser"] = 'chrome'
    data['capabilities'] = {
        'os': 'OS X',
        'os_version': 'Sierra', # 10.12
        'browser': 'chrome',
        'version': '56',
    }

    data["browser"] = 'firefox'
    data['capabilities'] = {
        'os': 'OS X',
        'os_version': 'Sierra', # 10.12
        'browser': 'firefox',
        'version': '51',
    }
    '''

    return data

def check_args(**kwargs):
    require_arg(kwargs, "sauce_config_path")

def browser_kwargs(**kwargs):
    sauce_config = read_sauce_config(kwargs["sauce_config_path"])

    return {"sauce_config": sauce_config}

def get_capabilities(sauce_config):
    from selenium.webdriver import DesiredCapabilities

    capabilities_attr = sauce_config["browser"].replace(" ", "").upper()
    if hasattr(DesiredCapabilities, capabilities_attr):
        capabilities = getattr(DesiredCapabilities, capabilities_attr)
    else:
        capabilities = {"browserName": sauce_config["browser"]}

    capabilities.update(sauce_config["capabilities"])

    return capabilities

def executor_kwargs(test_type, server_config, cache_manager, run_info_data,
                    **kwargs):
    executor_kwargs = base_executor_kwargs(test_type, server_config,
                                           cache_manager, **kwargs)


    # executor_kwargs["capabilities"] = get_capabilities(kwargs["sauce_config"])
    sauce_config = read_sauce_config(kwargs["sauce_config_path"])

    executor_kwargs["capabilities"] = {
        'os': sauce_config['capabilities']['os'],
        'os_version': sauce_config['capabilities']['os_version'],
        'browser': sauce_config['capabilities']['browser'],
        'version': sauce_config['capabilities']['version'],
    }

    return executor_kwargs


def env_options():
    # Need to convince this to use w3c-test.org
    host = "w3c-test.org"
    domains = {item: ("%s.%s" % (item, host) if item else host)
               for item in subdomains}
    return {"external_config": {"host": host,
                                "domains": domains,
                                "ports": {"http": [80, 81],
                                          "https": [443],
                                          "ws": [80]}}}


class SauceBrowser(Browser):
    init_timeout = 300

    def __init__(self, logger, sauce_config):
        Browser.__init__(self, logger)
        self.sauce_config = sauce_config

    def start(self):
        pass

    def stop(self):
        pass

    def pid(self):
        return None

    def is_alive(self):
        # TODO: Should this check something about the connection?
        return True

    def cleanup(self):
        pass

    def executor_browser(self):
        return ExecutorBrowser, {"webdriver_url": self.sauce_config["url"]}
