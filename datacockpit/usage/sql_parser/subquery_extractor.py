"""
Given a query, returns a list of subqueries.
If none, returns a list containing just the query.
"""
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from typing import List
from datacockpit.usage.sql_parser.sql_validator import is_wellformed_query, get_bracket_close_index

def _extract(query):
    if not is_wellformed_query(query):
        return ([], False)
    queries = []
    i = 0
    cur_query = ""
    while i < len(query):
        c = query[i]
        cur_query = cur_query + c
        if c == '(':
            j = get_bracket_close_index(query, i)
            subq = query[i+1: j]  # to keep the brackets out
            extracted = _extract(subq)
            if extracted[1]:  # i.e. subquery found
                sub_query = extracted[0]
                cur_query = cur_query[:-1] # to remove the starting brace
                cur_query += " NULL "
                i += len(subq) + 1
                queries.extend(sub_query)
        i += 1

    queries.append(cur_query)
    return (queries, True)

def extract(query: str) -> List[str]:
    """ Returns a list of all (sub)queries that can be extracted from
    the given query.
    """
    return _extract(query)[0]
