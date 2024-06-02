# config.py
import os
from neo4j import GraphDatabase

class Config:
    NEO4J_URI = os.environ.get("NEO4J_URI")
    NEO4J_USER = os.environ.get("NEO4J_USER")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

    @classmethod
    def get_driver(cls):
      if not cls.NEO4J_URI or not cls.NEO4J_USER or not cls.NEO4J_PASSWORD:
          raise ValueError("Missing Neo4j configuration.")
      return GraphDatabase.driver(
        cls.NEO4J_URI,
        auth=(cls.NEO4J_USER, cls.NEO4J_PASSWORD)
      )
