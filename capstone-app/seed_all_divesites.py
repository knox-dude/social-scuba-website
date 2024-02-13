import os
import json
import pycountry
from sqlalchemy import insert
from app import db, app
from models import Divesite

def read_json_file(file_path):
    """Opens a JSON file of form {data: [{...}, ...]}"""

    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['data']

def get_all_divesites_data(folder_path):
    """Store all cached API data into database"""

    with app.app_context():
        db.drop_all()
        db.create_all()

    completed = set()
    countries = {str.lower(country.name) for country in pycountry.countries}
    countries_to_add = [
        'usa',
        'bolivia',
        'bonaire',
        'bosnia',
        'cocos islands',
        'cook island',
        'falkland islands',
        'iran',
        'korea',
        'micronesia',
        'moldova',
        'palestine',
        'saint martin',
        'sint maarten',
        'taiwan',
        'tanzania',
        'vietnam'
    ]
    for country in countries_to_add:
        countries.add(country)
    continents = set(["north america", "europe", "south america", "africa", "asia", "oceania"])

    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            
            # Read the JSON file and append the data to the list. Skip if empty or seen
            divesites_data = read_json_file(file_path)
            if len(divesites_data) == 0:
                continue

            data_to_add = []

            for site in divesites_data:

                # if this record has been seen already, skip it
                if site['id'] in completed:
                    continue
                completed.add(site['id'])

                # convert id to api_id, we'll give our own ids in this database
                site['api_id'] = site['id']
                del site['id']

                # convert lat/lng from strings to float
                site['lat'] = float(site['lat'])
                site['lng'] = float(site['lng'])

                # rename Location to location for consistency
                site['location'] = site['Location']
                del site['Location']

                # convert HTML escaped characters to normal characters
                site['name'] = site['name'].replace("&#039;", "'")
                site['name'] = site['name'].replace("&amp;", "&")
                site['name'] = site['name'].replace("&quot;", '"')

                # try to grab continent and country
                split_location = site['location'].split(",")

                for keyword in split_location:

                    keyword = keyword.strip()

                    if str.lower(keyword) in countries:
                        site['country'] = keyword

                    if str.lower(keyword) in continents:
                        site['continent'] = keyword
                
                data_to_add.append(site)

            # add data if we have any
            if len(data_to_add) != 0:

                with app.app_context():
                    db.session.execute(
                        insert(Divesite),
                        data_to_add
                    )
                    db.session.commit()
    return

# Specify the path to the by_country_or_region folder
folder_path = os.path.join(os.getcwd(), 'api-queries/by_country_or_region')

# Get all divesites data from JSON files in the folder
all_divesites_data = get_all_divesites_data(folder_path)