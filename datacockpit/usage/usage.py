from datacockpit.usage.sql_parser import sql_parser
import pandas as pd
import sys
import os
from datetime import datetime
from random import randint

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


class Usage:
    def __init__(self,
                 input_path: str, attr_metadata_output_path: str = None,
                 aggr_output_path: str = None, dataset_usage_output_path: str = None,
                 period_type: str = "daily") -> None:
        """ Initializes Usage object with path to CSV containing usage logs

        :param input_path: CSV "query_id | database | query | timestamp | user | application"
        :type input_path: str
        :param attr_metadata_output_path: CSV "database | dataset | attribute | query_type | \
            query_id | timestamp | user | application"; Won't dump if unspecified
        :type attr_metadata_output_path: str
        :param aggr_output_path: CSV "database | dataset | attribute | query_type | period_type | \
            period | count"; Won't dump if unspecified
        :type aggr_output_path: str
        :param dataset_usage_output_path: CSV "database | dataset | query_count | unique_user_count | \
            dataset_usage_frequency_score | no_of_unique_users_score | overall_dataset_usage_score"; \
            Won't dump if unspecified
        :type dataset_usage_output_path: str
        :param period_type: Aggregating period. Supported: ["daily"]
        :type period_type: str

        """

        self.input_path                 = input_path
        self.attr_metadata_output_path  = attr_metadata_output_path
        self.aggr_output_path           = aggr_output_path
        self.dataset_usage_output_path  = dataset_usage_output_path
        SUPPORTED_PERIOD_TYPES          = ["daily", None]
        if period_type not in SUPPORTED_PERIOD_TYPES:
            raise NotImplementedError(
                f"Period type <<{period_type}>> not supported")
        self.period_type = period_type


    def get_attribute_usage(self, df):
        if self.period_type == "daily":
            df["period_type"] = "daily"
            df["period"] = df['timestamp'].apply(
                lambda ts: datetime.fromtimestamp(ts).strftime("%Y-%m-%d"))
            result_df = df.groupby(["database", "dataset", "attribute", "query_type", "period"]).\
                agg(count_queries=('query_id', 'nunique'),
                    last_used=('timestamp', 'max'),
                    unique_user_count=('user', 'nunique'))
        else:
            df["period_type"] = "unspecified"
            df["period"] = "unspecified"
            result_df = df.groupby(["database", "dataset", "attribute", "query_type", "period"]).\
                agg(count_queries=('query_id', 'nunique'),
                    last_used=('timestamp', 'max'),
                    unique_user_count=('user', 'nunique'))

        # Calculate the last-used for overall period if unspecified
        if self.period_type != "daily":
            result_df["last_used"] = df.groupby(["database", "dataset", "attribute", "query_type"]).\
                agg(last_used=('timestamp', 'max'))

        return result_df


    def generate_metadata(self, multiplier: float = None) -> \
    tuple([pd.DataFrame, pd.DataFrame, pd.DataFrame]):
        """ Generates attribute and dataset level usage stats and overall dataset usage score
        Currently relies on semi-random logic that users can specify weightage to compute scores
        """
        input_df = pd.read_csv(self.input_path)
        input_df = input_df.reset_index()
        metadata_df = pd.DataFrame()
        for _, row in input_df.iterrows():
            try:
                query_metadata = sql_parser.get_metadata_table(
                    sql_query=row['query'])
            except:
                continue
            if query_metadata is None:
                continue
            query_metadata.insert(0, 'database', row['database'])
            query_metadata['query_id']      = row['query_id']
            query_metadata['timestamp']     = row['timestamp']
            query_metadata['user']          = row['user']
            query_metadata['application']   = row['application']
            metadata_df = pd.concat([metadata_df, query_metadata], axis=0)
        aggr_df = self.get_attribute_usage(df=metadata_df)
        aggr_df.reset_index(inplace=True)
        dataset_usage_df = metadata_df.groupby(['database', 'dataset']).agg(
            query_count=('query_id', 'nunique'),
            unique_user_count=('user', 'nunique')
            )
        if not multiplier:
            multiplier = randint(5, 15)
        dataset_usage_df["dataset_usage_frequency_score"] = dataset_usage_df.apply(
            lambda row: min((row.query_count * multiplier), 100), axis=1)
        dataset_usage_df["no_of_unique_users_score"] = dataset_usage_df.apply(
            lambda row: min((row.unique_user_count * multiplier), 100), axis=1)
        dataset_usage_df['overall_dataset_usage_score'] = dataset_usage_df.apply(
            lambda row: max(row.dataset_usage_frequency_score, row.no_of_unique_users_score),
            axis=1
        )
        dataset_usage_df.reset_index(inplace=True)

        if self.attr_metadata_output_path:
            metadata_df.to_csv(self.attr_metadata_output_path)
        if self.aggr_output_path:
            aggr_df.to_csv(self.aggr_output_path)
        if self.dataset_usage_output_path:
            dataset_usage_df.to_csv(self.dataset_usage_output_path)

        return (metadata_df, aggr_df, dataset_usage_df)
