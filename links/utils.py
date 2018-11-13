import csv
from urllib import parse

from branchlinks.link_templates import TEMPLATE_DICT

BASE_URL_COL_NAME = 'base_url'
TEMPLATE_COL_NAME = 'template_name'


def process_csv(request, file, template_name):
    urls = []
    template_global = TEMPLATE_DICT.get(template_name, {})
    if request.user and hasattr(request.user, 'company'):
        base_url = request.user.company.linkdefaults.ad_link_dict.get('base_url', None)

    with open(file) as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        for row in csv_reader:
            template = template_global

            if BASE_URL_COL_NAME in row:
                base_url = row.get(BASE_URL_COL_NAME, base_url)
                del row[BASE_URL_COL_NAME]

            if TEMPLATE_COL_NAME in row:
                template = row.get(TEMPLATE_COL_NAME)
                if template:
                    template = TEMPLATE_DICT.get(template.upper(), template_global)
                else:
                    template = template_global
                del row[TEMPLATE_COL_NAME]

            link_data = merge_dictionaries(row, template)
            url = base_url + parse.urlencode(link_data, safe='{}:')  # safe characters do not get encoded
            urls.append(url)

    return urls


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