import os
from urllib import parse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from branchlinks.link_templates import TEMPLATE_DICT

from .models import Link, LinkDefaults
from .utils import process_csv, process_kv_only


# because of how fragile this could be its best to define for some kind of consistency
HTML_KEY = 'key_'
HTML_VALUE = 'value_'

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


@login_required(login_url='/login/')
def adlinks(request):
    link_dict = request.user.company.linkdefaults.ad_link_dict  # fetch link defaults from DB
    if request.method == 'POST' and len(request.FILES) > 0 and request.FILES['uploaded_file']:
        file = request.FILES['uploaded_file']
        urls = None # to hold urls to output
        template_name = request.POST.get('template_name', None)  # check if a template is to be used
        if file.name.endswith('.csv'):
            path = default_storage.save(os.path.join('tmp', file.name), ContentFile(file.read())) #  store a file temporarily
            urls = process_csv(request, path, template_name)

        return render(request, 'index.html', {
            'urls': urls,
            'uploaded_file_url': True,
            'user': request.user,
            'ad_templates': TEMPLATE_DICT.keys(),
            'link_dict_items': link_dict.items()
        })
    elif request.method == 'POST':
        post_dict = request.POST.dict()
        pairs = get_key_value_pairs_from_html(post_dict)
        template_name = request.POST.get('template_name', None)  # check if a template is to be used

        url = process_kv_only(pairs, template_name)

        return render(request, 'index.html', {
            'urls': [url],
            'uploaded_file_url': True,
            'user': request.user,
            'ad_templates': TEMPLATE_DICT.keys(),
            'link_dict_items': link_dict.items()
        })



    return render(request, 'index.html', {
        'user': request.user,
        'ad_templates': TEMPLATE_DICT.keys(),
        'link_dict_items': link_dict.items()

    })
