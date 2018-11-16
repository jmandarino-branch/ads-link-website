import base64
import csv
import json
import os
from datetime import datetime
from urllib import parse

from branchlinks.link_templates import TEMPLATE_DICT
from branchlinks.settings import BASE_DIR

BASE_URL_COL_NAME = 'base_url'
TEMPLATE_COL_NAME = 'template_name'


def process_csv(request, file, template_name, query_params, to_file=False):
    # declare variables the c way!
    urls = []
    template_global = TEMPLATE_DICT.get(template_name, {})
    preset_values = {}
    base_url = None
    outfile = None

    if request.user and hasattr(request.user, 'company'):
        # if we have preset values these take priority
        preset_values = merge_dictionaries(query_params, request.user.company.linkdefaults.ad_link_dict)
        base_url = preset_values.get('base_url', None)

    if to_file:
        output_filename = os.path.join(BASE_DIR, 'tmp', '{}{}{}'.format(request.user.company.name.replace(' ', '-'),
                                                                        datetime.now().strftime("%Y-%m-%d"), '.csv'))
        outfile = open(output_filename, 'w')
        outfile.write('URL,URI,\n')

    with open(file) as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        for row in csv_reader:
            template = template_global

            row_base_url = base_url

            if BASE_URL_COL_NAME in row and row_base_url is None:
                row_base_url = row.get(BASE_URL_COL_NAME)
                del row[BASE_URL_COL_NAME]

            if TEMPLATE_COL_NAME in row:
                template = row.get(TEMPLATE_COL_NAME)
                if template:
                    template = TEMPLATE_DICT.get(template.upper(), template_global)
                else:
                    template = template_global
                del row[TEMPLATE_COL_NAME]

            updated_row = merge_dictionaries(preset_values, row)
            link_data = merge_dictionaries(updated_row, template)
            url = row_base_url + parse.urlencode(link_data, safe='{}')  # safe characters do not get encoded

            data = (url, row_base_url+link_data_uri(link_data))
            if to_file:
                outfile.write('{},{},\n'.format(data[0],data[1]))
            else:
                urls.append(data)
    if outfile:
        outfile.close()
        return urls, outfile.name
    return urls, None


def process_kv_only(pairs, template_name):
    base_url = pairs.get(BASE_URL_COL_NAME, None)
    if base_url is None:
        return 'ERROR: Please include base_url in your keys'
    del pairs[BASE_URL_COL_NAME]

    template = None
    if template_name:
        template = TEMPLATE_DICT.get(template_name.upper(), {})

    link_data = merge_dictionaries(pairs, template)

    return (base_url + parse.urlencode(link_data, safe='{}'),)


def merge_dictionaries(row_data, default):
    """Merge d2 into d1, where d1 has priority

    for all values of d2 merge them into d1. If a value exists in d1 and in d2 keep the value from d1

    :param d1: dictionary of values
    :param d2: dictionary of values
    :return: dictionary of unified values
    """
    if default is None:
        return row_data
    if row_data is None:
        return default

    return {**default, **row_data}

def link_data_uri(link_data):
    """Take Link Data and uri encode it

    :param link_data: Dictionary of link data
    :return:
    """
    unencoded = json.dumps(link_data)
    b64_encoded = base64.b64encode(unencoded.encode())

    # uri encode
    return parse.quote(b64_encoded)