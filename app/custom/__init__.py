# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

# place any custom functions here
# a custom function is a convenience function that does multiple steps in one,
# otherwise you would create all this logic with nodes in the UI
# here is an example:
#
# def get_films_with_luke_skywalker():
#   swapi_url = "https://swapi.dev/api/people/"
#   resp = requests.get(swapi_url)
#   resp.raise_for_status()
#   resp_json = resp.json()
#   results = resp_json["results"]
#   for person in results:
#       if "Luke" in person["name"]:
#           return person["films"]
#
# NOTE: if this file gets too large, you can put them into a separate file or
# python package and import them.

from jsonpath_ng.ext import parse
from app.utils import JSONExtractionError


def extract_json(json_obj: dict, expression: str):
    try:
        if not isinstance(json_obj, dict):
            raise ValueError("json_object must be a dictionary")

        values = [res.value for res in parse(expression).find(json_obj)]
        if len(values) == 1:
            return values[0]
        return values
    except Exception as e:
        raise JSONExtractionError(f"Unable to extract JSON: {e}")
