import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render

from branchlinks.link_templates import TEMPLATE_DICT

from .models import Link, LinkDefaults
from .utils import process_csv


def index(request):
    """View function for home page of site."""


    context = {
        'num_books': 12,
        'num_instances': 12,
        'num_instances_available': 23,
        'num_authors': 44,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


def simple_upload(request):
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
            'ad_templates': TEMPLATE_DICT.keys()
        })
    return render(request, 'index.html', {
        'user': request.user,
        'ad_templates': TEMPLATE_DICT.keys()
    })
