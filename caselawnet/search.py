import json
from . import matcher
import httplib2


def get_post_data(keyword, contentsoorten=['uitspraak'], rechtsgebieden=[], instanties=[],
                  date_from=None, date_to=None,
                  maximum=1000):
    if not type(maximum) == int:
        maximum = int(maximum[0])

    post_data = {
        "Advanced": {
            "PublicatieStatus": "Ongedefinieerd"
        },
        "Contentsoorten": [{
                           "NodeType": 7,
                           "Identifier": u,
                           "level": 1
                           } for u in contentsoorten],
        "DatumPublicatie": [],
        "DatumUitspraak": [],
        "Instanties": [{
                       "NodeType": 1,
                       "Identifier": i,
                       "level": 1
                       } for i in instanties],
        "PageSize": maximum,
        "Rechtsgebieden": [{
                       "NodeType": 3,
                       "Identifier": r,
                       "level": 1
                       } for r in rechtsgebieden],
        "SearchTerms": [
            {
                "Field": "AlleVelden",
                "Term": keyword
            }
        ],
        "ShouldCountFacets": True,
        "ShouldReturnHighlights": False,
        "SortOrder": "Relevance",
        "StartRow": 0
    }
    post_data = get_dates(post_data, date_from, date_to)
    return json.dumps(post_data)


def get_dates(post_data, date_from, date_to):
    if date_from is not None or date_to is not None:
        post_data['Advanced'] = {'UitspraakdatumRange': {}}
    if date_from is not None:
        date_from = transform_date(date_from)
        post_data['Advanced']['UitspraakdatumRange']['From'] = date_from
    if date_to is not None:
        date_from = transform_date(date_to)
        post_data['Advanced']['UitspraakdatumRange']['To'] = date_from
    return post_data

def transform_date(date):
    if type(date) == list:
        date = date[0]
    date = '-'.join(reversed(date.split('-')))
    return date


def get_query_result(keyword, **args):
    post_data = get_post_data(keyword, **args)
    print(post_data)
    url =  'https://uitspraken.rechtspraak.nl/api/zoek'
    # TODO: SSL certificate is unknown by httplib2
    http = httplib2.Http(disable_ssl_certificate_validation=True)
    headers = {'Content-Type': 'application/json',
               'Accept': 'application/json'}
    response, content = http.request(url, 'POST', headers=headers,
                                     body=post_data)
    result = json.loads(content.decode('utf-8'))
    return result


def search(keyword, **args):
    result = get_query_result(keyword, **args)
    nodes = [result_to_node(res) for res in result['Results']]
    return nodes


def result_to_node(result):
    node = {}
    node['id'] = result['DeeplinkUrl']
    node['ecli'] = result['TitelEmphasis']
    node['creator'] = 'Hoge Raad'  # TODO
    node['title'] = result.get('Titel', node['id'])
    node['abstract'] = result.get('Tekstfragment', '')
    node['date'] = result['Publicatiedatum']
    node['subject'] = result['Rechtsgebieden'][0]

    matched_articles = matcher.get_articles(node['abstract'])
    node['articles'] = [art + ' ' + book for (art, book), cnt in
                        matched_articles.items()]
    node['year'] = int(node['date'].split('-')[-1])
    node['count_version'] = len(result['Vindplaatsen'])
    node['count_annotation'] = len([c for c in result['Vindplaatsen'] if
                                    c['VindplaatsAnnotator'] != ''])
    # New:
    node['procedure'] = result['Proceduresoorten']
    return node

