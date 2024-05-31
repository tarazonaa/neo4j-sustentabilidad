from fastapi import FastAPI, HTTPException, Request
from neo4j import GraphDatabase
from pydantic import BaseModel
from typing import List, Optional
from app.config import Config
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

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
        

@app.get("/api/metrics/changes")
async def get_metrics_changes(order: str = 'ASC'):
    query = """
    MATCH (c:Country)-[r:MEASURED]->(m:Metric)
    RETURN m.name AS Metric, r.year AS Year, r.value AS Value
    ORDER BY m.name, r.year
    """

    # We can limit it with ejemplo LIMIT 10
    
    try:
        with driver.session() as session:
            result = session.run(query)
            data = [(record["Metric"], record["Year"], record["Value"]) for record in result]
        
        print("Fetched data:", data)
        
        if not data:
            raise HTTPException(status_code=404, detail="No data retrieved from the database")

        # Convert data to a DataFrame
        df = pd.DataFrame(data, columns=["Metric", "Year", "Value"])
        
        # Convert Year and Value to appropriate data types
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')

        # Drop rows with invalid data
        df = df.dropna(subset=['Year', 'Value'])
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found in DataFrame")
        
        # Check for duplicates and aggregate values if needed
        df = df.groupby(['Metric', 'Year']).agg({'Value': 'mean'}).reset_index()
        
        # Calculate the change for each metric
        df['Change'] = df.groupby('Metric')['Value'].diff()

        # Handle potential outliers
        q1 = df['Change'].quantile(0.25)
        q3 = df['Change'].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Filter out outliers
        df_filtered = df[(df['Change'] >= lower_bound) & (df['Change'] <= upper_bound)]

        # Sort the DataFrame by change
        ascending_order = order.upper() == 'ASC'
        sorted_df = df_filtered.sort_values(by='Change', ascending=ascending_order)

        # sorted DataFrame
        print("Sorted DataFrame:", sorted_df)

        return {
            "data": sorted_df.to_dict(orient='records'),
            "order": order.upper()
        }
    except Exception as e:
        
        print("Error:", str(e))
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the request: {str(e)}")





