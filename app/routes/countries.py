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
        "countryCode2": country.alpha_2,
        "countryCode3": country.alpha_3,
        "countryName": str(country.name).strip()
    } for country in countries]), mimetype="application/json")


def get_country(country):
    if country:
        if len(country) == 2:
            full_country = pycountry.countries.get(alpha_2=country)
        elif len(country) == 3:
            full_country = pycountry.countries.get(alpha_3=country)
        else:
            full_country = pycountry.countries.get(name=country)
        return {"countryCode2": full_country.alpha_2,
                "countryCode3": full_country.alpha_3,
                "countryName": str(full_country.name).strip()}
    else:
        return None
