import requests
import urllib.parse
import json


def get_publisher_names():
    url = "https://sparql.fellesdatakatalog.digdir.no/"
    params = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dct: <http://purl.org/dc/terms/>
        
        SELECT DISTINCT ?publisherName ?dataset
        FROM <https://datasets.fellesdatakatalog.digdir.no>
        WHERE {
            ?dataset dct:publisher ?publisher .
          ?publisher foaf:name ?publisherName .
          ?dataset dct:identifier ?datasetId .
        }
    """
    res = requests.post(url=url, params={'query': params})
    if not res:
        print(f"no sparql response")
        return

    return json.loads(res.text)["results"]["bindings"]


def get_theme_names():
    url = "https://fellesdatakatalog.digdir.no/reference-data/eu/data-themes"
    res = requests.get(url=url)
    if not res:
        print("no theme data found")
        return None

    return json.loads(res.text)["dataThemes"]


def get_link_ids():
    url = "https://sparql.fellesdatakatalog.digdir.no/"
    params = """
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        SELECT ?uuid ?dataset
        FROM <https://datasets.fellesdatakatalog.digdir.no>
        WHERE {
          ?dataset a dcat:Dataset .
          ?record foaf:primaryTopic ?dataset .
          ?record dct:identifier ?uuid .
        } LIMIT 50
    """
    res = requests.post(url=url, params={'query': params})
    if not res:
        print(f"no sparql response")
        return

    return json.loads(res.text)["results"]["bindings"]
