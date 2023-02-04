"""
Helper functions that help check whether a query is well formed.
"""


from collections import deque
from sqlglot import transpile, parse_one, exp


def get_bracket_close_index(s: str, i: int) -> int:
    """ Get index of corresponding bracket close
    Returns -1 if unavailable else index
    """
    if s[i] != '(':
        return -1
    d = deque()
    for k in range(i, len(s)):
        # Pop a starting bracket
        # for every closing bracket
        if s[k] == ')':
            d.popleft()
        # Push all starting brackets
        elif s[k] == '(':
            d.append(s[i])
        # If deque becomes empty
        if not d:
            return k
    return -1

def is_wellformed_query(sql_query: str) -> bool:
    """
    Returns True if sql_query is a well-formed SQL query
    "abc" is invalid but "SELECT * FROM A" is valid
    The way it works is it checks if it is a legit SQL query
    and if a table can be inferred from it.
    This is to avoid cases like "(*)" which can be interpreted to be
    a valid subquery.
    """
    try:
        # to check if valid syntax
        transpile(sql_query)
        # to check if table found
        for table in parse_one(sql_query).find_all(exp.Table):
            if table.name is not None:
                return True
        return False
    except:
        return False

