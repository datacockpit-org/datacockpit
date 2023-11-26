import sqlalchemy
from sqlalchemy import text

import sqlite3
import csv
from tabulate import tabulate
import datetime
from typing import List
import logging
import pandas as pd

class Quality:
	def __init__(self, conn: sqlalchemy.engine.Connection):
		self.conn   = conn
		self.metrics = ["completeness", "correctness"]


	def calculate_metrics(self, db_name, constraints: List[List] = None,
		log_to_csv: bool=False):

		print("Please wait. This might take a few minutes")

		self.conn.execute(text("DROP TABLE IF EXISTS attribute_metrics"))
		self.conn.execute(text("DROP TABLE IF EXISTS record_metrics"))

		#Create metric tables
		self.conn.execute(text("CREATE TABLE IF NOT EXISTS attribute_metrics" + \
			"(db_name text, table_name text, attribute_name text, timestamp" + \
			" timestamp, uniqueness float, completeness float, correctness float, overall float)"))
		self.conn.execute(text("CREATE TABLE IF NOT EXISTS record_metrics" + \
			"(db_name text, table_name text, primary_key text, timestamp" + \
			" timestamp, uniqueness float, completeness float, correctness float, overall float)"))

		# Get a list of tables in the db
		# cursor = self.conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
		cursor = self.conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_type='BASE TABLE' AND table_schema='public';"
))
		tables = [x[0] for x in cursor.fetchall()]

		# Remove metric tables from the list of tables to analyze
		tables_to_ignore = ["attribute_metrics", "record_metrics", "dcp_metadata", "dcp_aggr", "dcp_dataset_usage"]
		for table_to_ignore in tables_to_ignore:
			try:
				tables.remove(table_to_ignore)
			except:
				pass

		current_date_time = datetime.datetime.now()
		timestamp = str(current_date_time)[:19]  # Get ts string with sql parseable format

		self.generate_attribute_metrics(db_name, constraints, tables, timestamp)
		self.generate_record_metrics(db_name, constraints, tables, timestamp)

		if log_to_csv:
			self._log_to_csv()

		self.conn.commit()

	def generate_record_metrics(self, db_name, constraints, tables, timestamp):
		# Create an entry for each record of every table in db, in the record metrics table
		for table_name in tables:
			cursor = self.conn.execute("SELECT tn.name FROM pragma_table_info('" + \
				table_name + "') as tn WHERE tn.pk = 1;")
			primary_key = [x[0] for x in cursor.fetchall()][0]
			self.conn.execute("INSERT INTO record_metrics SELECT '"+ db_name + \
				"' AS db_name, '" + table_name + "' AS table_name, " + primary_key + \
				" AS primary_key, '" + timestamp + \
				"' AS timestamp, 0, 0, 0, 0  from " + table_name)
		for table_name in tables:
			# Get table attribute names
			query = "SELECT * FROM " + table_name + " LIMIT 1"
			cursor = self.conn.execute(query)
			attribute_names = [description[0] for description in cursor.description]

			null_values = []
			for _ in range(len(attribute_names)):
				null_values += [["''", "'None'", "'NULL'"]] # TODO: Account for cols
						# with no null condition

			primary_key = "serial_no"
			cursor = self.conn.execute("SELECT tn.name FROM pragma_table_info('" + table_name + "') as tn WHERE tn.pk = 1;")
			primary_key = [x[0] for x in cursor.fetchall()][0]

			self.generate_record_completeness(
				null_values, db_name, table_name, primary_key, timestamp
			)

			if not constraints:
				# Default example constraint: Ensure that attribute values are not -3
				constraints = []
				for _ in range(len(attribute_names)):
					constraints += [['IS NOT "-3"']]
			self.generate_record_correctness(constraints, db_name, table_name, primary_key, timestamp)
			self.generate_record_redundancy(db_name, table_name, primary_key, timestamp)
			self.generate_record_overall()

	def generate_attribute_metrics(self, db_name, constraints, tables, timestamp):
		for table_name in tables:
			query = "SELECT * FROM " + table_name + " LIMIT 1;"
			cursor = self.conn.execute(text(query))
			print(cursor.description)

			# Get attribute names from the table
			attribute_names = [description[0] for description in cursor.description]

					# Create an entry for each attribute in the metrics table
			for attribute_name in attribute_names:
				query = "INSERT INTO attribute_metrics (db_name, table_name, " + \
							"attribute_name, timestamp, completeness, correctness, uniqueness)" + \
							" VALUES( '" + db_name + "', '" + table_name + "', '" + attribute_name + \
							"', '" + timestamp +  "', 0, 0, 0);"
				self.conn.execute(query)

			null_values = []

			for _ in range(len(attribute_names)):
				null_values += [["''", "'None'", "'NULL'"]]  # TODO: Account for cols
						# with no null condition

			# Call attribute completeness function
			self.generate_attribute_completeness(null_values, db_name, table_name, timestamp)

			if not constraints:
				# Default example constraint: Ensure that attribute values are not -3
				constraints = []
				for _ in range(len(attribute_names)):
					constraints += [['IS NOT "0"']]

			# Call attribute correctness function
			self.generate_attribute_correctness(constraints, db_name, table_name, timestamp)

			# Call attribute redundancy function
			self.generate_attribute_redundancy(db_name, table_name, timestamp)

			self.generate_attribute_overall()

	def _log_to_csv(self):
		csvWriter = csv.writer(open("quality_attribute.csv", "w"))

				# Write headers to the csv
		cursor = self.conn.execute("SELECT * FROM  attribute_metrics  LIMIT 1")
		headers = [description[0] for description in cursor.description]
		csvWriter.writerow(headers)

		cursor = self.conn.execute("SELECT * FROM attribute_metrics")
		rows = cursor.fetchall()
		for row in rows:
			csvWriter.writerow(row)

		csvWriter = csv.writer(open("quality_record.csv", "w"))

				#Write headers to the csv
		cursor = self.conn.execute("SELECT * FROM  record_metrics  LIMIT 1")
		headers = [description[0] for description in cursor.description]
		csvWriter.writerow(headers)

		cursor = self.conn.execute("SELECT * FROM record_metrics")
		rows = cursor.fetchall()
		for row in rows:
			csvWriter.writerow(row)


		#################################################################################
		#################################################################################

	#Attribute completeness Query
    #null_values is a 2d list containing a list of acceptable null values for each attribute.
    # The list for an attribute may be empty

	def generate_attribute_completeness(self, null_values, db_name, table_name, timestamp):
		query = "SELECT * FROM " + table_name + " LIMIT 1"

		cursor = self.conn.execute(query)

		attribute_names = [description[0] for description in cursor.description]

		attribute_null_values = {}
		for i in range(len(attribute_names)):
			attribute_null_values[attribute_names[i]] = null_values[i]

		logging.debug(attribute_names)


		attribute_completeness_query = "SELECT "  #Query to get the completeness of each attribute
		for attribute in attribute_names:
			attribute_null = attribute_null_values[attribute]
			#attribute_completeness_query += "CAST((SELECT COUNT(*) FROM journals WHERE " + attribute + " != '') AS FLOAT) * 100 / CAST(COUNT(*) AS FLOAT) AS '" + attribute + "', "
			if(len(attribute_null) > 0):
				attribute_completeness_query += "CAST((SELECT COUNT(*) FROM " + table_name + " WHERE "
				for null_value in attribute_null:
					attribute_completeness_query += attribute + " != " + null_value + " AND "

				attribute_completeness_query = attribute_completeness_query[:-4]
				attribute_completeness_query += ") AS FLOAT) * 100 / CAST(COUNT(*) AS FLOAT) AS '" + attribute + "', "

		attribute_completeness_query = attribute_completeness_query[:-2]
		attribute_completeness_query += " FROM " + table_name

		logging.debug(attribute_completeness_query)

        #Execute the query and fetch results into a variable
		cursor = self.conn.execute(attribute_completeness_query)
		attributes = [description[0] for description in cursor.description]
		completeness_values = cursor.fetchall()
        # print(tabulate(completeness_values, headers=names, tablefmt='orgtbl'))

        #Add completeness column to the quality metrics table, if does not exist. Adding done in the function to avoid adding null values for attributes during creation of table
		try:
			self.conn.execute("ALTER TABLE attribute_metrics ADD COLUMN completeness;")
		except sqlite3.OperationalError:
			# print("column already exists, do nothing")
			pass

        #Update the completeness value for each attribute in the tables
		for i in range(len(attribute_names)):
			query = "UPDATE attribute_metrics SET completeness = " + str(completeness_values[0][i]) + " WHERE db_name = '" + db_name + "' AND table_name = '" + table_name + "' AND attribute_name = '" + attributes[i] + "' AND timestamp = '" + timestamp + "';"
			self.conn.execute(query)

		cursor = self.conn.execute("SELECT * FROM attribute_metrics")

        # print(tabulate(cursor.fetchall(), headers=['db_name', 'table_name', 'attribute_name', 'timestamp', 'completeness'], tablefmt='orgtbl'))


	def generate_attribute_correctness(self, constraints, db_name, table_name, timestamp):
		query = "SELECT * FROM " + table_name + " LIMIT 1"

		cursor = self.conn.execute(query)

		names = [description[0] for description in cursor.description]

		attribute_constraint = {}
		for i in range(len(names)):
			attribute_constraint[names[i]] = constraints[i]

		attribute_correctness_query = "SELECT "

		for attribute in names:
			attribute_constraints = attribute_constraint[attribute]
			if (len(attribute_constraint) > 0):
				attribute_correctness_query += "CAST(100 * CAST(SUM(CASE "
				for constraint in attribute_constraints:
					attribute_correctness_query += "WHEN " + attribute + " " + constraint + " THEN 1 "
				attribute_correctness_query += "ELSE 0 END) AS FLOAT) / CAST((SELECT COUNT(*) FROM " + table_name + " ) AS FLOAT) AS FLOAT) AS '" + attribute + "', "

		attribute_correctness_query = attribute_correctness_query[:-2]
		attribute_correctness_query += " FROM " + table_name

		cursor = self.conn.execute(attribute_correctness_query)
		attributes = [description[0] for description in cursor.description]
		correctness_values = cursor.fetchall()

		try:
			self.conn.execute("ALTER TABLE attribute_metrics ADD COLUMN correctness;")
		except sqlite3.OperationalError:
			# print("column already exists, do nothing")
			pass

		for i in range(len(names)):
			query = "UPDATE attribute_metrics SET correctness = " + str(correctness_values[0][i]) + " WHERE db_name = '" + db_name + "' AND table_name = '" + table_name + "' AND attribute_name = '" + attributes[i] + "' AND timestamp = '" + timestamp + "';"
			self.conn.execute(query)

		cursor = self.conn.execute("SELECT * FROM attribute_metrics")

        # print(tabulate(cursor.fetchall(), headers=['db_name', 'table_name', 'attribute_name', 'timestamp', 'completeness', 'correctness'], tablefmt='orgtbl'))

	def generate_attribute_redundancy(self, db_name, table_name, timestamp):
		query = "SELECT * FROM " + table_name + " LIMIT 1"

		cursor = self.conn.execute(query)

		names = [description[0] for description in cursor.description]

		attribute_redundancy_query = "SELECT "

		for attribute in names:
			attribute_redundancy_query += "( COUNT(DISTINCT " + attribute + ")) * 100 /(CAST(COUNT(*) AS FLOAT)) AS " + attribute + ", "

		attribute_redundancy_query = attribute_redundancy_query[:-2]
		attribute_redundancy_query += " FROM " + table_name

		# print(attribute_redundancy_query)

		cursor = self.conn.execute(attribute_redundancy_query)
		attributes = [description[0] for description in cursor.description]
		redundancy_values = cursor.fetchall()
		# print(tabulate(redundancy_values, headers=names, tablefmt='orgtbl'))


		try:
			self.conn.execute("ALTER TABLE attribute_metrics ADD COLUMN uniqueness;")
		except sqlite3.OperationalError:
			# print("column already exists, do nothing")
			pass

		for i in range(len(names)):
			query = "UPDATE attribute_metrics SET uniqueness = " + str(redundancy_values[0][i]) + " WHERE db_name = '" + db_name + "' AND table_name = '" + table_name + "' AND attribute_name = '" + attributes[i] + "' AND timestamp = '" + timestamp + "';"
			# print(query)
			self.conn.execute(query)

		cursor = self.conn.execute("SELECT * FROM attribute_metrics")

		headers = [description[0] for description in cursor.description]

		# print(tabulate(cursor.fetchall(), headers=headers, tablefmt='orgtbl'))


	def generate_attribute_overall(self):
		try:
			self.conn.execute("ALTER TABLE attribute_metrics ADD COLUMN overall;")
		except sqlite3.OperationalError:
			# print("column already exists, do nothing")
			pass

		attribute_overall_query = "UPDATE attribute_metrics SET overall = ("

		for metric in self.metrics:
			attribute_overall_query += metric + " + "

		attribute_overall_query = attribute_overall_query[:-2] + ") / " + str(len(self.metrics))

		self.conn.execute(attribute_overall_query)

	def generate_record_completeness(self, null_values, db_name, table_name, primary_key, timestamp):
		query = "SELECT * FROM " + table_name + " LIMIT 1"

		cursor = self.conn.execute(query)

		names = [description[0] for description in cursor.description]

		attribute_null_values = {}
		for i in range(len(names)):
			attribute_null_values[names[i]] = null_values[i]

		record_completeness_query = "SELECT '"+ db_name + "' AS db_name, '" + table_name + "' AS table_name, " + primary_key +" AS primary_key, '" + timestamp + "' AS timestamp, (CAST("

		for attribute in names:
			attribute_null = attribute_null_values[attribute]
			if(len(attribute_null) > 0):
				record_completeness_query += "(CASE "
				for null_value in attribute_null:
					record_completeness_query += "WHEN " + attribute + " IS " + null_value + " THEN 0 "
				record_completeness_query += "ELSE 1 END) + "

		record_completeness_query = record_completeness_query[:-2]
		record_completeness_query += "AS FLOAT) * 100 / " + str(len(names)) + ") AS 'completeness' FROM " + table_name
		record_completeness_query = "CREATE VIEW record_completeness AS " + record_completeness_query

		self.conn.execute(record_completeness_query)

		try:
			self.conn.execute("ALTER TABLE record_metrics ADD COLUMN completeness;")
		except sqlite3.OperationalError:
			# print("column already exists, do nothing")
			pass

		self.conn.execute("UPDATE record_metrics SET completeness = ( SELECT record_completeness.completeness FROM record_completeness WHERE record_completeness.primary_key = record_metrics.primary_key AND record_completeness.db_name = record_metrics.db_name AND record_completeness.table_name = record_metrics.table_name AND record_completeness.timestamp = record_metrics.timestamp) WHERE primary_key IN (SELECT primary_key FROM record_completeness) AND db_name IN (SELECT db_name FROM record_completeness) AND table_name IN (SELECT table_name FROM record_completeness) AND timestamp IN (SELECT timestamp FROM record_completeness);")
		self.conn.execute("DROP VIEW record_completeness;")

		cursor = self.conn.execute("SELECT * FROM record_metrics")

		headers = [description[0] for description in cursor.description]

		# print(tabulate(cursor.fetchall()[:20], headers=headers, tablefmt='orgtbl'))

	def generate_record_correctness(self, constraints, db_name, table_name, primary_key, timestamp):
		query = "SELECT * FROM " + table_name + " LIMIT 1"
		cursor = self.conn.execute(query)
		names = [description[0] for description in cursor.description]

		attribute_constraint = {}
		for i in range(len(names)):
			attribute_constraint[names[i]] = constraints[i]

		record_correctness_query = "SELECT '"+ db_name + "' AS db_name, '" + table_name + "' AS table_name, " + primary_key +" AS primary_key, '" + timestamp + "' AS timestamp, (CAST("

		for attribute in names:
			attribute_constraints = attribute_constraint[attribute]
			if (len(attribute_constraint) > 0):
				record_correctness_query += "(CASE "
				for constraint in attribute_constraints:
					record_correctness_query += "WHEN " + attribute + " " + constraint + " THEN 1 "
				record_correctness_query += "ELSE 0 END) + "

		record_correctness_query = record_correctness_query[:-2]
		record_correctness_query += "AS FLOAT) * 100 / " + str(len(names)) + ") AS 'correctness' FROM " + table_name
		record_correctness_query = "CREATE VIEW record_correctness AS " + record_correctness_query

		cursor = self.conn.execute(record_correctness_query)

		try:
			self.conn.execute("ALTER TABLE record_metrics ADD COLUMN correctness;")
		except sqlite3.OperationalError:
			# print("column already exists, do nothing")
			pass

		self.conn.execute("UPDATE record_metrics SET correctness = ( SELECT record_correctness.correctness FROM record_correctness WHERE record_correctness.primary_key = record_metrics.primary_key AND record_correctness.db_name = record_metrics.db_name AND record_correctness.table_name = record_metrics.table_name AND record_correctness.timestamp = record_metrics.timestamp) WHERE primary_key IN (SELECT primary_key FROM record_correctness) AND db_name IN (SELECT db_name FROM record_correctness) AND table_name IN (SELECT table_name FROM record_correctness) AND timestamp IN (SELECT timestamp FROM record_correctness);")
		self.conn.execute("DROP VIEW record_correctness;")

		cursor = self.conn.execute("SELECT * FROM record_metrics")

		headers = [description[0] for description in cursor.description]

		# print(tabulate(cursor.fetchall()[:20], headers=headers, tablefmt='orgtbl'))

	def generate_record_redundancy(self, db_name, table_name, primary_key, timestamp):
		query = "SELECT * FROM " + table_name + " LIMIT 1"
		cursor = self.conn.execute(query)
		names = [description[0] for description in cursor.description]

		primary_key_index = 0

		for i in range(len(names)):
			if names[i] == primary_key:
				primary_key_index = i
				break

		try:
			self.conn.execute("ALTER TABLE record_metrics ADD COLUMN uniqueness;")
		except sqlite3.OperationalError:
			# print("column already exists, do nothing")
			pass

		cursor = self.conn.execute("SELECT * FROM " + table_name)

		row = cursor.fetchone()

		while(row != None):
			query = "UPDATE record_metrics SET uniqueness = " + str( len(set(row)) * 100/len(row)) + " WHERE db_name = '" + db_name + "' AND table_name = '" + table_name + "' AND primary_key = '" + str(row[primary_key_index]) + "' AND timestamp = '" + timestamp + "';"
			self.conn.execute(query)
			row = cursor.fetchone()

		cursor = self.conn.execute("SELECT * FROM record_metrics")

		headers = [description[0] for description in cursor.description]

		# print(tabulate(cursor.fetchall()[:20], headers=headers, tablefmt='orgtbl'))

	def generate_record_overall(self):
		try:
			self.conn.execute("ALTER TABLE record_metrics ADD COLUMN overall;")
		except sqlite3.OperationalError:
			# print("column already exists, do nothing")
			pass

		record_overall_query = "UPDATE record_metrics SET overall = ("

		for metric in self.metrics:
			record_overall_query += metric + " + "

		record_overall_query = record_overall_query[:-2] + ") / " + str(len(self.metrics))

		self.conn.execute(record_overall_query)

	def get_metric_tables(self) -> tuple([pd.DataFrame, pd.DataFrame]):

		attribute_metric_table = pd.read_sql_query("SELECT * FROM attribute_metrics",self.conn)
		record_metric_table = pd.read_sql_query("SELECT * FROM record_metrics",self.conn)

		return (attribute_metric_table, record_metric_table)
