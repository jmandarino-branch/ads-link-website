import collections
import json
import os
import mimetypes
from urllib import parse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper


from branchlinks import constants
from .models import Link, LinkDefault
from .ctd_service import ctd_service_driver, ClickTrackingParsingError
from .utils import  create_deeplink_feeds, process_csv, process_kv_only, process_email_link, update_links

from links.models import Template

Branch_kv_pair = collections.namedtuple('Branch_kv_pair', 'key new_key value')

# because of how fragile this could be its best to define for some kind of consistency
HTML_KEY = 'key_'
HTML_VALUE = 'value_'
HTML_NEW_KEY = 'new_key_'


@login_required(login_url=constants.LOGIN_URL)
def adlinks(request):
    link_dict = request.user.company.linkdefault.ad_link_dict  # fetch link defaults from DB
    ad_templates = request.user.company.templates.all()
    ad_link_base_url = request.user.company.linkdefault.ad_base_url

    # empty dictionaries '{}' are treated as strings
    if isinstance(link_dict, str):
        link_dict = dict()

    if ad_link_base_url:
        link_dict['base_url'] = ad_link_base_url

    if request.method == 'POST' and len(request.FILES) > 0 and request.FILES['uploaded_file']:
        file = request.FILES['uploaded_file']
        urls = None  # to hold urls to output

        # handle extra inputs
        post_dict = request.POST.dict()
        pairs = get_key_value_pairs_from_html(post_dict)

        export_to_file = bool(request.POST.get('fileExport', False))

        template_id = request.POST.get('template_name', None)  # check if a template is to be used
        if file.name.endswith('.csv'):
            path = default_storage.save(os.path.join('tmp', file.name), ContentFile(file.read()))  # store a file temporarily
            urls, outfile_name = process_csv(request, path, template_id, pairs, export_to_file)

            if outfile_name:
                response = download_file(outfile_name)
                return response


        return render(request, 'index.html', {
            'urls': urls,
            'uploaded_file_url': True,
            'user': request.user,
            'ad_templates': ad_templates,
            'link_dict_items': link_dict.items()
        })
    elif request.method == 'POST':
        post_dict = request.POST.dict()
        pairs = get_key_value_pairs_from_html(post_dict)
        template_id = request.POST.get('template_name', None)  # check if a template is to be used

        url = process_kv_only(pairs, template_id, request)

        return render(request, 'index.html', {
            'urls': [url],
            'uploaded_file_url': True,
            'user': request.user,
            'ad_templates': ad_templates,
            'link_dict_items': link_dict.items()
        })



    return render(request, 'index.html', {
        'user': request.user,
        'ad_templates': ad_templates,
        'link_dict_items': link_dict.items()

    })


@login_required(login_url=constants.LOGIN_URL)
def email_links(request):

    link_dict = request.user.company.linkdefault.email_link_dict

    # empty dictionaries '{}' are treated as strings
    if isinstance(link_dict, str):
        link_dict = dict()

    response_dict = {
        'user': request.user,
        'ORIGINAL_URL': constants.ORIGINAL_URL,
        'link_dict_items': link_dict.items(),
    }
    if request.method == 'POST':
        original_url = request.POST[constants.ORIGINAL_URL]
        # TODO: get KV pairs from page
        post_dict = request.POST.dict()
        pairs = get_key_value_pairs_from_html(post_dict)

        final_url = process_email_link(request, original_url, link_dict, pairs)

        # ad final_url to response
        response_dict['urls'] = [final_url]

    return render(request, 'email_links.html', response_dict)


@login_required(login_url=constants.LOGIN_URL)
def help_page(request):
    return render(request, 'adlink_help.html', {
        'user': request.user,
        'templates': Template.objects.filter(company=request.user.company)

    })

@login_required(login_url=constants.LOGIN_URL)
def product_feeds_help(request):
    return render(request, 'product_feeds_help.html', {
        'user': request.user,
        'templates': Template.objects.filter(company=request.user.company),
        'adlink_url': LinkDefault.objects.get(company=request.user.company).ad_base_url

    })

@login_required(login_url=constants.LOGIN_URL)
def product_feeds(request):
    link_dict = request.user.company.linkdefault.ad_link_dict  # fetch link defaults from DB
    ad_templates = request.user.company.templates.all()

    print(link_dict, type(link_dict))

    response_dict = {
        'user': request.user,
        'ad_templates': ad_templates,
        'link_dict_items': link_dict.items() if isinstance(link_dict, dict) else {}
    }

    if request.method == 'POST' and len(request.FILES) > 0 and request.FILES['uploaded_file']:
        file = request.FILES['uploaded_file']

        # handle extra inputs
        post_dict = request.POST.dict()
        pairs = get_key_value_pairs_from_html(post_dict)

        col_name = request.POST.get('replacement', None)

        if not col_name:
            response_dict['error'] = 'No Column Name Entered'

            return render(request, 'product_feeds.html', response_dict)

        template_id = request.POST.get('template_name', None)  # check if a template is to be used
        if file.name.endswith('.csv') or file.name.endswith('.tsv'):
            try:
                path = default_storage.save(os.path.join('tmp', file.name),
                                            ContentFile(file.read()))  # store a file temporarily

                outfile = create_deeplink_feeds(request, path, template_id, col_name, pairs)
                response = download_file(outfile)
                return response
            except KeyError as e:
                response_dict['error'] = e

        else:
            response_dict['error'] = 'Please use a File of type .csv or .tsv'

    return render(request, 'product_feeds.html', response_dict)


def link_updater(request):
    response_dict = {}

    if request.method == 'POST':
        # persist the branch key and secret
        branch_key = request.POST.get('branch_key')
        branch_secret = request.POST.get('branch_secret')

        response_dict['branch_key'] = branch_key
        response_dict['branch_secret'] = branch_secret

        if '' in [branch_key, branch_secret]:
            response_dict['error'] = "Please enter a Branch Key and Secret"
            response_dict['branch_key_error'] = True
            return render(request, 'link_updater.html', response_dict)

    if request.method == 'POST' and len(request.FILES) > 0 and request.FILES['uploaded_file']:
        file = request.FILES['uploaded_file']

        # handle extra inputs
        post_dict = request.POST.dict()
        kv_list = get_key_value_group_from_html(post_dict)

        try:
            update_links(file, branch_key, branch_secret, kv_list)
        except Exception as e:
            response_dict['error'] = e

    return render(request, 'link_updater.html', response_dict)

def email_debugger(request):
    response_dict = {
        'ORIGINAL_URL': constants.ORIGINAL_URL,
    }

    if request.method == 'POST':
        url = request.POST.get(constants.ORIGINAL_URL, None)

        if url and isinstance(url, str) and url != '':
            try:
                result = ctd_service_driver(url)
            except ClickTrackingParsingError as e:
                return render(request, 'email_debugger.html', {
                    'ORIGINAL_URL': constants.ORIGINAL_URL,
                    'error': e
                })
            #TODO: handle result == None
            # TODO: make pretty
            if result:
                response_dict = {
                    'aasa': result.AASA,
                    'cname': result.cname,
                    'ssl': result.SSL,
                    'bundle': result.bundle,
                    'prefix': result.prefix,
                    'paths': result.paths,
                    'ORIGINAL_URL': constants.ORIGINAL_URL,
                    'ctd_url': result.get_url_text(),
                    'cname_correct': result.cnamed_correctly(),
                    'ctd_deeplink' : result.is_valid_path(),
                    'branch_link': result.branch_link

                }


    return render(request, 'email_debugger.html', response_dict)

def get_key_value_group_from_html(dictionary):
    """Processes HTML input fields and builds branch_kv_pair tuples

    process the key values pairs. Keys are denoted by the input fields name="key_(key_name)"
    values are denoted with input fields name="value_(value_name)" and name="new_key_(key name)
    :param dictionary: (dict{ str:str }) values from request data sent by frontend
    :return: dictionary with properly named KV pairs

    :param dictionary:
    :return: list (tuples)
    """

    output = []
    for k in dictionary.keys():
        if k.startswith(HTML_KEY):
            key_name = k.split(HTML_KEY, 1)[1]  # split only once on the
            value_name = HTML_VALUE + key_name
            new_key_name = HTML_NEW_KEY + key_name
            branch_key = Branch_kv_pair(dictionary.get(k),
                                        new_key=dictionary.get(new_key_name), value=dictionary.get(value_name))
            output.append(branch_key)
    return output


def get_key_value_pairs_from_html(dictionary):
    """Process HTML input fields to find KV pairs

    process the key values pairs. Keys are denoted by the input fields name="key_(key_name)"
    values are denoted with input fields name="value_(value_name)"
    :param dictionary: (dict{ str:str }) values from request data sent by frontend
    :return: dictionary with properly named KV pairs
    """
    pairs = {}
    for k in dictionary.keys():
        if HTML_KEY in k:
            key_name = k.split(HTML_KEY, 1)[1]  # split only once on the
            value_name = HTML_VALUE + key_name
            pairs[dictionary[k]] = dictionary[value_name]
    return pairs

def download_file(outfile_name):
    chunk_size = 8192
    filename = os.path.basename(outfile_name)
    response = StreamingHttpResponse(FileWrapper(open(outfile_name, 'rb'), chunk_size),
                           content_type=mimetypes.guess_type(outfile_name)[0])
    response['Content-Length'] = os.path.getsize(outfile_name)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response