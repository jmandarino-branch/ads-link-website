import json
import re
from urllib.parse import urlparse
from urllib.parse import ParseResult


import dns.resolver
import requests


class ClickTrackingDomain:
    """An object that represents the data of a Click tracking domain

    url: (urllib.parse.ParseResult) the CTD url
    cname: (str) where the domain is cnam'd to
    AASA: (dict) the AASA file downloaded
    SSL: (bool) if the domain has SSL set up
    bundle: (str) the bundle information from the AASA
    prefix: (str) the app prefix from the AASA
    paths: (list[str]) paths dictated by email
    https://docs.python.org/3/library/urllib.parse.html#url-parsing

    """
    AASA_ROUTE = 'apple-app-site-association'
    WELL_KNOWN_AASA_ROUTE = '.well-known/apple-app-site-association'

    def __init__(self, url, cname=None):
        self.url = url
        self.cname = cname
        self.AASA = None
        self.SSL = False

        self.bundle = ''
        self.prefix = ''
        self.paths = []

    def get_url_text(self):
        if isinstance(self.url, ParseResult):
            return self.url.geturl()

    def cnamed_correctly(self):
        return str(self.cname) == 'thirdparty.bnc.lt.'

    def get_aasa_url(self):
        if self.url is None:
            return None
        url = self.url._replace(path=self.AASA_ROUTE, params='', query='', fragment='')
        return url.geturl()

    def get_well_known_aasa_url(self):
        if self.url is None:
            return None
        url = self.url._replace(path=self.WELL_KNOWN_AASA_ROUTE, params='', query='', fragment='')
        return url.geturl()


    def is_valid_path(self):
        if self.url is None:
            return False

        if self.paths is []:
            return True
        url_path = self.url.path

        for path in self.paths:
            # escape characters, then replace \* with .* to follow convention
            r = re.compile(re.escape(path).replace('\*', '.*'))

            print(path, r)
            result = r.match(url_path)
            if result:
                return True
        return False


def validate_ssl_aasa(ctd, wellknown=False):

    try:
        if wellknown:
            r = requests.get(ctd.get_well_known_aasa_url(), verify=True)
        else:
            r = requests.get(ctd.get_aasa_url(), verify=True)

        ctd.SSL = True

        if r.status_code == 200:
            print(r.text)

            try:
                ctd.AASA = r.json()
            except json.JSONDecodeError:
                ctd.AASA = None
                print("no AASA")
                return False

    except requests.exceptions.SSLError:
        print("no SSL")
        ctd.SSL = False
        ctd.AASA = None
        return False

    return True


def parse_aasa_for_path(ctd):
    # check path
    if not ctd.AASA:
        return False
    applinks = ctd.AASA.get('applinks', None)
    if applinks:
        details = applinks.get('details', None)
        if details and isinstance(details, list):
            paths = details[0].get('paths', None)
            appID = details[0].get('appID', None)

            if appID:
                prefix = appID.split('.', 1)[0]
                bundle = appID.split('.', 1)[1]

                ctd.prefix = prefix
                ctd.bundle = bundle

            if paths:
                ctd.paths = paths

    return ctd.is_valid_path()


def ctd_service_driver(url):
    ctd_url = urlparse(url)

    ctd = ClickTrackingDomain(ctd_url)
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ['8.8.8.8']

    # This is to get CNAME
    try:
        answer = resolver.query(ctd.url.netloc, 'CNAME')
        ctd.cname = answer.rrset[0].target
        print(ctd.cname)
    except dns.resolver.NoAnswer:
        print('no answer')
    except dns.resolver.NXDOMAIN:
        print('this is bad')
        return None

    aasa = validate_ssl_aasa(ctd, False)

    if not aasa:
        validate_ssl_aasa(ctd, True)

    aasa = parse_aasa_for_path(ctd)

    print(aasa)

    return ctd
