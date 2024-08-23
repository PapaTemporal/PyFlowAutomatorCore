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

import re
from jsonpath_ng.ext import parse


def json_parse(json_obj: dict, expression: str):
    try:
        return parse(expression).find(json_obj)
    except Exception as e:
        raise type(e)(f"'json_parse' exception: {e}") from e
    

def re_findall(text: str, pattern: str):
    try:
        return re.findall(pattern, text)
    except Exception as e:
        raise type(e)(f"'re_findall' exception: {e}") from e
    

def re_search(text: str, pattern: str):
    try:
        return re.search(pattern, text)
    except Exception as e:
        raise type(e)(f"'re_search' exception: {e}") from e
