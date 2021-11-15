from typing import List, Optional
from terminusdb_client import WOQLQuery, WOQLClient
from terminusdb_client.woqlschema.woql_schema import (
    DocumentTemplate,
    EnumTemplate,
    WOQLSchema,
    LexicalKey,
)

import pandas as pd
from tqdm import tqdm
import tempfile

schema = WOQLSchema()

class Netflix(DocumentTemplate):
    _schema = schema
    title: str
    type_of: "Content_Type"
    director: Optional[str]
    cast: Optional[str]
    country: Optional[str]
    release_year: int
    rating: "Rating"
    duration: str
    listed_in: str
    description: str
    date_added: Optional[str]

class Content_Type(EnumTemplate):
    _schema = schema
    TV_Show = "TV Show"
    Movie = "Movie"

class Rating(EnumTemplate):
    _schema = schema
    TV_MA = "TV-MA"
    R = ()
    PG_13 = "PG-13"
    TV_14 = "TV-14"
    TV_PG = "TV-PG"
    NR = ()
    TV_G = "TV-G"
    TV_Y = "TV-Y"
    TV_Y7 = "TV-Y7"
    TY = ()
    TY_7 = "TY-7"
    PG = ()
    G = ()
    NC_17 = "NC-17"
    TV_Y7_FV = "TV-Y7-FV"
    UR = ()

def insert_data(client, url):
    df = pd.read_csv(url, chunksize=1000)
    for chunk in tqdm(df, desc='Transfering data'):
        csv = tempfile.NamedTemporaryFile()
        chunk.to_csv(csv)
        netflix_content = read_data(csv.name)
        client.insert_document(netflix_content, commit_msg="Adding all Netflix content")
        
def read_data(csv):
    records = []
    df = pd.read_csv(csv)
    for index, row in df.iterrows():

        type_of = row['type'].replace(" ", "_")
        rating = "NR" if pd.isna(row['rating']) else row['rating'].replace("-", "_")

        records.append(Netflix(title=row['title'], type_of=Content_Type[type_of], director=str(row['director']), cast=str(row['cast']), country=str(row['country']), release_year=row['release_year'], rating=Rating[rating], duration=row['duration'], listed_in=row['listed_in'], description=row['description'], date_added=str(row['date_added'])))

    return records

def query_documents(client):
    documents = client.get_all_documents()

    # documents comes back as a iterable that can be convert into a list
    print("\nAll documents\n")
    print(list(documents))

    matches = client.query_document({"@type"  : "Netflix",
                                 "type_of": "Movie",
                                 "release_year": "2020"})

    # matches comes back as a iterable that can be convert into a list
    print("\nDocuments matches\n")
    print(list(matches))

    # If you want to get a specific number of records, just add count=number when calling both functions:
    documents = client.get_all_documents(count=5)
    matches = client.query_document({"@type"  : "Netflix",
                                    "type_of": "Movie",
                                    "release_year": "2020"}, count=5)

def branches(client):
    #You can create a new branch by calling the create_branch method
    client.create_branch("some_branch", empty=False)

    # When empty is set to False, a new branch will be created, 
    # containing the schema and data inserted into the database previously. 
    # If set to True, an empty branch will be created.
    client.create_branch("some_branch1", empty=True)

    # You can delete a branch by calling the delete and passing the name of the branch as parameter.
    client.delete_branch("some_branch")

    # List all branches
    branches = client.get_all_branches()

    print(branches)

if __name__ == "__main__":
    db_id = "Netflix"
    url = "netflix.csv"

    team = "mariog"
    client = WOQLClient("https://cloud.terminusdb.com/mariog/")
    
    try:
        client.connect(team=team, use_token=True)
        client.create_database(db_id, label = "Netflix Graph", description = "Create a graph with Netflix data")
    except Exception:
        client.connect(db=db_id, team=team, use_token=True)

    schema.commit(client, commit_msg = "Adding Netflix Schema")
    
    insert_data(client, url)
    results = client.get_all_documents(count=10)
    print("\nRESULTS\n", list(results))

    print("\nQUERYING DOCUMENTS\n")
    query_documents(client)

    print("\nBranches\n")
    branches(client)

    # Get the whole commit history:
    commit_history = client.get_commit_history()
    print("\nCOMMIT HISTORY\n",commit_history)