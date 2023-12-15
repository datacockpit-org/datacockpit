# DataCockpit

[![PyPI license](https://img.shields.io/pypi/l/ansicolortags.svg)](https://pypi.python.org/pypi/datacockpit/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/datacockpit)

DataCockpit is a Python toolkit that leverages the data, usage logs, and associated meta-data
within a data lake and provisions two kinds of auxiliary information:

1. quality – the validity and appropriateness of data required to perform certain analytic tasks.
2. usage – the historical utilization characteristics of data across multiple users.

<br/>

## Architecture
<img src="assets/images/architecture.png" alt="DataCockpit architecture diagram"/>

<br/>

## Install
DataCockpit is written in Python 3. Please ensure you have a Python 3 environment already installed.

Installing DataCockpit is as simple as making microwave popcorn! Just `pip install datacockpit` and then sit back and let it do the work while you put your feet up.

<br/>

## How to Use
```python
from datacockpit import DataCockpit

# Setup database connection with SQL engine and log-file CSV
dcp_obj = DataCockpit(engine=your_sqlalchemy_engine,
        logs_path="your/logs/path.csv")

# Compute and persist quality & usage metrics
dcp_obj.compute_quality(levels=None, metrics=None)
dcp_obj.compute_usage(levels=None, metrics=None)
```

- First, we initialize a [SQLAlchemy](https://www.sqlalchemy.org/) `engine` that is used to connect to the database.
- Then we create an object, `dcp_obj`, of the `DataCockpit` class, by passing the `engine` and `logs_path` as arguments. `logs_path` points to the location where the historical usage logs (SQL queries and metadata such as the user who ran them and the timestamp) are saved in a CSV file.
- The next two lines call methods to compute and persist quality and usage with parameters to support different `levels` (e.g., ['attribute', 'record', 'all']) and `metrics` (e.g., ['correctness', 'completeness', 'all']).
- The `compute_` commands persist the computed metrics to database tables.
- You can retrieve the computed metrics for use in downstream applications through the below `get_` commands.

```python
# Retrieve computed information for use in downstream applications
quality_info = dcp_obj.get_quality()
usage_info = dcp_obj.get_usage()
```

Depending on your data and query patterns, the `get_quality()` and `get_usage()` functions will return the following quality and usage information.

<br/>

## Data Quality Information

<br/>

### Attribute metrics table (attribute_metrics):

- `Completeness` is the percentage of non-missing values for an attribute.
- `Correctness` is the percentage of correct values for an attribute based on pre-defined constraints.
- `Objectivity` is the amount of distortion in the data distribution.
- `Uniqueness` is the percentage of unique values for an attribute.

<img src="assets/images/quality-attribute-metrics.png" alt="attribute metrics">

<br/>

### Record metrics table (record_metrics):

- `Completeness` is the percentage of non-missing values in each dataset record.
- `Correctness` is the percentage of correct values in each dataset record.
- `Uniqueness` is the percentage of unique values in each dataset record.

<img src="assets/images/quality-record-metrics.png" alt="record metrics">

<br/>

## Data Usage Information

The usage metrics are fairly self explanatory. The SQL queries are parsed to get the Metadata Table that shows usage statistics for every attribute in the datasets (analogous to tables). The Aggregate Table and the Dataset Usage Tables are rolled up from the Metadata Table. Other analyses such as timeseries analyses are shown in the Jupyter notebooks in the `assets/notebooks` directory. It runs on a sample usage file available in `assets/data/query_logs.csv`.

<br/>

### Metadata table (dcp_metadata):

<img src="assets/images/usage-metadata-table.png" alt="usage metadata table">

<br/>

### Aggregate table (dcp_aggr):

<img src="assets/images/usage-aggregate-table.png" alt="usage aggregate table">

<br/>

### Data usage (dcp_dataset_usage)

<img src="assets/images/usage-dataset-table.png" alt="usage dataset table">


<br/>

## Build

DataCockpit can be installed as a Python package and imported in your own awesome applications!

- DataCockpit is written in Python 3. Please ensure you have a Python 3 environment already installed.
- Clone this repository (review branch) and enter (`cd`) into it.
- Create a new virtual environment, `virtualenv --python=python3 venv`
- Activate it using, `source venv/bin/activate` (MacOSX/Linux) or `venv\Scripts\activate.bat` (Windows)
- Install dependencies, `python -m pip install -r requirements.txt`
- \<make your changes\>
- Bump up the version in setup.py and create a Python distributable, `python setup.py sdist`
- This will create a new file inside **datacockpit-*.*.*.tar.gz** inside the `dist` directory.
- Install the above file in your Python environment using, `python -m pip install <PATH-TO-datacockpit-*.*.*.tar.gz>`
- Verify by opening your Python console and importing it:
```python
>>> from datacockpit import DataCockpit
```
- Enjoy, DataCockpit is now available for use as a Python package!

<br/>

## Analysis

Look at [assets](https://github.com/datacockpit-org/datacockpit/tree/review/assets/notebooks) for
examples of how to use the metrics obtained, such as visualizing the temporal trends in data
or finding the most critical attributes.

<br/>


## Credits
DataCockpit was created by Arpit Narechania, Fan Du, Atanu R. Sinha, Ryan A. Rossi, Jane Hoffswell, Shunan Guo, Eunyee Koh, Surya Chakraborty, Shivam Agarwal, Shamkant B. Navathe, and Alex Endert.


<br/>


## License
The software is available under the [MIT License](https://github.com/datacockpit-org/datacockpit/blob/master/LICENSE).


<br/>


## Contact
If you have any questions, feel free to [open an issue](https://github.com/datacockpit-org/datacockpit/issues/new/choose) or contact [Arpit Narechania](http://narechania.com), [Surya Chakraborty](suryashekharc.github.io) (chakraborty [at] gatech.edu), or Shivam Agarwal (s.agarwal [at] gatech.edu).
