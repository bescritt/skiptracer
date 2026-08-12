"""Network-mocked tests for scraping plugins.

These exercise real parse logic against synthetic HTTP responses via the
`responses` library, so the suite runs fully offline and deterministically.
"""

import builtins as bi
import responses

import pytest

from skiptracer.plugins.fouroneone import FourOneOneGrabber
from skiptracer.plugins.myspace import MySpaceGrabber
from skiptracer.plugins.whoismind import WhoisMindGrabber
from skiptracer.plugins.advance_background_checks import AdvanceBackgroundGrabber
from skiptracer.plugins.true_people import TruePeopleGrabber


# --------------------------------------------------------------------------
# FourOneOne (reverse phone)
# --------------------------------------------------------------------------
@responses.activate
def test_fouroneone_parses_address_blocks():
    html = """
    <html><body>
      <div class='cname'>John Doe</div>
      <div class='adr_1'><span itemprop='streetAddress'>1 Main St</span>
        <span itemprop='addressLocality'>Town</span>
        <span itemprop='addressRegion'>CA</span>
        <span itemprop='postalCode'>90001</span></div>
    </body></html>
    """
    responses.add(responses.GET, 'https://411.info/reverse/?r=1234567890',
                  body=html, status=200, content_type='text/html')
    g = FourOneOneGrabber()
    res = g.get_info('1234567890', 'phone')
    assert res['name'] == 'John Doe'
    assert res['street'] == '1 Main St'
    assert res['state'] == 'CA'
    assert res['zipcode'] == '90001'


@responses.activate
def test_fouroneone_no_results_returns_empty_dict():
    responses.add(responses.GET, 'https://411.info/reverse/?r=0000000000',
                  body="<html><body><p>nothing</p></body></html>",
                  status=200, content_type='text/html')
    g = FourOneOneGrabber()
    res = g.get_info('0000000000', 'phone')
    assert res == {}


# --------------------------------------------------------------------------
# MySpace (email search, no account)
# --------------------------------------------------------------------------
@responses.activate
def test_myspace_no_account_reports_not_found():
    responses.add(responses.GET,
                  'https://myspace.com/search/people?q=a@b.com',
                  body="<html><body><p>no results</p></body></html>",
                  status=200, content_type='text/html')
    g = MySpaceGrabber()
    res = g.get_info('a@b.com', 'email')
    assert res['name'] is False
    assert res['account'] == 'Not found'


# --------------------------------------------------------------------------
# WhoIsMind (registered domains by email)
# --------------------------------------------------------------------------
@responses.activate
def test_whoismind_extracts_domains():
    html = """
    <html><body>
      <a href="https://example.com">example.com</a>
      <a href="https://other.org">other.org</a>
      <a href="https://example.com">example.com</a>
    </body></html>
    """
    responses.add(responses.GET, 'https://whoisamped.com/email/a@b.com.html',
                  body=html, status=200, content_type='text/html')
    g = WhoisMindGrabber()
    res = g.get_info('a@b.com', 'email')
    domains = [d['domain'] for d in res[0]]
    assert 'example.com' in domains
    assert 'other.org' in domains
    assert domains.count('example.com') == 1  # deduped via np.unique


# --------------------------------------------------------------------------
# AdvancedBackgroundChecks (JSON-LD parsing)
# --------------------------------------------------------------------------
@responses.activate
def test_abc_parses_jsonld_person():
    import json
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "@id": "https://www.advancedbackgroundchecks.com/secondary/1",
        "name": "Alice Smith",
        "birthDate": "1985-04-12",
        "address": [{
            "@type": "PostalAddress",
            "streetAddress": "1 Elm St",
            "addressLocality": "Springfield",
            "addressRegion": "IL",
            "postalCode": "62701"
        }],
        "relatedTo": [{"@type": "Person", "name": "Bob Smith"}]
    }
    page_html = (
        "<html><body>"
        "<script type='application/ld+json'>" + json.dumps(person) +
        "</script>"
        "<script type='application/ld+json'>"
        '{"@type":"Person","telephone":["555-1234"],"email":["a@b.com"]}'
        "</script>"
        "</body></html>"
    )
    responses.add(responses.GET,
                  'https://www.advancedbackgroundchecks.com/name/Alice-Smith',
                  body=page_html, status=200, content_type='text/html')
    g = AdvanceBackgroundGrabber()
    out = g.get_info('Alice Smith', 'name')
    assert isinstance(out, list) and len(out) == 1
    assert out[0]['name'] == 'Alice Smith'
    assert out[0]['birth_date'] == '1985-04-12'
    assert out[0]['address_list'][0]['city'] == 'Springfield'
    assert out[0]['related_to'] == ['Bob Smith']


# --------------------------------------------------------------------------
# TruePeopleSearch (phone URL builder + no-result detection)
# --------------------------------------------------------------------------
@responses.activate
def test_truepeople_no_results_reports_not_found():
    html = ("<html><body>"
            "<div class='card-summary'>none</div>"
            "</body></html>")
    responses.add(responses.GET,
                  'https://www.truepeoplesearch.com/results',
                  body=html, status=200, content_type='text/html')
    g = TruePeopleGrabber()
    # makephone('1234567890') -> '(123)-456-7890'; url built internally
    out = g.get_info('1234567890', 'phone')
    # With a 'card-summary' present but no parsed records, info_dict stays empty
    assert out == {}
