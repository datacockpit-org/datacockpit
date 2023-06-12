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
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email) VALUES
    ('John Doe', 'john@example.com'),
    ('Jane Smith', NULL),
    ('Mike Johnson', 'mike@example.com'),
    ('Alice Brown', 'alice@example.com'),
    ('Bob Johnson', 'bob@example.com'),
    ('', 'invalid_email'),
    (NULL, 'invalid_name@example.com'),
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com');

Added some more values to show freshness
INSERT INTO users (name, email, created_at)
VALUES
    ('Sarah Johnson', 'sarah@example.com', '2022-03-15 10:30:00'),
    ('Michael Brown', 'michael@example.com', '2022-06-02 15:45:00'),
    ('Emily Davis', 'emily@example.com', '2022-09-18 08:15:00'),
    ('David Wilson', 'david@example.com', '2022-12-05 12:00:00'),
    ('Jennifer Smith', 'jennifer@example.com', '2023-02-27 09:20:00');


CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    price REAL,
    quantity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO products (name, price, quantity) VALUES
    ('Product A', 10.99, 50),
    ('Product B', -5.99, 100),
    ('Product C', 19.99, NULL),
    ('Product D', 14.99, 75),
    ('Product A', 9.99, 25),
    ('', 12.99, 50),
    (NULL, 8.99, 10),
    ('Product B', 5.99, 20);


CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO orders (user_id, product_id, quantity) VALUES
    (1, 1, 5),
    (2, 1, -10),
    (1, 3, 2),
    (3, 4, 3),
    (4, 5, 1),
    (NULL, 6, 5),
    (7, NULL, 10),
    (1, 1, 5),
    (2, 2, 2),
    (3, 1, 3);

4. Finally, run this code after making changes to the database_path.
"""
# Setup database connection with SQL engine and log-file CSV
if __name__ == "__main__":
    database_path = '/Users/suryashekharchakraborty/mydatabase.db'
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