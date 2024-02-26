from google.cloud.sql.connector import Connector
from rdflib import Graph, URIRef
from rdflib.namespace import DCAT, RDF, SKOS, DCTERMS
import urllib.request
import pandas as pd
import locale
from dateutil import parser
from util import get_publisher_names, get_theme_names, get_link_ids
from theme_mapping import theme_map
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

dataset_predicate_to_column = {
    'http://purl.org/dc/terms/accessRights': 'access_rights',
    'http://purl.org/dc/terms/accrualPeriodicity': 'periodicity',
    'http://purl.org/dc/terms/description': 'description',
    'http://purl.org/dc/terms/issued': "issued",
    'http://purl.org/dc/terms/publisher': 'publisher',
    'http://purl.org/dc/terms/title': 'title',
    'http://purl.org/dc/terms/temporal': 'temporal',
    'http://www.w3.org/ns/dcat#theme': 'theme',
    'http://www.w3.org/ns/dcat#dataQuality': 'quality',
    'http://www.w3.org/ns/dcat#keyword': 'keywords'
}

distribution_predicate_to_column = {
    'http://purl.org/dc/terms/description': 'desc',
    'http://purl.org/dc/terms/format': 'format',
    'http://purl.org/dc/terms/title': 'title'
}

access_uri_to_name = {
    'http://publications.europa.eu/resource/authority/access-right/PUBLIC': 'offentlig',
    'http://publications.europa.eu/resource/authority/access-right/RESTRICTED': 'begrenset',
    'http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC': 'ikke offentlig',
    'http://publications.europa.eu/resource/authority/access-right/SENSITIVE': 'sensitiv',
    'http://publications.europa.eu/resource/authority/access-right/CONFIDENTIAL': 'konfidensiell'
}

periodicity_uri_to_name = {
    'notPlanned': 'aldri',
    'daily': 'daglig',
    'annually': 'årlig',
    'weekly': 'ukentlig',
    'quarterly': 'hvert kvartal',
    'monthly': 'månedlig',
    'hourly': 'hver time',
    'unknown': 'med ukjent frekvens',
    'irregular': 'irregulært',
    'continual': 'kontinuerlig',
    'asNeeded': 'når det trengs',
    'http://publications.europa.eu/resource/authority/frequency/ANNUAL': 'årlig',
    'http://publications.europa.eu/resource/authority/frequency/OTHER': 'med ukjent frekvens',
    'http://publications.europa.eu/resource/authority/frequency/WEEKLY': 'ukentlig',
    'http://publications.europa.eu/resource/authority/frequency/HOURLY': 'hver time',
    'http://publications.europa.eu/resource/authority/frequency/NEVER': 'aldri',
    'http://publications.europa.eu/resource/authority/frequency/MONTHLY': 'månedlig',
    'http://publications.europa.eu/resource/authority/frequency/CONT': 'kontinuerlig',
    'http://publications.europa.eu/resource/authority/frequency/DAILY': 'daglig',
    'http://publications.europa.eu/resource/authority/frequency/UNKNOWN': 'med ukjent frekvens',
    'http://publications.europa.eu/resource/authority/frequency/IRREG': 'irregulært',
    'http://publications.europa.eu/resource/authority/frequency/DECENNIAL': 'hvert tiende år',
    'http://publications.europa.eu/resource/authority/frequency/QUARTERLY': 'hvert kvartal',
    'http://publications.europa.eu/resource/authority/frequency/TRIENNIAL': 'hvert tredje år',
    'http://publications.europa.eu/resource/authority/frequency/UPDATE_CONT': 'kontinuerlig',
    'http://publications.europa.eu/resource/authority/frequency/BIWEEKLY': '2 ganger i uken',
    'http://publications.europa.eu/resource/authority/frequency/BIENNIAL': 'annethvert år'
}


def extract():
    print("Henter nyeste datasetter fra felles datakatalog.")
    urllib.request.urlretrieve("https://datasets.fellesdatakatalog.digdir.no/catalogs", "datasets.ttl")


def transform():
    print("Begynner transformeringer av datasetter.")

    datasets = []
    dataset_dict = {
        'id': [], 'title': [], 'description': [], 'publisher': [], 'quality': [],
        'theme': [], 'access_rights': [], 'issued': [], 'periodicity': [], 'keywords': [],
        'link': [], 'temporal': []
    }
    distributions_dict = {'id': [], 'dataset': [], 'title': [], 'desc': [], 'format': []}
    graph = Graph()
    graph.parse('datasets.ttl', format='ttl')
    locale.setlocale(locale.LC_TIME, "no_NO")

    publisher_names = get_publisher_names()
    dataset_links = get_link_ids()
    theme_names = get_theme_names()
    temporals = {}

    # Find all datasets in catalog
    for s, p, o in graph.triples((None, RDF.type, DCAT.Dataset)):
        datasets.append(s)

    for s, p, o in graph.triples((None, RDF.type, DCTERMS.PeriodOfTime)):
        temporals[s] = {}

    for temporal in temporals:
        for s, p, o in graph.triples((temporal, None, None)):
            if str(p) == "http://schema.org/endDate":
                dt = parser.parse(str(o))
                temporals[temporal]["stop"] = dt.strftime("%B %d, %Y")
            if str(p) == "http://schema.org/startDate":
                dt = parser.parse(str(o))
                temporals[temporal]["start"] = dt.strftime("%B %d, %Y")

    # Fill in dataset info
    for dataset in datasets:
        row = {}
        row["id"] = str(dataset)
        row["theme"] = []
        distributions = []

        # Find dataset info and distributions
        for s, p, o in graph.triples((dataset, None, None)):
            if str(p) in dataset_predicate_to_column:

                # Special case for access_rights
                if str(p) == "http://purl.org/dc/terms/accessRights":
                    if str(o) in access_uri_to_name:
                        row["access_rights"] = access_uri_to_name[str(o)]
                    else:
                        row["access_rights"] = "ukjent"

                # Special case for description
                elif str(p) == "http://purl.org/dc/terms/description":
                    if o.language == "no" or o.language == "nb" or o.language is None:
                        row["description"] = str(o)

                # Special case for title
                elif str(p) == "http://purl.org/dc/terms/title":
                    if o.language == "no" or o.language == "nb" or o.language is None:
                        row["title"] = str(o)

                # Special case for theme
                elif str(p) == "http://www.w3.org/ns/dcat#theme":
                    theme_eu = [x["label"]["no"] for x in theme_names if x["uri"] == str(o).replace("https", "http")]
                    theme_no = theme_map[str(o).replace("https", "http")] if str(o).replace("https", "http") in theme_map else None
                    if len(theme_eu) > 0:
                        row["theme"].append(theme_eu[0])
                    elif theme_no is not None:
                        row["theme"].append(theme_no)

                # Special case for periodicity
                elif str(p) == "http://purl.org/dc/terms/accrualPeriodicity":
                    if str(o) in periodicity_uri_to_name:
                        row["periodicity"] = periodicity_uri_to_name[str(o).replace("https", "http")]
                    else:
                        row["periodicity"] = "med ukjent frekvens"

                # Special case for temporal
                elif str(p) == 'http://purl.org/dc/terms/temporal':
                    temporal = temporals[o]
                    if "start" not in temporal and "stop" in temporal:
                        row["temporal"] = f"frem til {temporal['stop']}"
                    elif "stop" not in temporal and "start" in temporal:
                        row["temporal"] = f"fra {temporal['start']}"
                    elif "start" in temporal and "stop" in temporal:
                        row["temporal"] = f"fra {temporal['start']} frem til {temporal['stop']}"

                # Special case for keywords
                elif str(p) == 'http://www.w3.org/ns/dcat#keyword':
                    if o.language == "no" or o.language == "nb" or o.language is None:
                        if 'keywords' in row:
                            row['keywords'] += f", {str(o)}"
                        else:
                            row['keywords'] = str(o)

                # Ensure uniform timestamps
                elif str(p) == "http://purl.org/dc/terms/issued":
                    dt = parser.parse(str(o))
                    row["issued"] = dt.strftime("%Y-%m-%d")

                # Default case
                else:
                    row[dataset_predicate_to_column[str(p)]] = str(o)

            if str(p) == 'http://www.w3.org/ns/dcat#distribution':
                distributions.append(o)

        # Find distribution data
        for distribution in distributions:
            row_distributions = {}
            row_distributions["id"] = str(distribution)
            row_distributions["dataset"] = str(dataset)
            for s, p, o in graph.triples((distribution, None, None)):
                if str(p) in distribution_predicate_to_column:

                    # Special case for format
                    if str(p) == "http://purl.org/dc/terms/format" and len(str(o).split('/')) >= 2:
                        if "format" in row_distributions:
                            row_distributions["format"] += f",{str(o).split('/')[-1]}"
                        else:
                            row_distributions["format"] = str(o).split('/')[-1]
                    else:
                        row_distributions[distribution_predicate_to_column[str(p)]] = str(o)

            # Add distributions data
            for col in distributions_dict:
                if col in row_distributions:
                    distributions_dict[col].append(row_distributions[col])
                else:
                    distributions_dict[col].append(None)

        # Find publisher name
        publisher = [x["publisherName"]["value"] for x in publisher_names if x["dataset"]["value"] == str(dataset)]
        row["publisher"] = publisher[0] if len(publisher) > 0 else "ukjent"

        # Find dataset link
        link = [x["uuid"]["value"] for x in dataset_links if x["dataset"]["value"] == str(dataset)]
        if len(link) == 0:
            continue
        row["link"] = f"https://data.norge.no/datasets/{link[0]}"

        if "periodicity" not in row:
            row["periodicity"] = "med ukjent frekvens"

        # Process all themes into one string
        if len(row["theme"]) > 0:
            row["theme"] = f"""{"kategorien" if len(row["theme"]) <= 1 else "kategoriene"} '{"', '".join(row["theme"])}'"""
        else:
            row["theme"] = "kategorien ukjent"

        # Use nynorsk if dataset has no bokmål title
        if "title" not in row:
            for s, p, o in graph.triples((dataset, DCTERMS.title, None)):
                if o.language == "nn":
                    row["title"] = str(o)

        # Use nynorsk if dataset has no bokmål description
        if "description" not in row:
            for s, p, o in graph.triples((dataset, DCTERMS.description, None)):
                if o.language == "nn":
                    row["description"] = str(o)

        # Add dataset data
        for col in dataset_dict:
            if col in row:
                dataset_dict[col].append(row[col])
            else:
                dataset_dict[col].append(None)

    pd.set_option('display.max_columns', None)
    df_dataset = pd.DataFrame(data=dataset_dict)
    df_distributions = pd.DataFrame(data=distributions_dict)

    summaries = []
    print("Summerer datasett.")

    # Produce dataset summary
    for index, dataset in df_dataset.iterrows():
        if dataset["issued"] is not None:
            dt = parser.parse(dataset["issued"])
        else:
            dt = None
        has_quality = dataset["quality"] is not None
        has_keywords = dataset["keywords"] is not None

        if dataset["description"] is None:
            dataset["description"] = "Ingen beskrivelse av datasettet tilgjengelig."

        distributions = df_distributions.loc[df_distributions["dataset"] == dataset["id"]]
        formats = distributions[distributions.format.notnull()]["format"]
        format_set = set()
        for x in formats:
            for format in x.split(","):
                format_set.add(format)

        summary = f"""
        Dette datasettet, med navn '{dataset["title"]}' er utgitt av '{dataset["publisher"]}'.
        Datasettet har {dataset["access_rights"]} tilgang og {dataset["theme"]}.
        
        Beskrivelsen av datasettet er som følger:
        {dataset["description"]}
        
        {"Datakvaliteten til datasettet er beskrevet som følger: " + dataset["quality"] if has_quality else ""}

        Datasettet {f'ble opprettet {dt.strftime("%B %d, %Y")} og' if dt is not None else ""} oppdateres {dataset["periodicity"]}.
        Datasettet har {len(distributions.index)} distribusjoner og tilbyr data på formatene {', '.join(f for f in format_set)}.
        {f'Nøkkelordene for datasettet er: {dataset["keywords"]}.' if has_keywords else ""}
        {f"Dataen er tidsmessig begrenset {dataset['temporal']}." if dataset['temporal'] is not None else ""}
        Linken til datasettet er '{dataset["link"]}'
        """

        summaries.append(summary)

        if dataset["title"] == 'Automatiske passasjertellinger på strekninger operert av Kolumbus':
            print(summary)

    df_dataset = df_dataset.assign(summary=summaries)
    df_dataset = df_dataset[['id', 'summary']]
    print(df_dataset.head())

    return df_dataset


async def load(df):

    # GCP info
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION')
    instance_name = os.getenv('SQL_INSTANCE_ID')

    # Cloud SQL info
    database_user = os.getenv('SQL_DB_USER')
    database_password = os.getenv('SQL_PASSWORD')
    database_name = "fdk-v2"

    print(f"Begynner opplasting av data til {database_name}")

    # Save the Pandas dataframe in a PostgreSQL table.
    loop = asyncio.get_running_loop()
    async with Connector(loop=loop) as connector:
        # Create connection to Cloud SQL database
        conn: asyncpg.Connection = await connector.connect_async(
            f"{project_id}:{region}:{instance_name}",  # Cloud SQL instance connection name
            "asyncpg",
            user=f"{database_user}",
            password=f"{database_password}",
            db=f"{database_name}"
        )

        # Create the `products` table.
        await conn.execute("""CREATE TABLE IF NOT EXISTS datasets(
                                id VARCHAR(200) PRIMARY KEY,
                                summary TEXT)""")

        # Copy the dataframe to the `products` table.
        tuples = list(df.itertuples(index=False))

        await conn.copy_records_to_table('datasets', records=tuples, columns=list(df), timeout=10)
        await conn.close()

# Main run sequence
#extract()
df_datasets = transform()
#asyncio.run(load(df_datasets))
