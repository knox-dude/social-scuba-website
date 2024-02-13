# The Social Scuba Website

[Check it out now!](https://social-scuba.org)

## Recreating the project:

## Initial Requirements
1. Python 3.9
2. Postgres
3. A Google Maps API Key (free to signup and use)
4. A World Scuba Diving Sites API Key (One time payment of $5)
5. (Optional) A domain name and AWS instance to launch the site

## Retrieving Data

First, sign up for an account here: [World Scuba Diving Sites API](https://rapidapi.com/jojokcreator/api/world-scuba-diving-sites-api)

**Important: You will need to pay $5 for the API data.** Downloading all the data at once exceeds the free tier limits.

git clone this repository.

create secret.py in api-queries (touch api-queries/secret.py)

put in api-queries/secret.py:

- API_KEY: "your api key that you got from the website"
- API_HOST: "host name of the website, will be on the website"

### After Retrieving Data

cd capstone-app

Create python 3.9 venv in capstone-app. Use this command: 

python3.9 -m venv venv (if don't have python3.9, look up how to do it, something about deadsnakes ppa is what I did since I use ubuntu)

pip install -r requirements.txt

createdb social-scuba-app

sign up for a google maps api key (it's free)

touch secret.py

put in secret.py:

- SECRET_KEY="just put in a bunch of random letters and numbers and characters"
- GOOGLE_API_KEY="make a google api key to be able to load maps"

run models.py (python models.py)

run seed_all_divesites.py (python seed_all_divesites.py)

Now you should be able to run the flask app! I'm not putting a tutorial here for launching the instance as a website. If you're interested in that, [here's the guide I made on google drive.](https://docs.google.com/document/d/1NHXK4xisnSpGo7s2KSeBK9rWBTs9ChshRdTjIdYYjng/edit?usp=sharing)

Any questions? Add [Andrew Knox on linkedIn](https://linkedin.com/in/andrewknox99) and specifically mention the social-scuba app so I don't accidentally delete the connect request.
