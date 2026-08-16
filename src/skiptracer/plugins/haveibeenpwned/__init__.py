from __future__ import print_function
from __future__ import absolute_import
#######################################################################
#   haveibeenpwned scraper - returns breach name and date for email     #
#######################################################################
# Fixed version: removed dead cfscrape dependency, replaced fragile
# ast.literal_eval JSON parsing with json.loads, added proper error
# handling for expired/invalid API keys (401).
#
# Original defects:
#   1. cfscrape is uninstallable on Python 3.13 (Py2 API usage)
#   2. ast.literal_eval on raw bytes fails on modern API responses
#   3. No handling of 401 (expired key) — silently proceeds to crash
from ..base import PageGrabber
from ...colors.default_colors import DefaultBodyColors as bc
from .. import proxygrabber
import logging
import json
import requests  # stdlib-compatible, replaces dead cfscrape usage

logger = logging.getLogger(__name__)


def _make_scraper():
    """Return a requests.Session (HIBP API does not use Cloudflare bot protection).

    The original code used cfscrape which is uninstallable on Python 3.13.
    HIBP's API explicitly does NOT use Cloudflare challenge pages — a
    plain requests session suffices.
    """
    try:
        import requests as _requests
        session = _requests.Session()
        session.headers.update({"User-Agent": "skiptracer/4.0 (+https://github.com/bescritt/skiptracer)"})
        return session
    except Exception as e:
        print(
            "  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
            "requests unavailable: {}\n".format(e) + bc.CEND)
        return None


class HaveIBeenPwnedGrabber(PageGrabber):
    """
    HIBP (Have I Been Pwned) scraper for email breach lookups.
    Uses the v3 Breached Account API directly.
    """
    def get_info(self, email, category):
        """
        Uniform call for framework — delegates to trymore().
        """
        print("[" + bc.CPRP + "?" + bc.CEND + "] " +
              bc.CCYN + "HaveIBeenPwned" + bc.CEND)
        self.count = 0
        self.resurl = 0
        return self.trymore(email)

    def trymore(self, email):
        """
        Actual logic for HIBP v3 breached-account lookup.
        Handles: HTTP 404 (no breaches), HTTP 401 (key issue),
        HTTP 403 (rate-limited or key invalid), and parse errors.
        """
        while self.resurl == 0:
            self.count += 1
            url = 'https://haveibeenpwned.com/api/v3/breachedaccount/{}'.format(email)

            scraper = _make_scraper()
            if scraper is None:
                self.info_dict['hibp'] = {'status': 'error', 'message': 'requests unavailable'}
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                      "Cannot make HTTP requests — requests module unavailable.\n" + bc.CEND)
                return self.info_dict

            headers = {
                'user-agent': 'skiptracer/4.0',
                'hibp-api-key': self.env.get('HAVEIBEENPWNED_API_KEY', ''),
                'content-type': 'application/json',
            }
            self.source = scraper.get(url, headers=headers)

            # HTTP 404 = no breaches found for this account
            if self.source.status_code == 404:
                print("  [" + bc.CGRN + "+" + bc.CEND + "] " +
                      bc.CCYN + "No breaches found for: " + bc.CEND +
                      bc.CCYN + email + bc.CEND)
                self.info_dict['hibp'] = {'status': 'no_breaches', 'email': email}
                self.resurl = 1
                return self.info_dict

            # HTTP 401 = API key missing or invalid
            if self.source.status_code == 401:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                      "HIBP API key invalid or expired (HTTP 401).\n" + bc.CEND)
                self.info_dict['hibp'] = {
                    'status': 'auth_error',
                    'message': 'HAVEIBEENPWNED_API_KEY is invalid, expired, or missing',
                    'http_status': 401,
                }
                self.resurl = 1
                return self.info_dict

            # HTTP 403 = rate limited (even with a valid key)
            if self.source.status_code == 403:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                      "HIBP rate-limited (HTTP 403). Wait 60s before retrying.\n" + bc.CEND)
                self.info_dict['hibp'] = {
                    'status': 'rate_limited',
                    'http_status': 403,
                }
                self.resurl = 1
                return self.info_dict

            # HTTP 200 = breaches found
            if self.source.status_code == 200:
                try:
                    # FIX: use json.loads instead of fragile ast.literal_eval chain
                    self.source = self.source.json()
                except (json.JSONDecodeError, ValueError) as e:
                    print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                          "Failed to parse HIBP JSON: {}\n".format(e) + bc.CEND)
                    self.info_dict['hibp'] = {
                        'status': 'parse_error',
                        'message': str(e),
                    }
                    self.resurl = 1
                    return self.info_dict

                for dataset in self.source:
                    self.result = dataset
                    if self.result:
                        self.breach = self.result.get('BreachDate', 'Unknown')
                        self.domain = self.result.get('Domain', 'Unknown')
                        self.title = self.result.get('Title', 'Unknown')
                        self.exposes = self.result.get('DataClasses', [])
                        self.info_dict.update({
                            "BreachDate": self.breach,
                            "Domain": self.domain,
                            "Title": self.title,
                            "DataExposed": self.exposes})
                        print(
                            "  [" +
                            bc.CGRN +
                            "+" +
                            bc.CEND +
                            "] " +
                            bc.CRED +
                            "Dump Name: " +
                            bc.CEND +
                            self.title)
                        print(
                            "    [" +
                            bc.CGRN +
                            "=" +
                            bc.CEND +
                            "] " +
                            bc.CRED +
                            "Domain: " +
                            bc.CEND +
                            self.domain)
                        print(
                            "    [" +
                            bc.CGRN +
                            "=" +
                            bc.CEND +
                            "] " +
                            bc.CRED +
                            "Breach: " +
                            bc.CEND +
                            self.breach)
                        print(
                            "    [" +
                            bc.CGRN +
                            "=" +
                            bc.CEND +
                            "] " +
                            bc.CRED +
                            "Exposes: " +
                            bc.CEND)

                        for xpos in self.exposes:
                            print(
                                "      [" +
                                bc.CGRN +
                                "-" +
                                bc.CEND +
                                "] " +
                                bc.CRED +
                                "DataSet: " +
                                bc.CEND +
                                xpos)
                    else:
                        print(
                            "  [" + bc.CRED + "X" + bc.CEND + "] " +
                            bc.CYLW + "No results were found.\n" + bc.CEND)

            # Any other HTTP status
            else:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                      "HIBP returned HTTP {}: {}\n".format(
                          self.source.status_code, self.source.text[:200]) +
                      bc.CEND)
                self.info_dict['hibp'] = {
                    'status': 'http_error',
                    'http_status': self.source.status_code,
                    'response': self.source.text[:200],
                }

            self.resurl = 1
            print()
            return self.info_dict


# Backward-compatible alias for the original (misspelled) class name.
# setup.py entry-point references 'HaveIBeenPwwnedGrabber' — keep the alias
# so existing installations don't break.
HaveIBeenPwwnedGrabber = HaveIBeenPwnedGrabber
