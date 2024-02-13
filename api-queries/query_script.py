import json
import re
import os
import requests
from secret import API_KEY, API_HOST


# get absolute path names for data files
script_directory = os.path.dirname(os.path.abspath(__file__))

file_path_sample_terms = os.path.join(script_directory, "sample_queries.txt")
queries_completed_file=os.path.join(script_directory, 'query_requests_completed.txt')
queries_not_completed_file=os.path.join(script_directory, 'query_requests_not_completed.txt')

def create_query_files()->None:
    """Creates two files:
    - query_requests_completed.txt
    - query_requests_not_completed.txt

    These files track which query terms have been performed and received data from the API."""

    query_terms = set()

    if not os.path.exists(queries_not_completed_file):

        # get list of all possible queries, taken from API website
        with open(file_path_sample_terms, "r") as f:
            # Matches terms in curly quotes followed by commas
            pattern = re.compile(r'“([^“”]+)”\s*,')

            for line in f:
                matches = pattern.findall(line)
                # strip unwanted characters
                for idx, match in enumerate(matches):
                    matches[idx]=match.strip("“”,")
                
                query_terms.update(matches)
        
        # create and fill file with queries that have not been performed
        with open(queries_not_completed_file, "x") as f:
            query_terms=sorted(list(query_terms))
            for term in query_terms:
                f.write(f"{term}\n")
    
    # create file with completed queries. Nothing inside yet.
    if not os.path.exists(queries_completed_file):
        with open(queries_completed_file, "x") as f:
            pass

def get_query_strings()->list:
    """Returns a backwards sorted list of query strings that have not yet been performed."""

    # get not performed queries
    query_strings=set()
    with open(queries_not_completed_file, "r") as f:
        for line in f:
            query_strings.add(line.strip("\n"))

    # get performed queries
    completed_queries = set()
    with open(queries_completed_file, "r") as f:
        for line in f:
            completed_queries.add(line.strip("\n"))

    # set difference them
    query_strings=query_strings-completed_queries

    query_strings=sorted(list(query_strings))
    query_strings.reverse()
    return query_strings

def perform_request():
    """Requests api until limit is reached for the day. Adds completed query json to data files"""

    query_strings=get_query_strings()
    url = "https://world-scuba-diving-sites-api.p.rapidapi.com/api/divesite"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST
    }
    completed_queries=[]

    # request API until limit is reached
    while True:
        if len(query_strings) == 0:
            break
        if len(query_strings) == 1:
            print()
        query_country = query_strings.pop()
        querystring={"country":query_country}

        response = requests.get(url, headers=headers, params=querystring)

        if response.status_code != 200:
            break
        
        completed_queries.append(query_country)
        datafilepath = os.path.join(script_directory, f"by_country_or_region/{query_country}.json")

        # export query result to a file
        with open(datafilepath, "w") as json_file:
            json.dump(response.json(), json_file, indent=2)

    # write completed results to the query_requests_completed file
    with open(queries_completed_file, "a") as f:
        for q in completed_queries:
            f.write(q + "\n")

create_query_files()
perform_request()