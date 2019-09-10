import json
import re
from urllib.parse import urlparse
from urllib.parse import ParseResult


import dns.resolver
import requests


class ClickTrackingParsingError(Exception):
    pass


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

        self.branch_link = None

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
            not_flag = False
            if 'NOT' in path:
                not_flag = True
                path = path.replace('NOT', '').strip()
            # escape characters, then replace \* with .* to follow convention
            r = re.compile(re.escape(path).replace('*', '.*'))
            result = r.match(url_path)
            if result:
                if not_flag:
                    return False
                return True
        return False


def validate_ssl_aasa(ctd, wellknown=False):
    """Validates Both SSL and AASA file

    Sets the CTD obj's AASA and SSL

    AASA -- will be a json file
    SSL -- A boolean true if SSL exist, False if not

    :param ctd: (obj: ClickTrackingDomain) The click tracking domain
    :param wellknown: A flag to check which path to try (either standard or .well-known)
    :return: bool True if AASA is found and SSL
    """

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
                return False

    except requests.exceptions.SSLError:
        ctd.SSL = False
        ctd.AASA = None
        return False
    except requests.exceptions.ConnectionError:
        ctd.SSL = False
        ctd.AASA = None
        return False

    return True


def parse_aasa_for_path(ctd):
    """Parses AASA file for path, bundle id and prefix

    Sets the prefix, path and bundle id of the CTD object.
    returns true if the paths in the AASA file match the path in the CTD

    :param ctd: (obj: ClickTrackingDomain) The click tracking domain
    :return: bool, False if we can't parse the AASA file, True if the URL of the CTD is a valid path to open the app
    """
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

    return ctd.is_valid_path() # this seems like pretty poor practice... not sure how to better design this


def check_for_branch_link(ctd):
    """Check redirects of the CTD url for a branch link

    Follows the redirects of the click tracking domain using the requests lib. attempts to find a .app.link domain and
    return it

    :param ctd: (obj: ClickTrackingDomain) The click tracking domain
    :return: (str) the branch URL else returns None
    """

    # add check for SSL and AASA for domains that are erroring
    if not ctd.SSL or ctd.AASA is None:
        return None
    print(ctd.SSL, ctd.AASA)

    # ALL URLs should be valid already
    r = requests.get(ctd.get_url_text(), verify=False)

    url = urlparse(r.url)
    if 'app.link' in url.netloc:
        return url.geturl()

    if r.history:
        for x in r.history:
            url = urlparse(x.url)
            if 'app.link' in url.netloc:
                return url.geturl()
    return None


def ctd_service_driver(url):

    ctd_url = urlparse(url.strip())

    if not(ctd_url.scheme == 'https' or ctd_url.scheme == 'http'):
        raise ClickTrackingParsingError('Scheme is not http or https')

    ctd = ClickTrackingDomain(ctd_url)
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ['8.8.8.8']

    # This is to get CNAME
    try:
        answer = resolver.query(ctd.url.netloc, 'CNAME')
        ctd.cname = answer.rrset[0].target
        print(ctd.cname)
    except dns.resolver.NoAnswer:
        # no CNAME
        ctd.cname = None
        pass

    except dns.resolver.NXDOMAIN:
        raise ClickTrackingParsingError('Could not reach the domain, Please check for typo\'s')

    aasa = validate_ssl_aasa(ctd, False)

    if not aasa:
        validate_ssl_aasa(ctd, True)

    aasa = parse_aasa_for_path(ctd)
    ctd.branch_link = check_for_branch_link(ctd)


    return ctd
