import logging
import os

from neo4j import GraphDatabase

# Enable logging
logging.basicConfig(level=logging.DEBUG)

NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USER = os.environ.get("NEO4J_USER")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

def test_connection():
    driver = GraphDatabase.driver(
        NEO4J_URI, 
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    try:
        with driver.session() as session:
            result = session.run("RETURN 1")
            print(result.single())
        print("Connection successful")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    test_connection()
