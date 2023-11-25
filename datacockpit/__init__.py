from datacockpit.usage import Usage
from datacockpit.quality import Quality
import sqlalchemy
import pandas as pd
from typing import List
import logging
class DataCockpit:
    """
    Class exposed to users to interact with the package. Exposes modules in the package via
    public methods
    """

    def __init__(self, engine: sqlalchemy.engine, path_to_logs: str):
        """ Initialize DataCockpit object

        :param sqlalchemy.engine engine: SQLAlchemy engine object to connect to the database
        :param str path_to_logs: Path to CSV where the query logs are saved containing columns:
                "query_id | database | query | timestamp | user | application"

        :return: None
        """
        self.engine         = engine
        # self.conn           = engine.raw_connection()
        self.conn           = engine.connect()
        self.path_to_logs   = path_to_logs
        logging.basicConfig(level=logging.ERROR)


    def _write_df_to_table(self, df: pd.DataFrame, table: str, if_exists: str):
        """ Helper function to write pandas df to table using conn
        """
        df.to_sql(table, self.engine, if_exists=if_exists, index=False)


    def compute_usage(self, levels:List[str] = None, metrics:List[str] = None,
        if_exists: str="append") -> None:
        """ Compute usage statistics of the databases and attributes in the datalake

        :param List[str] levels: The level of aggregation, To Be Implemented.
        :param List[str] metrics: The kind of metrics, To Be Implemented.
        :param str if_exists: Strategy to follow if usage metrics tables already exist
                You can set if_exists to "fail", or "replace". Defaults to "append".
        :return: None, it writes the results to the metrics tables using the DB engine
        """
        # TODO: Use level and metrics for aggregations; currently doing for all together
        usage_obj = Usage(input_path=self.path_to_logs)
        metadata_df, aggr_df, dataset_usage_df = usage_obj.generate_metadata()
        self._write_df_to_table(metadata_df,        "dcp_metadata", if_exists)
        self._write_df_to_table(aggr_df,            "dcp_aggr", if_exists)
        self._write_df_to_table(dataset_usage_df,   "dcp_dataset_usage", if_exists)


    def get_usage(self, levels:List[str] = None, metrics:List[str] = None)-> \
    tuple([pd.DataFrame, pd.DataFrame, pd.DataFrame]):
        """ Return usage statistics of the databases and attributes in the datalake

        :param List[str] levels: The levels of aggregation, To Be Implemented.
        :param List[str] metrics: The kind of metrics, To Be Implemented.

        :return: a tuple containing (metadata_df, aggr_df, dataset_usage_df)
        metadata_df: queries parsed to extract tokens and their usages
        aggr_df: aggregated usage statistics per requirements
        dataset_usage_df: dataset level aggregates
        """
        # TODO: Use level and metrics for aggregations; currently doing for all together
        usage_obj = Usage(input_path=self.path_to_logs)
        metadata_df, aggr_df, dataset_usage_df = usage_obj.generate_metadata()
        return metadata_df, aggr_df, dataset_usage_df


    def compute_quality(self,levels = None, metrics = None, log_to_csv:bool = False) -> None:
        """Compute quality metrics for the tables in the sqlalchemy connection

        :param bool log_to_csv: If True, writes the attribute and record level
                                metric tables to csv files in the current directory
        """
        db_name = self.engine.url.database
        quality_obj = Quality(self.conn)
        quality_obj.calculate_metrics(db_name, log_to_csv=log_to_csv)

    def get_quality(self) -> tuple([pd.DataFrame, pd.DataFrame]):
        """Return attribute and record metric tables as pd dataframes
        """

        quality_obj = Quality(self.conn)
        attribute_metric_table, record_metric_table = quality_obj.get_metric_tables()

        return attribute_metric_table, record_metric_table


