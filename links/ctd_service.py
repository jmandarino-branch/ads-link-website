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
    return it. This will also validate links that are generically wrapped even if they are not properly integrated with
    branch

    :param ctd: (obj: ClickTrackingDomain) The click tracking domain
    :return: (str) the branch URL else returns None
    """

    # URLs can fail above checks but still be valid here because they have a branch link

    try:
        r = requests.get(ctd.get_url_text(), verify=False)
    except:
        # not great practice but any failure is a reason to quit
        return None

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


"""
Test links:
http://l.marketing01.email-allstate.com/rts/go2.aspx?h=450583&tp=i-H43-A2-NQq-1HzQUs-25-eZ7el-3E-1HzQUq-1999E9&x=049608%7cP_CUSTMKTG_STFS_ONLINERESEARCHSERVICES_P%7c20190905%7c
https://ablink.mail.grailed.com/
https://woof.chewy.com
web only: https://dl.zola.com/external/5cbf7190071eff4e251abe7a/aHR0cHM6Ly93d3cuem9sYS5jb20vd2VkZGluZy1wbGFubmluZy9wYXBlcj91dG1fbWVkaXVtPWVtYWlsJnV0bV9zb3VyY2U9dHJpZ2dlcmVkJnV0bV9jYW1wYWlnbj11bmlmaWVkd2VsY29tZV9wYXBlciZieGlkPTVjMWE5YzMxY2RiN2VjNmMzNDE0NTk1YSYkd2ViX29ubHk9dHJ1ZSZub2FwcD10cnVl/5c1a9c31cdb7ec6c3414595aD44fd2904
deeplink with Path validation: https://ablink.mail.grailed.com/uni/wf/click?upn=tT6YHeYyNeCFDKc-2Bw-2B9Pz9zV14sAf9fdqUwJf7oPQJbnBQPsW41VsUhcT3xbinNEyiVsQdJpm8dCc1Nk5cFU6ncB80zMMfXkZtroRDIc70A-3D_1C8fdgrh-2Fw7P0-2F2Ol3PSBqFV5Bid60CsJ2gOrSVYfMzoVcV5oNKNwu3KpjB9JL1ttr0HdAfd7jmxveNMBflj2xyMQOTuLfIewRKmfDau0y4BsCwwHn-2FnbjqKKLgfXcxLUeSTjlso5ABMq-2F8VR-2Fl8MggMBhP0GU1ZZutvuDlz5Q41CQVXlwqCC-2BpjRkl6N35DQiNQwrnSxLLDzdHTQmJ5gdM7aEabFtjpUHCiEVgK2sAeCCW1j62BPg1e8Zz8seeFp7oCw4pvQRN-2B7yh1PAp-2BA4DXosk-2BShz2eGbFUGGyrOcr6wFJqah07NNOA56T1aeXS9uTo7W8neJ8kHAk3fX-2FSDFxXxSJx5-2BsX8-2FOCntrBvYz6giOWS4TJ6-2FrqWZExrOmm8Gb18Bo0fkmOXoSPiYssB3M8evajEPVPfKjf4KsZDxozRPfZXcLlug9i7svPD12QsHVWZx1l-2F8uhy8qFvYXhei9Yvq1z77vpT7PbTQljB5gHzdZybe7ZxSJfVCgiWwg
"""