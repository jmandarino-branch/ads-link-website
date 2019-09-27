import base64
import csv
import json
import os
from datetime import datetime
from urllib import parse

from branchlinks.link_templates import TEMPLATE_DICT
from branchlinks.settings import BASE_DIR

from links.models import Template

BASE_URL_COL_NAME = 'base_url'
TEMPLATE_COL_NAME = 'template_name'
CONSTANT_3P_UPPER = '$3P'
CONSTANT_3p_LOWER = '$3p'


def process_csv(request, file, template_id, query_params, to_file=False):
    """

    :param request: (Django WSGI Request) The Request from the web
    :param file: (string) The name of the file to open (saved in tmp/ folder)
    :param template_id: (string) the numeric representation of a template's Id
    :param query_params: (Dict (str)) keys and values found in the Query params
    :param to_file: (Bool) a flag that if true indicates the system will force a file download on the webpage
    :return: ( List( Tuple( str URL, str URI),) str) ex. [ ('hello', 'world'),], output.txt
    """
    # declare variables the c way!
    urls = []
    if template_id:
        template_global = Template.objects.get(id=int(template_id), company=request.user.company).template_data
    else:
        template_global = None
    preset_values = {}
    base_url = None
    outfile = None

    if request.user and hasattr(request.user, 'company'):
        # if we have preset values these take priority
        # preset_values = merge_dictionaries(query_params, request.user.company.linkdefault.ad_link_dict)
        base_url = query_params.get('base_url', None)

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
                template = row.get(TEMPLATE_COL_NAME, None)
                if template:
                    template_db = Template.objects.filter(search_name=template, company=request.user.company)

                    if template_db:
                        template = template_db.first().template_data
                    else:
                        template = template_global
                else:
                    template = template_global
                del row[TEMPLATE_COL_NAME]

            updated_row = merge_dictionaries(query_params, row)
            link_data = merge_dictionaries(updated_row, template)

            if base_url is None:
                return [('ERROR: on line {}, Please include base_url in the CSV or in the Query Parameters'
                         .format(csv_reader.line_num),)],  None

            url = row_base_url + parse.urlencode(link_data, safe='{}')  # safe characters do not get encoded

            if not (CONSTANT_3P_UPPER in link_data or CONSTANT_3p_LOWER in link_data):
                return [('ERROR: on line {}, Please include $3p in your keys'.format(csv_reader.line_num),)],  None

            data = (url, row_base_url+link_data_uri(link_data))
            if to_file:
                outfile.write('{},{},\n'.format(data[0],data[1]))
            else:
                urls.append(data)
    if outfile:
        outfile.close()
        return urls, outfile.name
    return urls, None


def process_kv_only(pairs, template_id, request):
    base_url = pairs.get(BASE_URL_COL_NAME, None)
    if base_url is None:
        return 'ERROR:', 'Please include base_url in your keys'
    del pairs[BASE_URL_COL_NAME]

    base_url = base_url.lower()
    template = None
    if template_id:
        template = Template.objects.get(id=int(template_id), company=request.user.company).template_data

    link_data = merge_dictionaries(pairs, template)

    if not(CONSTANT_3P_UPPER in link_data or CONSTANT_3p_LOWER in link_data) and base_url.endswith('3p?'):
        return 'ERROR:', 'Please include $3p in your keys'

    return base_url + parse.urlencode(link_data, safe='{}'),base_url+link_data_uri(link_data)


def process_email_link(request, original_url, link_data_dict, pairs):
    base_url = request.user.company.linkdefault.email_base_url
    if not base_url:
        return 'ERROR:', 'email_base_url please contact Branch'

    # create link data
    link_data = link_data_dict.copy()
    link_data['$original_url'] = original_url
    link_data['$canonical_url'] = original_url

    link_data = merge_dictionaries(pairs, link_data)

    return base_url + parse.urlencode(link_data, safe='{}')

def merge_dictionaries(user_data_dict, default):
    """Merge user_data_dict into d1, where default has priority

    for all values of default merge them into user_data_dict. If a value exists in user_data_dict and in default
    keep the value from user_data_dict

    :param user_data_dict: dictionary of values
    :param user_data_dict: dictionary of values
    :return: dictionary of unified values
    """
    if default is None:
        return user_data_dict
    if user_data_dict is None:
        return default

    return {**default, **user_data_dict}

def link_data_uri(link_data):
    """Take Link Data and uri encode it

    :param link_data: Dictionary of link data
    :return:
    """
    unencoded = json.dumps(link_data)
    b64_encoded = base64.b64encode(unencoded.encode())

    # uri encode
    return parse.quote(b64_encoded)


def create_deeplink_feeds(request, filename, template_id, col_name, pairs):
    output_filename = os.path.join(BASE_DIR, 'tmp', '{}{}{}'.format(request.user.company.name.replace(' ', '-'),
                                                                    datetime.now().strftime("%Y-%m-%d"), '.csv'))
    template_global = {}

    base_url = request.user.company.linkdefault.ad_base_url

    if template_id:
        template_global = Template.objects.get(id=int(template_id), company=request.user.company).template_data

    query_params = merge_dictionaries(pairs, template_global)

    with open(filename) as csv_file:
        dialect = csv.Sniffer().sniff(csv_file.read(1024))
        csv_file.seek(0)
        csv_reader = csv.DictReader(csv_file, dialect=dialect)

        write_csv(output_filename, {str(x): str(x) for x in csv_reader.fieldnames}, 'w')  # write header

        for row in csv_reader:
            # apply template data to the url

            if col_name not in row:
                raise KeyError("Could not find column name: {}, please check capitalization".format(col_name))

            query_params['$original_url'] = row[col_name]  # keep the original url
            query_params['$fallback_url'] = row[col_name]  # keep original url as fallback
            query_params['$canonical_url'] = row[col_name]  # add $canonical_url for linking

            url = base_url + parse.urlencode(query_params, safe='{}')  # safe characters do not get encoded

            row[col_name] = url
            write_csv(output_filename, row.values(), 'a')  # write rows to output

    return output_filename


def write_csv(filename, row, mode):
    with open(filename, mode=mode) as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(row)