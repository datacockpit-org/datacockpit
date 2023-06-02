from datacockpit import DataCockpit
from sqlalchemy import create_engine



"""
1. Install sqlite on your machine.

2. Create a database on your local machine.
sqlite3 /Users/your_username/mydatabase.db

3. Populate the database with some tables.
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT
);

INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com');
INSERT INTO users (name, email) VALUES ('Jane Smith', 'jane@example.com');
INSERT INTO users (name) VALUES ('Bob Johnson');

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    price REAL,
    quantity INTEGER
);

INSERT INTO products (name, price, quantity) VALUES ('Product 1', 9.99, 10);
INSERT INTO products (name, price, quantity) VALUES ('Product 2', 19.99, 5);
INSERT INTO products (name, quantity) VALUES ('Product 3', NULL);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER
);

INSERT INTO orders (user_id, product_id, quantity) VALUES (1, 1, 2);
INSERT INTO orders (user_id, product_id, quantity) VALUES (2, 1, NULL);

4. Finally, run this code after making changes to the database_path.
"""
# Setup database connection with SQL engine and log-file CSV
if __name__ == "__main__":
    database_path = '/Users/your_username/mydatabase.db'
    engine = create_engine(f'sqlite:///{database_path}')

    dcp_obj = DataCockpit(engine=engine,
            path_to_logs="assets/data/query_logs.csv")

    # Compute and persist quality & usage metrics
    dcp_obj.compute_quality(levels=None, metrics=None)
    dcp_obj.compute_usage(levels=None, metrics=None)

"""
5. Finally, check out the following tables generated in your database:
attribute_metrics
record_metrics
dcp_metadata
dcp_aggr
dcp_dataset_usage
"""