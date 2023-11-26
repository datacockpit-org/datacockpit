import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from sql_metadata import Parser
from datacockpit.usage.sql_parser.subquery_extractor import extract
from collections import defaultdict
import pandas as pd
import logging


def get_metadata_dict(sql_query: str):
    """
    Notes:
    This function accounts for aliases but discards them
    This function accounts for nested table names
    This function assigns HAVING to group_by
    Will raise error for "SELECT test, id FROM foo, bar"
    Refer to the test function for expected I/O
    """
    parser = Parser(sql_query)
    tables = parser.tables
    columns_with_metadata = parser.columns_dict

    if len(tables) < 1:
        raise Exception("Dataset not found")
    if not columns_with_metadata:
        logging.warning("Columns not found")
        return

    metadata = defaultdict(list)
    for type_of_query, attributes in columns_with_metadata.items():
        for attribute in attributes:
            if len(tables) > 1:
                resolved_table = None
                for table_name in tables:
                    if attribute.startswith(table_name):
                        resolved_table = table_name
                        break
                if resolved_table:
                    table = resolved_table
                else:
                    logging.warning("Error in table resolution")
                    return
            else:
                table = tables[0]
            if not attribute.startswith(table):
                attribute = f"{table}.{attribute}"
            metadata[table].append((attribute, type_of_query))
    return dict(metadata)

def jsonify_dict(sql_dict):
    # Convert dict to list of JSONs for easier conversion to pandas
    if not sql_dict:
        return []
    res = []
    for table, attributes in sql_dict.items():
        inner_json = {}
        if not table:  # derived attributes are not associated with any tables
            table = "QUERY"
        inner_json["dataset"] = table
        inner_json["attributes"] = attributes
        res.append(inner_json)
    return res


def _get_metadata_table(sql_query):
    metadata_dict = get_metadata_dict(sql_query)
    if not metadata_dict:
        return None
    metadata_json = jsonify_dict(metadata_dict)
    df = pd.DataFrame.from_dict(metadata_json).explode("attributes")
    df['attribute'], df['query_type'] = zip(*df.attributes)
    return df.drop("attributes", axis=1)


def get_metadata_table(
    sql_query: str,
    extract_subqueries: bool = True):
    """Get Pandas dataframe from the SQL query

    :param sql_query: SQL query to parse
    :param extract_subqueries: Whether to extract subqueries
    :return: df with columns ["dataset", "attribute", "query_type"]
    :rtype: pd.DataFrame
    """
    if not extract_subqueries:
        return _get_metadata_table(sql_query)
    subqueries = extract(query=sql_query)
    if not subqueries:
        return None
    df = _get_metadata_table(subqueries[0])
    for subquery in subqueries[1:]:
        df = pd.concat([df,  _get_metadata_table(subquery)], axis=0)
    return df
