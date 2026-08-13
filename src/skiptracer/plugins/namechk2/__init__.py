from __future__ import print_function
#
# NameChk scraper: no1special
#
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
    """
    def get_info(self, email, type):
        """
        Looksup user accounts by given email
        """
        print("[" + bc.CPRP + "?" + bc.CEND + "] " +
              bc.CCYN + "NameChk" + bc.CEND)
        username = str(email).split("@")[0]
        ses = requests.Session()
        webproxy = False # this needs to be a setting
        proxy = "" # placeholder for now

        def _is_blocked_response(resp_text, status_code):
            """Detect common anti-bot/blocking responses.
            Returns a reason string or None if not blocked.
            """
            if status_code in (403, 429):
                return 'http_status_{}'.format(status_code)
            lower = (resp_text or '').lower()
            blockers = ('captcha', 'recaptcha', 'cloudflare', 'please enable javascript',
                        'access denied', 'forbidden', 'verify you are human', 'bot')
            for token in blockers:
                if token in lower:
                    return 'contains_{}'.format(token.replace(' ', '_'))
            return None

        if webproxy:
            proto = proxy.split("/")[0].split(":")[0]
            r = ses.get('https://namechk.com/', proxies={proto: bi.proxy})
        else:
            r = ses.get('https://namechk.com/')

        # detect anti-bot / blocked responses early
        blocked_reason = _is_blocked_response(getattr(r, 'text', ''), getattr(r, 'status_code', 0))
        if blocked_reason:
            print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                  "NameChk appears to be blocking automated requests: {}\n".format(blocked_reason) + bc.CEND)
            return {'blocked': True, 'reason': blocked_reason}

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
        except Exception as e:
            print("  [" + bc.CRED + "X" + bc.CEND + "] " +
                  bc.CYLW + "Could not find CSRF token.\n" + bc.CEND)
            pass  # return # print e
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
        ncook = "_ga=GA1.2.1058625756.1526852807; _gid=GA1.2.371808416.1526852807; _fssid=9c20a864-551e-470f-bd74-6640f9cc9058; __qca=P0-1810536716-1526852807185; _fsuid=e091827a-8a09-4cb9-b841-4bb78b6bc579; __gads=ID=6af13fe549a859bd:T=1526852808:S=ALNI_MZI5yxUiBsOz-2qmDmok0tVeISwvw;" + str(get_cookie(cookies)[
                                                                                                                                                                                                                                                                                                     0])
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
        # detect blocking after the post
        blocked_reason = _is_blocked_response(getattr(r, 'text', ''), getattr(r, 'status_code', 0))
        if blocked_reason:
            print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                  "NameChk appears to be blocking automated requests on POST: {}\n".format(blocked_reason) + bc.CEND)
            return {'blocked': True, 'reason': blocked_reason}
        try:
            cookies = r.cookies.get_dict()
            cooked = str(get_cookie(cookies)[0])
        except Exception as e:
            # print ("  ["+bc.CRED+"X"+bc.CEND+"] "+bc.CYLW+"Could not locate required cookies.\n"+bc.CEND)
            pass
        try:
            encres = r.text.encode('ascii', 'ignore').decode('utf8')
            encresdic = json.loads(encres)
            datareq = {}
        except Exception as e:
            print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                  "Could not load results into JSON format.\n" + bc.CEND)
            return  # print e

        for xservice in services:
            for dictkey in encresdic.keys():
                datareq["token"] = quote(encresdic[dictkey], safe="")
            datareq['fat'] = quote(csrf, safe="")
            datastring = ""
            try:
                for datakey in datareq.keys():
                    datastring += "{}={}&".format(datakey, datareq[datakey])
                datastring += "service={}".format(xservice)
            except Exception as e:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " +
                      bc.CYLW + "Could not find CSRF token.\n" + bc.CEND)
                return
            try:
                response = ses.post(
                    'https://namechk.com/services/check',
                    headers=headers,
                    data=datastring)
                # detect blocking on service check response
                blocked_reason = _is_blocked_response(getattr(response, 'text', ''), getattr(response, 'status_code', 0))
                if blocked_reason:
                    print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                          "NameChk appears to be blocking automated requests on service check: {}\n".format(blocked_reason) + bc.CEND)
                    return {'blocked': True, 'reason': blocked_reason}

                jload = json.loads(response.text)
                if jload['available'] == False:
                    if jload['callback_url'] == "":
                        pass
                    else:
                        print(
                            "  [" +
                            bc.CGRN +
                            "+" +
                            bc.CEND +
                            "] " +
                            bc.CRED +
                            "Acct Exists: " +
                            bc.CEND +
                            "{}".format(
                                jload['callback_url']))

            except Exception as e:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                      "Could not find required datasets.\n" + bc.CEND)
                return  # pass
        print()
        return
