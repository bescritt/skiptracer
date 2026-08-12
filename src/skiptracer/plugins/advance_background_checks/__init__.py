from __future__ import print_function
from __future__ import absolute_import

from ..base import PageGrabber
from ...colors.default_colors import DefaultBodyColors as bc
from .. import proxygrabber
from time import sleep

import re
import logging
import json
import base64 as b64
import sys

try:
    import __builtin__ as bi
except BaseException:
    import builtins as bi


class AdvanceBackgroundGrabber(PageGrabber):
    """
    Grab data from Advanced Background
    site
    """
    url = ""

    def __init__(self):
        """Load up AdvanceBackgroundGrabber plugin configs."""
        super(AdvanceBackgroundGrabber, self).__init__()

    def get_info(self, lookup, information):
        """
        Uniform call for framework to launch function in a way to single out the
        calls per URL
        """
        print("[" + bc.CPRP + "?" + bc.CEND + "] " +
              bc.CCYN + "AdvanceBackgroundChecks" + bc.CEND)

        return self.abc_try(lookup, information)

    def check_for_captcha(self):
        """
        Check for CAPTCHA, if proxy enabled,try new proxy w/ request, else
        report to STDOUT about CAPTCHA
        """
        captcha = self.soup.find('div', attrs={'class': 'g-recaptcha'})

        if bi.webproxy and captcha is not None:
            try:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                      "Switching proxy, trying again...\n" + bc.CEND)
                bi.proxy = proxygrabber.new_proxy()
                self.abc_try(lookup, information)
                return True
            except Exception as badproxy:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                      "Bad proxy...\n" + bc.CEND)
                pass
        if captcha is not None:
            print(
                "  [" +
                bc.CRED +
                "X" +
                bc.CEND +
                "] " +
                bc.CYLW +
                "Captch detected, use a proxy or complete challenge in browser\n" +
                bc.CEND)
            return True
        else:
            return False

    def makephone(self, information):
        """
        Format the phone number splitting on
        whitespace or hyphens
        """
        info = str(information).strip()
        try:
            if len(info.split("-")) > 1:
                parts = [p for p in info.split("-") if p != ""]
                if len(parts) == 3:
                    return "{}-{}-{}".format(*parts)
        except BaseException:
            pass

        try:
            if len(info.split(" ")) > 1:
                parts = [p for p in info.split(" ") if p != ""]
                if len(parts) == 3:
                    return "({})-{}-{}".format(parts[0], parts[1], parts[2])
        except BaseException:
            pass

        try:
            # If len of data is 10 and is an integer, break and format
            # as needed for URL
            if len(information) == 10:
                dashphone = '{}-{}-{}'.format(
                    information[0:3], information[3:6], information[6:])
                return dashphone
            if len(information) != 10:
                print(
                    "  [" +
                    bc.CRED + "X" + bc.CEND + "] " +
                    bc.CYLW +
                    "Check search string, should be 10 digits.\n" +
                    bc.CEND)
                return
        except BaseException:
            return

    def grab_phone(self, information):
        """Create phone number format."""
        try:
            self.num = self.makephone(information)
            if self.num is None:
                return
            self.url = "https://www.advancedbackgroundchecks.com/{}".format(
                self.num)
        except Exception as e:
            print(
                "  [" +
                bc.CRED + "X" + bc.CEND + "] " +
                bc.CYLW +
                "Could not produce required URL.\n" +
                bc.CEND)
            return

    def grab_email(self, information):
        """Grab the targets email."""
        if str(information).split('@')[1]:
            email = str(b64.b64encode(information.encode('utf-8'))).split("b'")[1]
            email = email.split("'")[0]
            self.url = "https://www.advancedbackgroundchecks.com/emails/" + email

    def grab_name(self, information):
        """Grab the targets Name."""
        if str(information).split(' ')[1]:
            self.url = "https://www.advancedbackgroundchecks.com/name/{}".format(
                str(information).replace(' ', '-'))

    def find_results(self, lookup):
        """
        Check if the search found any results.
        Returns the list of JSON-LD <script> tags, or an empty list.
        """
        if self.soup.find(
                'div', {'id': 'no-result-widgets'}):  # Report if no results
            print("  [" + bc.CRED + "X" + bc.CEND + "] " +
                  bc.CYLW + "No results were found.\n" + bc.CEND)
            return []

        checkres = self.soup.find_all("h1")

        if lookup == "phone":
            for xcheck in checkres:
                if xcheck.text in [
                        "We could not find any results based on your search criteria.  Please review your search and try again, or try our sponsors for more information.", "Top Results for " + str(self.num)]:
                    print("  [" + bc.CRED + "X" + bc.CEND + "] " +
                          bc.CYLW + "No results were found.\n" + bc.CEND)
                    return []

        return self.soup.find_all(
            'script', type="application/ld+json")  # Scrape JSON-LD from DOM

    def grab_json_data(self, script):
        """
        Grab the JSON-LD data and normalise it to a list of person dicts.
        Accepts a BeautifulSoup tag or a raw JSON string.
        """
        if hasattr(script, 'get_text'):
            text = script.get_text().strip()
        else:
            text = str(script).strip()
        text = text.replace("\n", "").replace("\t", "")
        data = json.loads(text)  # Loads data as JSON
        if isinstance(data, dict):
            return [data]
        return list(data)

    def get_person_list(self, person_list):
        """
        Iterate through the person list and collect structured results.
        """
        address_list = []
        for person in person_list:
            addrfirst = 0

            name = person.get("name")
            print("  [" + bc.CGRN + "+" + bc.CEND + "] " +
                  bc.CRED + "Name: " + bc.CEND + str(name))

            if person.get("birthDate"):  # Set DoB
                print("  [" + bc.CGRN + "+" + bc.CEND + "] " +
                      bc.CRED + "D.o.B: " + bc.CEND + str(person.get("birthDate")))

            if person.get("additionalName"):  # Set additional names AKA
                print("  [" + bc.CGRN + "+" + bc.CEND + "] " +
                      bc.CRED + "Alias: " + bc.CEND)
                for xaka in person.get("additionalName"):
                    print(
                        "    [" +
                        bc.CGRN + "=" + bc.CEND + "] " +
                        bc.CRED + "AKA: " + bc.CEND + str(xaka))

            telephone = []
            email = []
            # Some records embed a second JSON-LD block with contact details
            url2 = person.get('@id')
            if url2:
                try:
                    self.url2 = url2
                    self.source2 = self.get_source(self.url2)
                    self.soup2 = self.get_dom(self.source2)
                    script_html2 = self.soup2.find_all(
                        'script', type="application/ld+json")
                    if len(script_html2) > 1:
                        block = script_html2[1].get_text().strip()
                        block = block.replace("\n", "").replace("\t", "")
                        person_list2 = json.loads(block)
                        telephone = person_list2.get('telephone', [])
                        email = person_list2.get('email', [])
                except Exception:
                    pass

            if telephone:
                print("  [" + bc.CGRN + "+" + bc.CEND + "] " +
                      bc.CRED + "Phone: " + bc.CEND)
                for tele in telephone:
                    print("    [" + bc.CGRN + "=" + bc.CEND + "] " +
                          bc.CRED + "#: " + bc.CEND + str(tele))
            if email:
                print("  [" + bc.CGRN + "+" + bc.CEND + "] " +
                      bc.CRED + "Email: " + bc.CEND)
                for em in email:
                    print("   [" + bc.CGRN + "=" + bc.CEND + "] " +
                          bc.CRED + "Addr: " + bc.CEND + str(em))

            if person.get("address"):  # Set Addresses
                print("  [" + bc.CGRN + "+" + bc.CEND + "] " +
                      bc.CRED + "Addresses.: " + bc.CEND)
                for addy in person.get("address"):
                    addrfirst += 1
                    if addrfirst == 1:
                        print(
                            "    [" + bc.CGRN + "=" + bc.CEND + "] " +
                            bc.CRED + "Current Address: " + bc.CEND)
                    else:
                        print(
                            "    [" + bc.CGRN + "=" + bc.CEND + "] " +
                            bc.CRED + "Prev. Address: " + bc.CEND)
                    print("      [" + bc.CGRN + "-" + bc.CEND + "] " +
                          bc.CRED + "Street: " + bc.CEND +
                          str(addy.get("streetAddress")))
                    print("      [" + bc.CGRN + "-" + bc.CEND + "] " +
                          bc.CRED + "City: " + bc.CEND +
                          str(addy.get("addressLocality")))
                    print("      [" + bc.CGRN + "-" + bc.CEND + "] " +
                          bc.CRED + "State: " + bc.CEND +
                          str(addy.get("addressRegion")))
                    print("      [" + bc.CGRN + "-" + bc.CEND + "] " +
                          bc.CRED + "ZipCode: " + bc.CEND +
                          str(addy.get("postalCode")))
                    address_list.append({"city": addy.get("addressLocality"),
                                         "state": addy.get("addressRegion"),
                                         "zip_code": addy.get("postalCode"),
                                         "address": addy.get("streetAddress")})

            if person.get("relatedTo"):  # Set Relatives
                print("  [" + bc.CGRN + "+" + bc.CEND + "] " +
                      bc.CRED + "Related: " + bc.CEND)
                for xrelate in [item.get("name") for item in person.get(
                        "relatedTo")]:
                    print(
                        "    [" + bc.CGRN + "=" + bc.CEND + "] " +
                        bc.CRED + "Known Relative: " + bc.CEND + str(xrelate))

            self.info_list.append({"name": name,
                                   "birth_date": person.get("birthDate"),
                                   "additional_names": person.get("additionalName"),
                                   "telephone": telephone,
                                   "email": email,
                                   "address_list": address_list,
                                   "related_to": [item.get("name") for item in (person.get("relatedTo") or [])]})

    def abc_try(self, information, lookup):
        """
        Determines different URL constructs based on user supplied data
        """
        if lookup == "phone":
            self.grab_phone(information)

        if lookup == "email":  # Make the URL for email lookup
            self.grab_email(information)

        if lookup == "name":  # Make the URL for name lookup
            self.grab_name(information)

        self.source = self.get_source(self.url)
        self.soup = self.get_dom(self.source)

        if self.check_for_captcha() == True:
            print(("  [" + bc.CRED + "X" + bc.CEND + "] " +
                   bc.CYLW + "Goto: {}" + bc.CEND).format(self.url))

            self.iscomplete = input(
                "  [" + bc.CRED + "!]" + bc.CYLW +
                "Have you completed the CAPTCHA? " + bc.CEND)

            if str(self.iscomplete).lower() in ['no', False, 0]:
                print("  [" + bc.CRED + "X" + bc.CEND + "] " + bc.CYLW +
                      "User has not completed the CAPTCHA\n" + bc.CEND)
                return False

        script_tags = self.find_results(lookup)
        if not script_tags:
            print("  [" + bc.CRED + "X" + bc.CEND + "] " +
                  bc.CYLW +
                  "Unable to complete request... Try again later...\n" +
                  bc.CEND)
            return

        # Use the first JSON-LD block (the primary person record)
        person_list = self.grab_json_data(script_tags[0])
        self.get_person_list(person_list)

        print()
        return self.info_list
