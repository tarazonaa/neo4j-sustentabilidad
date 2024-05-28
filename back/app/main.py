from fastapi import FastAPI, HTTPException, Request
from neo4j import GraphDatabase
from pydantic import BaseModel
from typing import List, Optional
from .config import Config  

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

driver = Config.get_driver()

# Close the driver connection when the app is shutting down
@app.on_event("shutdown")
def shutdown_event():
    driver.close()

# Root endpoint for testing
@app.get("/")
async def root():
    return {"message": "Big testing"}

# Endpoint to get country data
@app.get("/api/countries")
async def get_countries():
    query = "MATCH (c:Country) RETURN c.code2 AS code2, c.code AS code, c.notes AS notes, c.name AS name, c.currency AS currency LIMIT 10"
    with driver.session() as session:
        result = session.run(query)
        countries = [record.data() for record in result]
    return {"countries": countries}

# Endpoint to get region data
@app.get("/api/regions")
async def get_regions():
    query = "MATCH (r:Region) RETURN r.name AS name, r.id AS id LIMIT 10"
    with driver.session() as session:
        result = session.run(query)
        regions = [record.data() for record in result]
    return {"regions": regions}

# Endpoint to get metric data
@app.get("/api/metrics")
async def get_metrics():
    query = "MATCH (m:Metric) RETURN m.code AS code, m.name AS name, m.periodicity AS periodicity, m.definition AS definition LIMIT 10"
    with driver.session() as session:
        result = session.run(query)
        metrics = [record.data() for record in result]
    return {"metrics": metrics}

# Endpoint to get income group data
@app.get("/api/income-groups")
async def get_income_groups():
    query = "MATCH (i:IncomeGroup) RETURN i.name AS name, i.id AS id LIMIT 10"
    with driver.session() as session:
        result = session.run(query)
        income_groups = [record.data() for record in result]
    return {"income_groups": income_groups}

# Endpoint to get topic data
@app.get("/api/topics")
async def get_topics():
    query = "MATCH (t:Topic) RETURN t.topic AS topic, t.id AS id LIMIT 10"
    with driver.session() as session:
        result = session.run(query)
        topics = [record.data() for record in result]
    return {"topics": topics}

# Endpoint to execute Cypher queries
@app.post("/api/execute-cypher")
async def execute_cypher(request: Request):
    body = await request.json()
    cypher_query = body.get("query")
    
    if not cypher_query:
        raise HTTPException(status_code=400, detail="Query not provided")

    with driver.session() as session:
        try:
            result = session.run(cypher_query)
            records = [record.data() for record in result]
            return {"result": records}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
