from __future__ import print_function
from __future__ import absolute_import
#######################################################################
#   haveibeenpwned scraper - returns breach name and date for email     #
#######################################################################
from ..base import PageGrabber
from ...colors.default_colors import DefaultBodyColors as bc
from .. import proxygrabber
import logging
import json
import ast
try:
    import __builtin__ as bi
except BaseException:
    import builtins as bi


def _get_api_key(env):
    # prefer explicit HIBP API key env var; support legacy name
    return env.get('HAVEIBEENPWNED_API_KEY') or env.get('HIBP_API_KEY') or env.get('HAVEIBEENPWNED_API_KEY')


class HaveIBeenPwwnedGrabber(PageGrabber):
    """
    Use HIBP v3 API directly (requires API key). Falls back gracefully when
    no key is available or network errors occur.
    """
    def get_info(self, email, category):
        """Uniform call for framework"""
        print("[" + bc.CPRP + "?" + bc.CEND + "] " + bc.CCYN + "HaveIbeenPwned" + bc.CEND)
        self.info_dict = {}
        api_key = _get_api_key(self.env)
        if not api_key:
            print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW + "HIBP API key not configured; set HAVEIBEENPWNED_API_KEY or HIBP_API_KEY in environment" + bc.CEND)
            return self.info_dict

        url = f'https://haveibeenpwned.com/api/v3/breachedaccount/{email}'
        headers = {
            'user-agent': self.ua,
            'hibp-api-key': api_key,
            'Accept': 'application/json'
        }

        try:
            import requests
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 404:
                # no breaches for this account
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW + "No results were found." + bc.CEND)
                return self.info_dict
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logging.debug("HIBP request failed: %s", e)
            print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW + "HIBP query error: {}".format(e) + bc.CEND)
            return self.info_dict

        # data is a list of breach dicts
        for dataset in data:
            if not dataset:
                continue
            self.breach = dataset.get('BreachDate')
            self.domain = dataset.get('Domain')
            self.title = dataset.get('Title')
            self.exposes = dataset.get('DataClasses', [])
            self.info_dict.update({
                "BreachDate": self.breach,
                "Domain": self.domain,
                "Title": self.title,
                "DataExposed": self.exposes
            })
            print("  [" + bc.CGRN + "+" + bc.CEND + "] " + bc.CRED + "Dump Name: " + bc.CEND + str(self.title))
            print("    [" + bc.CGRN + "=" + bc.CEND + "] " + bc.CRED + "Domain: " + bc.CEND + str(self.domain))
            print("    [" + bc.CGRN + "=" + bc.CEND + "] " + bc.CRED + "Breach: " + bc.CEND + str(self.breach))
            print("    [" + bc.CGRN + "=" + bc.CEND + "] " + bc.CRED + "Exposes: " + bc.CEND)
            for xpos in self.exposes:
                print("      [" + bc.CGRN + "-" + bc.CEND + "] " + bc.CRED + "DataSet: " + bc.CEND + str(xpos))

        print()
        return self.info_dict


# Backwards/expected name for other callers/tests
HaveIBeenPwnedGrabber = HaveIBeenPwwnedGrabber
