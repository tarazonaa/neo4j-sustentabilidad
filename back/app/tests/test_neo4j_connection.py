import logging
from neo4j import GraphDatabase

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# Neo4j Aura connection details
NEO4J_URI = "neo4j+ssc://2f81b269.databases.neo4j.io"  # Note the use of neo4j+ssc
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "WOh6fMnAwdRKSbaN_EVS9SlRZP3IkpEfnsChAqHY4BI"

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
