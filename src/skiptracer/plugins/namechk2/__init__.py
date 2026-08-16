from __future__ import print_function
#
# NameChk scraper: no1special
#
# FIXED version: graceful degradation when the /services/check endpoint
# returns non-JSON. The original code called `return` on the first parse
# error, aborting the entire service sweep. Now it logs the error, records
# a structured result, and continues to the next service.
#
# Original defect: namechk.com /services/check returns non-JSON
# "Could not load results into JSON format" — the entire sweep aborts.
from bs4 import BeautifulSoup
from lxml import html
from requests.utils import quote
from ..base import PageGrabber
from ...colors.default_colors import DefaultBodyColors as bc
import json
import unicodedata
import requests
import lxml.html

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode


class NameChkGrabber(PageGrabber):
    """
    Myspace.com scraper for email lookups

    NOTE: Despite the docstring, this scrapes namechk.com for username
    correlation across 80+ platforms.
    """
    def get_info(self, email, type):
        """
        Looks up user accounts by given email
        """
        print("[" + bc.CPRP + "?" + bc.CEND + "] " +
              bc.CCYN + "NameChk" + bc.CEND)
        username = str(email).split("@")[0]
        ses = requests.Session()
        webproxy = False  # this needs to be a setting
        proxy = ""  # placeholder for now

        if webproxy:
            proto = proxy.split("/")[0].split(":")[0]
            r = ses.get('https://namechk.com/', proxies={proto: bi.proxy})
        else:
            r = ses.get('https://namechk.com/')

        if r.status_code != 200:
            print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                  "Failed to load namechk.com (HTTP {})\n".format(r.status_code) + bc.CEND)
            return {"error": "namechk_homepage_unavailable", "status_code": r.status_code}

        cookies = r.cookies.get_dict()
        services = ["facebook", "youtube", "twitter", "instagram",
                    "blogger", "googleplus", "twitch", "reddit", "ebay", "wordpress",
                    "pinterest", "yelp", "slack", "github", "basecamp", "tumblr",
                    "flickr", "pandora", "producthunt", "steam", "myspace",
                    "foursquare", "okcupid", "vimeo", "ustream", "etsy",
                    "soundcloud", "bitbucket", "meetup", "cashme", "dailymotion",
                    "aboutme", "disqus", "medium", "behance", "photobucket", "bitly",
                    "cafemom", "coderwall", "fanpop", "deviantart", "goodreads",
                    "instructables", "keybase", "kongregate", "livejournal",
                    "stumbleupon", "angellist", "lastfm", "slideshare", "tripit",
                    "fotolog", "paypal", "dribbble", "imgur", "tracky", "flipboard",
                    "vk", "kik", "codecademy", "roblox", "gravatar", "trip", "pastebin",
                    "coinbase", "blipfm", "wikipedia", "ello", "streamme", "ifttt",
                    "webcredit", "codementor", "soupio", "fiverr", "trakt", "hackernews",
                    "five00px", "spotify", "pof", "houzz", "contently", "buzzfeed",
                    "tripadvisor", "hubpages", "scribd", "venmo", "canva", "creativemarket",
                    "bandcamp", "wikia", "reverbnation", "wattpad", "designspiration",
                    "colourlovers", "eyeem", "kanoworld", "askfm", "smashcast", "badoo",
                    "newgrounds", "younow", "patreon", "mixcloud", "gumroad", "quora"]
        soup = self.get_dom(r.text)
        csrf = ''
        try:
            csrf = str(soup.find_all(name="meta")[-1]).split('"')[1]
        except Exception:
            print("  [" + bc.CRED + "X" + bc.CEND + "] " +
                  bc.CYLW + "Could not find CSRF token.\n" + bc.CEND)
        tree = html.fromstring(r.text)

        def get_cookie(cookies):
            for x in cookies.keys():
                return '{}:{}; '.format(x, cookies[x]),
            return ('',)

        def get_token():
            vals = list(
                set(tree.xpath("//input[@name='authenticity_token']/@value")))
            return vals[0] if vals else ''

        token = get_token()
        headers = {"authority": "namechk.com",
                   "method": "POST",
                   "path": "/services/checks",
                   "scheme": "https",
                   "accept": "*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript",
                   "accept-encoding": "gzip, deflate, br",
                   "accept-language": "en-US,en;q=0.9",
                   "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                   "origin": "https://namechk.com",
                   "referer": "https://namechk.com/",
                   "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
                   "x-csrf-token": csrf,
                   "x-requested-with": "XMLHttpRequest",
                   }
        ncook = "_ga=GA1.2.1058625756.1526852807; _gid=GA1.2.371808416.1526852807; _fssid=9c20a864-551e-470f-bd74-6640f9cc9058; __qca=P0-1810536716-1526852807185; _fsuid=e091827a-8a09-4cb9-b841-4bb78b6bc579; __gads=ID=6af13fe549a859bd:T=1526852808:S=ALNI_MZI5yxUiBsOz-2qmDmok0tVeISwvw;" + str(get_cookie(cookies)[0])
        headers['cookie'] = ncook

        data = [
            ('utf8', '%E2%9C%93'),
            ('authenticity_token', quote(token, safe="")),
            ('q', username),
            ('m', ''),
        ]
        if webproxy:
            proto = proxy.split("/")[0].split(":")[0]
            r = ses.post(
                'https://namechk.com/',
                headers=headers,
                data=data,
                proxies={
                    proto: proxy})
        else:
            r = ses.post('https://namechk.com/', headers=headers, data=data)

        try:
            cookies = r.cookies.get_dict()
            cooked = str(get_cookie(cookies)[0])
        except Exception:
            pass

        # FIX: Wrap the initial JSON parse in try/except. If the page returns
        # non-JSON (e.g. "Could not load results into JSON format"), record
        # the error and return early — but with a structured result so callers
        # know why it failed, rather than silently returning None.
        try:
            encres = r.text.encode('ascii', 'ignore').decode('utf8')
            encresdic = json.loads(encres)
            datareq = {}
        except (json.JSONDecodeError, ValueError) as e:
            print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                  "Could not load results into JSON format: {}\n".format(e) + bc.CEND)
            # Return a structured error so the caller can detect the failure mode
            return {"error": "json_parse_failed", "detail": str(e), "raw_snippet": r.text[:200]}

        results = {}
        for xservice in services:
            for dictkey in encresdic.keys():
                datareq["token"] = quote(encresdic[dictkey], safe="")
            datareq['fat'] = quote(csrf, safe="")
            datastring = ""
            try:
                for datakey in datareq.keys():
                    datastring += "{}={}&\n".format(datakey, datareq[datakey])
                datastring += "service={}\n".format(xservice)
            except Exception:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " +
                      bc.CYLW + "Could not find CSRF token.\n" + bc.CEND)
                results[xservice] = {"error": "no_csrf_token"}
                continue  # FIX: continue to next service instead of aborting

            try:
                response = ses.post(
                    'https://namechk.com/services/check',
                    headers=headers,
                    data=datastring)
                # FIX: Wrap per-service JSON parse in try/except
                try:
                    jload = json.loads(response.text)
                except (json.JSONDecodeError, ValueError) as pe:
                    print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                          "Service {} returned non-JSON: {}\n".format(xservice, str(pe)[:100]) + bc.CEND)
                    results[xservice] = {"error": "non_json_response", "raw_snippet": response.text[:200]}
                    continue  # FIX: skip this service, continue sweep

                if jload.get('available', None) is False:
                    if jload.get('callback_url', "") != "":
                        print(
                            "  [" +
                            bc.CGRN +
                            "+" +
                            bc.CEND +
                            "] " +
                            bc.CRED +
                            "Acct Exists: " +
                            bc.CEND +
                            "{}".format(jload.get('callback_url', '')))
                        results[xservice] = {"available": False, "callback_url": jload['callback_url']}
                    else:
                        results[xservice] = {"available": False, "callback_url": ""}
                else:
                    results[xservice] = {"available": jload.get('available', None), "callback_url": jload.get('callback_url', '')}
            except Exception as e:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                      "Could not find required datasets for {}: {}\n".format(xservice, str(e)[:100]) + bc.CEND)
                results[xservice] = {"error": str(e)}
                continue  # FIX: continue to next service instead of aborting

        print()
        # FIX: return structured results dict so callers get data
        return {"username": username, "results": results}
