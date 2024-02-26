# FDK LLM
FDK LLM er en proof-of-concept 'Large Language Model' (LLM) som bygger på 
metadata fra [data.norge](https://data.norge.no) og tillater kontekstuelle
fritekstsøk for å forenkle prosessen med å finne datasett lastet opp på
data.norge.

Løsningen kan testes fritt på [våre hjemmesider](https://samferdselsdata.no/orakel).


## Teknologier
FDK-LLM kjører på Google Cloud Platform (GCP) og benytter seg av Google sine
tilbydde tjenester. LLM-en vi benytter oss av er [Vertex AI](https://cloud.google.com/vertex-ai). 
Vi forholder oss utelukkende til bruk av context når vi benytter Vertex og
gjør dermed ingen form for fine-tuning av modellen. Dette sparer oss for masse
tid og kostnader assosiert med modell-trening.

I tillegg bruker vi [LangChain](https://python.langchain.com/docs/get_started/introduction),
som rammeverk for å opprette prompt-templates og interagere med Vertex. 

Datagrunnlaget for LLM-modellen ligger i en PostgreSQL instanse som kjører på
Cloud SQL i GCP. Helt kritisk for applikasjonen er postgres-utvidelsen [pgvector](https://github.com/pgvector/pgvector),
som lar oss gjøre vektoriserte likhetssøk mot datagrunnlaget vårt.


## Teknisk arkitektur
Arkitekturern til FDK-LLM er under kontinuerlig utvikling kan endre seg raskt.
Hovedsaklig kan et søk via orakelkatalogen deles opp i 2 steg. Disse er som følger:
- Dokumentgjennfinning
- LLM filtrering og validering

Disse to stegene kan gjennomføres ende-til-ende på omlag 5 sekunder.
Tidsmessig er det spørringen mot Vertex som tar størsteparten av tiden, mens
spørringen mot postgres tar en brøkdel av et sekund.

### Datatilberedninger
Metadataen for alle datasett i data.norge.no er offentlig tilgjengelig
i TTL-format. Denne dataen må behandles og lastes opp i en postgres-database
slik at vi kan bruke `pgvector` til å gjøre søk. 

Pgvector bruker text-embeddings til å sammenlikne datasettene. Dette betyr at
vi må ha datasettene på et rent tekstlig format. For å oppnå dette lager vi
en tekstlig oppsummering av hvert enkelt dataset som vi deretter
vektoriserer ved hjelp av Vertex. Nedenfor finner du et eksempel av hvordan
en slik oppsummering ser ut.

```
Dette datasettet, med navn 'Automatiske passasjertellinger på strekninger operert av Kolumbus' er utgitt av 'Entur as'.
Datasettet har begrenset tilgang og kategoriene 'Persontransport', 'Trafikk og transport', 'Transport'.

Beskrivelsen av datasettet er som følger:
Dataprodukt med automatiske passasjertellinger for alle busser operert av Kolumbus. 
Kolumbus har ansvaret for det offentlige tilbudet av buss, bybane, båt og ferge i Rogaland fylke.
Dataproduktet er basert på tellinger av av- og påstigninger på ett stopp på en holdeplass for en buss/bane på en rute.

Datasettet ble opprettet juni 16, 2023 og oppdateres daglig.
Datasettet har 1 distribusjoner og tilbyr data på formatet csv.
Nøkkelordene for datasettet er: buss, passasjerer, apc, rogaland, kollektivtransport, kolumbus.
Dataen er tidsmessig begrenset fra april 30, 2021.
```



### Dokumentgjennfinning
I første steget av prosessen finner vi potensielt relevante dataset ut ifra
søket. Vi bruker Text Embedding i Vertex til å vektorisere søket, og kjører
et likhetssøk mot vektorene i databasen.

```postgresql
WITH vector_matches AS (
     SELECT id, 
            1 - (embedding <=> $1) AS similarity
     FROM dataset_embeddings
     WHERE 1 - (embedding <=> $1) > $2
     ORDER BY similarity DESC
     LIMIT $3
 )
 SELECT id, summary 
 FROM datasets
 WHERE id IN (SELECT id FROM vector_matches)
```

I tillegg til vektoren av søksteksten bruker vi to ekstra variabler for å
kontrollere likhetsterskel og maks antall returnerte datasett. Antallet
datasett returnert i dette steget har stor innvirkning i oppfattet
nøyaktighet på brukersiden. Vi vil gjerne ha så mange datasett som mulig, 
men for mange kan gjøre neste steg en del tregere. I tillegg er det en
hard grense på hvor mange vi kan ta siden Vertex har en grense på størrelse
av context. Vi har landet på maks 7 datasett i vårt use-case, men dette kan
endre seg i fremtiden.


### LLM filtrering og validering
Siste steg av prosessen bruker Vertex sin LLM til å filtrere bort
irrelevante dataset fra forrige steg og besvare forespørselen fra brukeren.
Her bruker vi LangChain til å opprette en prompt som tar inn 
tekstlige oppsummeringer av datasettene gir instruksjoner om hvordan
forespørselen skal behandles. En typisk spørring mot Vertex vil se ut
som beskrevet under:


```text
You will be given a detailed description of different datasets in norwegian
enclosed in triple backticks (```) and a question enclosed in
double backticks(``).
Select the datasets that are most relevant to answer the question, with a maximum of 5 datasets.
If there are more more than 5 relevant datasets, try to vary them in your answer.
Create a markdown link on the format [DATASET_TITLE](DATA_NORGE_LINK) for each relevant dataset.
Using those dataset descriptions, answer the following
question in as much detail as possible.
You should only use the information in the descriptions.
Your answer should include the title links and why each dataset match the question posed by the user.
If no datasets are given, explain that the data may not exist.
Double check to make sure the markdown link format is correct and that the dataset title is the link text.
Give the answer in Norwegian.

Description:
```{text}```


Question:
``{user_query}``
```

I vår erfaring er modellen vi bruker i Vertex meget partisk for 
Markdown og det kan være vanskelig å få noe strukturert svar i et annet
format. Mye tid har gått med på å få LLMen til å svare 
konsistent på samme format, men likevel kan svaret struktureres annerledes
fra tid til annen. 


### Forbedringer
For å øke nøyaktigheten i søket har vi forsøkt å bruke LLMen til å generere
relevante ekstra nøkkelord som så brukes til å utvide søket i PostgreSQL.
Resultatet av dette har vært bedre resultater på mindre detaljerte
forespørsler på bekostning av cirka 1 sekund ekstra behandlingstid.


## Kostnader
Siden kostnad er en stor . Vertex AI er en serverless tjeneste fra Google,
som betyr at vi kun betaler for hver spørring vi gjør mot den. I praksis
vil kostnadene for Vertex dermed være relativt liten, men kan i motsetning
bli dyrere ved store antall spørringer.

For perioden 6.januar - 26.februar var kostnadene for dette prosjektet
distribuert følgende:

![Kostnadsdestribusjon](https://i.imgur.com/N11bJkU.png)

Fra distribusjonen ser vi at hovedkostnadene gikk til Cloud SQL, som kjører
vår postgres database. Denne er en dedikert server, som skaper løpende
kostnader. `pgvector` har ingen virkning på kostnadene og det er kun
serverkostnadene assosiert med postgres som vises her. 
I motsetning har Vertex ikke skapt store kostnader for vår del,
men denne ville fortsatt vært litt høyere i et mer populæert produksjonsmiljø.
