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
from .utils import process_csv, process_kv_only

from links.models import Template


# because of how fragile this could be its best to define for some kind of consistency
HTML_KEY = 'key_'
HTML_VALUE = 'value_'


@login_required(login_url=constants.LOGIN_URL)
def adlinks(request):
    link_dict = request.user.company.linkdefault.ad_link_dict  # fetch link defaults from DB
    ad_templates = request.user.company.templates.all()

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

@login_required(login_url=constants.LOGIN_URL)
def help_page(request):
    return render(request, 'adlink_help.html', {
        'user': request.user,
        'templates': Template.objects.filter(company=request.user.company)

    })


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