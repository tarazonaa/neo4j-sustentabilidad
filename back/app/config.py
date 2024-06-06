# config.py
from neo4j import GraphDatabase


class Config:
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "Micosis_23"

    @classmethod
    def get_driver(cls):
        return GraphDatabase.driver(
            cls.NEO4J_URI, auth=(cls.NEO4J_USER, cls.NEO4J_PASSWORD)
        )
