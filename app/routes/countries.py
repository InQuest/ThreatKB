from flask import json, Response
from app import app, auto
import pycountry


@app.route('/ThreatKB/countries', methods=['GET'])
@auto.doc()
def get_all_countries():
    """Return all countries in ThreatKB
    Return: list of countries dictionary"""
    countries = pycountry.countries
    return Response(json.dumps([{
            "countryCode": country.alpha_2,
            "countryName": country.name.encode('utf-8').strip()
        } for country in countries]), mimetype="application/json")
