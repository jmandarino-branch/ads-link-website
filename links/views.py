import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from branchlinks.link_templates import TEMPLATE_DICT

from .models import Link, LinkDefaults
from .utils import process_csv


@login_required(login_url='/login/')
def adlinks(request):
    link_dict = request.user.company.linkdefaults.ad_link_dict
    if request.method == 'POST' and request.FILES['uploaded_file']:
        file = request.FILES['uploaded_file']
        urls = None
        template_name = request.POST.get('template_name', None)
        if file.name.endswith('.csv'):
            path = default_storage.save(os.path.join('tmp', file.name), ContentFile(file.read()))
            urls = process_csv(request, path, template_name)

        return render(request, 'index.html', {
            'urls': urls,
            'uploaded_file_url': True,
            'user': request.user,
            'ad_templates': TEMPLATE_DICT.keys(),
            'link_dict_items': link_dict.items()
        })
    elif request.method == 'POST':
        pass
    return render(request, 'index.html', {
        'user': request.user,
        'ad_templates': TEMPLATE_DICT.keys(),
        'link_dict_items': link_dict.items()

    })
