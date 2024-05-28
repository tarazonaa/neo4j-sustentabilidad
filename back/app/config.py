# config.py
from neo4j import GraphDatabase

class Config:
    NEO4J_URI = "neo4j+ssc://2f81b269.databases.neo4j.io"  
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "WOh6fMnAwdRKSbaN_EVS9SlRZP3IkpEfnsChAqHY4BI"

    @classmethod
    def get_driver(cls):
        return GraphDatabase.driver(cls.NEO4J_URI, auth=(cls.NEO4J_USER, cls.NEO4J_PASSWORD))