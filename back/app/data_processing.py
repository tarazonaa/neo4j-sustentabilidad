from config import Config
import pandas as pd

driver = Config.get_driver()

relationships_df = pd.read_csv("./csvs/data_combined.csv")

# Rename the columns country code and indicator name
relationships_df = relationships_df.rename(columns={"Country Code": "country_code", "Indicator Code": "indicator_code"})

query = """
LOAD CSV WITH HEADERS FROM 'https://neo4j-ps-ds-bootcamp.s3.amazonaws.com/data/hackaton/SDGData_Combined.csv' AS row
WITH row
MATCH (c:Country {code: row.`Country Code`})
MATCH (m:Metric {code: row.`Indicator Code`})
MERGE (c)-[r:MEASURED {id: row.value_id, year: row.Year, value: row.value}]->(m)
RETURN c, r, m LIMIT 25;
"""

with driver.session() as session:
    result = session.run(query).data()
    print("Result: ", list(result))
    countries = [record["row"] for record in result]
    for country in countries:
        __import__('pprint').pprint(country)
