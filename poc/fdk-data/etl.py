from google.cloud.sql.connector import Connector
from rdflib import Graph, URIRef
from rdflib.namespace import DCAT, RDF
import urllib.request
import pandas as pd
import locale
from dateutil import parser
from util import get_publisher_names, get_theme_names
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
    dataset_dict = {'id': [], 'title': [], 'description': [], 'publisher': [], 'quality': [], 'theme': [], 'access_rights': [], 'issued': [], 'periodicity': [], 'keywords': []}
    distributions_dict = {'id': [], 'dataset': [], 'title': [], 'desc': [], 'format': []}
    graph = Graph()
    graph.parse('datasets.ttl', format='ttl')

    publisher_names = get_publisher_names()
    theme_names = get_theme_names()

    # Find all datasets in catalog
    for s, p, o in graph.triples((None, RDF.type, DCAT.Dataset)):
        datasets.append(s)

    # Fill in dataset info
    for dataset in datasets:
        row = {}
        row["id"] = str(dataset)
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

                # Special case for theme
                elif str(p) == "http://www.w3.org/ns/dcat#theme":
                    theme = [x["label"]["no"] for x in theme_names if x["uri"] == str(o).replace("https", "http")]
                    row["theme"] = theme[0] if len(theme) > 0 else "ukjent"

                # Special case for periodicity
                elif str(p) == "http://purl.org/dc/terms/accrualPeriodicity":
                    if str(o) in periodicity_uri_to_name:
                        row["periodicity"] = periodicity_uri_to_name[str(o).replace("https", "http")]
                    else:
                        row["periodicity"] = "med ukjent frekvens"

                # Special case for keywords
                elif str(p) == 'http://www.w3.org/ns/dcat#keyword':
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

        if "periodicity" not in row:
            row["periodicity"] = "med ukjent frekvens"

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
    locale.setlocale(locale.LC_TIME, "no_NO")
    print("Summerer datasett.")

    # Produce dataset summary
    for index, dataset in df_dataset.iterrows():
        if dataset["issued"] is not None:
            dt = parser.parse(dataset["issued"])
        else:
            dt = None
        has_quality = dataset["quality"] is not None
        has_keywords = dataset["keywords"] is not None

        distributions = df_distributions.loc[df_distributions["dataset"] == dataset["id"]]
        formats = distributions[distributions.format.notnull()]["format"]
        format_set = set()
        for x in formats:
            for format in x.split(","):
                format_set.add(format)

        summary = f"""
        Dette datasettet, med navn '{dataset["title"]}' er publisert av {dataset["publisher"]}.
        Datasettet har {dataset["access_rights"]} tilgang og kategorien '{dataset["theme"]}'.
        
        Beskrivelsen av datasettet er som følger:
        {dataset["description"]}
        
        {"Datakvaliteten til datasettet er beskrevet som følger: " + dataset["quality"] if has_quality else ""}

        Datasettet {f'ble opprettet {dt.strftime("%B %d, %Y")} og' if dt is not None else ""} oppdateres {dataset["periodicity"]}.
        Datasettet har {len(distributions.index)} distribusjoner og tilbyr data på formatene {', '.join(f for f in format_set)}.
        {f'Søkeordene for datasettet er: {dataset["keywords"]}.' if has_keywords else ""}
        """

        summaries.append(summary)

    df_dataset = df_dataset.assign(summary=summaries)

    return df_dataset, df_distributions


async def load(df):

    # GCP info
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION')
    instance_name = os.getenv('SQL_INSTANCE_ID')

    # Cloud SQL info
    database_user = os.getenv('SQL_DB_USER')
    database_password = os.getenv('SQL_PASSWORD')
    database_name = "fdk-v1"

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
                                title VARCHAR(200),
                                description TEXT,
                                publisher VARCHAR(100),
                                quality TEXT,
                                theme VARCHAR(100),
                                access_rights VARCHAR(20),
                                issued VARCHAR(10),
                                periodicity VARCHAR(30),
                                keywords TEXT,
                                summary TEXT)""")

        # Copy the dataframe to the `products` table.
        tuples = list(df.itertuples(index=False))

        await conn.copy_records_to_table('datasets', records=tuples, columns=list(df), timeout=10)
        await conn.close()

# Main run sequence
#extract()
#df_datasets, df_distributions = transform()
#asyncio.run(load(df_datasets))
