import math
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from pydantic import BaseModel

from app.config import Config

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

@app.get("/api/bonus")
async def get_neighborhoods_for_bonus():
    with driver.session() as session:

        # First Subquery: Get countries with lowest, median, and highest metric values
        query1 = """
            MATCH (c:Country)-[m:MEASURED]->(metric:Metric)
            WHERE m.year >= '1991' AND m.year <= '2018'
            WITH c, metric, m.year AS year, toFloat(m.value) AS value
            ORDER BY c.name, metric.name, year
            WITH c, metric.name AS metric_name, COLLECT(year) AS years, COLLECT(value) AS values
            WHERE SIZE(values) = (2018 - 1991 + 1)
            UNWIND RANGE(1, SIZE(values)-1) AS i
            WITH c, metric_name, values[i] AS current_value, values[i-1] AS previous_value
            WHERE previous_value <> 0 
            WITH c, metric_name, (current_value - previous_value) / previous_value * 100 AS yearly_percentage_change
            WHERE NOT isnan(yearly_percentage_change) AND NOT yearly_percentage_change = 'Infinity'  // Filter out NaNs and Infinities
            WITH c, AVG(yearly_percentage_change) AS avg_percentage_change
            WITH c.name AS country, avg_percentage_change
            ORDER BY avg_percentage_change DESC

            WITH COLLECT({country: country, avg_percentage_change: avg_percentage_change}) AS results
            WITH results, SIZE(results) AS total
            WITH results, total, 
                 results[0] AS best_1,
                 results[1] as best_2,
                 results[2] as best_3, 
                 results[toInteger(total / 2)] AS middle_1,
                 results[toInteger(total/2) + 1] as middle_2, 
                 results[toInteger(total/2) - 1] as middle_3, 
                 results[total - 1] AS lowest_1,
                 results[total - 2] AS lowest_2,
                 results[total - 3] AS lowest_3

            UNWIND [best_1, best_2, best_3, middle_1, middle_2, middle_3, lowest_1, lowest_2, lowest_3] AS main
            MATCH (start:Country {name: main.country})
            CALL apoc.path.subgraphNodes(start, {
              relationshipFilter: "NEIGHBORS",
              minLevel: 1,
              maxLevel: 2,
              limit: 100
            }) YIELD node AS neighbor
            WITH main, neighbor
            MATCH (neighbor)-[m:MEASURED]->(metric:Metric)
            WHERE m.year >= '1991' AND m.year <= '2018'
            WITH main, neighbor, metric, m.year AS year, toFloat(m.value) AS value
            ORDER BY neighbor.name, metric.name, year
            WITH main, neighbor, metric.name AS metric_name, COLLECT(year) AS years, COLLECT(value) AS values
            WHERE SIZE(values) = (2018 - 1991 + 1)
            UNWIND RANGE(1, SIZE(values)-1) AS i
            WITH main, neighbor, values[i] AS current_value, values[i-1] AS previous_value
            WHERE previous_value <> 0
            WITH main, neighbor, (current_value - previous_value) / previous_value * 100 AS yearly_percentage_change
            WHERE NOT isnan(yearly_percentage_change) AND NOT yearly_percentage_change = 'Infinity'  // Filter out NaNs and Infinities
            WITH main, neighbor, AVG(yearly_percentage_change) AS neighbor_avg_percentage_change

            RETURN main.country AS main_country, main.avg_percentage_change AS main_avg_percentage_change,
                   neighbor.name AS neighbor_country, neighbor_avg_percentage_change
            ORDER BY main_country, neighbor_avg_percentage_change DESC
        """
        result = session.run(query1)
        records = [record.data() for record in result]

        return {"data": records}

@app.get("/api/metrics/changes")
async def get_metrics_changes(order: str = "ASC"):
    query = """
    MATCH (c:Country)-[r:MEASURED]->(m:Metric)
    RETURN m.name AS Metric, r.year AS Year, r.value AS Value
    ORDER BY m.name, r.year
    """

    # We can limit it with ejemplo LIMIT 10

    try:
        with driver.session() as session:
            result = session.run(query)
            data = [
                (record["Metric"], record["Year"], record["Value"]) for record in result
            ]

        print("Fetched data:", data)

        if not data:
            raise HTTPException(
                status_code=404, detail="No data retrieved from the database"
            )

        # Convert data to a DataFrame
        df = pd.DataFrame(data, columns=["Metric", "Year", "Value"])

        # Convert Year and Value to appropriate data types
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

        # Drop rows with invalid data
        df = df.dropna(subset=["Year", "Value"])

        if df.empty:
            raise HTTPException(status_code=404, detail="No data found in DataFrame")

        # Check for duplicates and aggregate values if needed
        df = df.groupby(["Metric", "Year"]).agg({"Value": "mean"}).reset_index()

        # Calculate the change for each metric
        df["Change"] = df.groupby("Metric")["Value"].diff()

        # Handle potential outliers
        q1 = df["Change"].quantile(0.25)
        q3 = df["Change"].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Filter out outliers
        df_filtered = df[(df["Change"] >= lower_bound) & (df["Change"] <= upper_bound)]

        # Sort the DataFrame by change
        ascending_order = order.upper() == "ASC"
        sorted_df = df_filtered.sort_values(by="Change", ascending=ascending_order)

        # sorted DataFrame
        print("Sorted DataFrame:", sorted_df)

        return {"data": sorted_df.to_dict(orient="records"), "order": order.upper()}
    except Exception as e:

        print("Error:", str(e))
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )

# En que regiones se ha avanzado / retrocedido por métrica en mayor / menor medida
@app.get("/api/metrics/by-region")
async def get_regions_by_metric(strategy: Optional[str] = 'relative', order: Optional[str] = 'DESC'):
    if order.upper() not in ['ASC', 'DESC']:
        raise HTTPException(status_code=400, detail="Invalid ordering")
    
    query = None

    if strategy == 'relative':
      query = f"""
      MATCH (reg:Region)<-[:IS_IN]-(c:Country)-[r:MEASURED]->(m:Metric)
      WITH reg, c, m, MIN(r.year) AS firstYear, MAX(r.year) AS lastYear

      MATCH (reg)<-[:IS_IN]-(c)-[first:MEASURED {{year: firstYear}}]->(m)
      WITH reg, c, m, firstYear, toFloat(first.value) AS firstValue, lastYear

      MATCH (reg)<-[:IS_IN]-(c)-[last:MEASURED {{year: lastYear}}]->(m)
      WITH reg, c, m, firstYear, firstValue, lastYear, toFloat(last.value) AS lastValue

      WITH reg, c, m, firstYear, firstValue, lastYear, lastValue,
        CASE 
          WHEN firstValue <> 0.0 THEN (lastValue - firstValue) * m.multiplier / firstValue 
          ELSE 0 
        END AS idx

      WITH reg, m, AVG(idx) AS averageIndicator
      ORDER BY m.name, averageIndicator {order.upper()}

      WITH m.name AS metric, COLLECT({{region: reg.name, avgIndicator: averageIndicator * m.multiplier}}) AS regionChanges
      RETURN metric, regionChanges[0].region AS region, regionChanges[0].avgIndicator AS value
      ORDER BY metric
      """

    elif strategy == 'absolute':
      query = f"""
      MATCH (reg:Region)<-[:IS_IN]-(c:Country)-[r:MEASURED]->(m:Metric)
      WITH reg, c, m, MAX(r.year) AS lastYear

      MATCH (reg)<-[:IS_IN]-(c)-[last:MEASURED {{year: lastYear}}]->(m)
      WITH reg, c, m, toFloat(last.value) AS lastValue

      WITH reg, m, AVG(lastValue * m.multiplier) AS averageIndicator
      ORDER BY m.name, averageIndicator {order.upper()}

      WITH m.name AS metric, COLLECT({{region: reg.name, avgIndicator: averageIndicator * m.multiplier}}) AS regionChanges
      RETURN metric, regionChanges[0].region AS region, regionChanges[0].avgIndicator AS value
      ORDER BY metric
      """
    else:
      raise HTTPException(status_code=400, detail="Invalid strategy")

    try:
      with driver.session() as session:
        result = session.run(query)
        return {
            "data": [record.data() for record in result],
            "order": order.upper(),
            "strategy": strategy,
            "query": query
        }
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    finally:
      session.close()
        
# Que países han avanzado / retrocedido comparado vs otros en su región (ahorita me vv la región xd)	
@app.get("/api/metrics/by-country")
async def get_countries_by_metric(strategy: Optional[str] = 'relative', order: Optional[str] = 'DESC'):
    if order.upper() not in ['ASC', 'DESC']:
        raise HTTPException(status_code=400, detail="Invalid ordering")
    
    query = None

    if strategy == 'relative':
      query = f"""
      MATCH (c:Country)-[r:MEASURED]->(m:Metric)
      WITH c, m, MIN(r.year) AS firstYear, MAX(r.year) AS lastYear

      MATCH (c)-[first:MEASURED {{year: firstYear}}]->(m)
      WITH c, m, firstYear, toFloat(first.value) AS firstValue, lastYear

      MATCH (c)-[last:MEASURED {{year: lastYear}}]->(m)
      WITH c, m, firstYear, firstValue, lastYear, toFloat(last.value) AS lastValue

      WITH c, m, firstYear, firstValue, lastYear, lastValue,
        CASE 
          WHEN firstValue <> 0.0 THEN (lastValue - firstValue) * m.multiplier / firstValue 
          ELSE 0 
        END AS idx
      ORDER BY m.name, idx {order.upper()}
        
      WITH m.name AS metric, COLLECT({{country: c.code, index: idx * m.multiplier}}) AS countryChanges
      RETURN metric, countryChanges[0].country AS country, countryChanges[0].index AS value
      ORDER BY metric
      """
    elif strategy == 'absolute':
      query = f"""
      MATCH (c:Country)-[r:MEASURED]->(m:Metric)
      WITH c, m, MAX(r.year) AS lastYear

      MATCH (c)-[last:MEASURED {{year: lastYear}}]->(m)
      WITH c, m, toFloat(last.value) AS lastValue
      ORDER BY m.name, lastValue {order.upper()}

      WITH m.name AS metric, COLLECT({{country: c.code, value: lastValue * m.multiplier}}) AS countryChanges
      RETURN metric, countryChanges[0].country AS country, countryChanges[0].value AS value
      ORDER BY metric
      """
    else:
      raise HTTPException(status_code=400, detail="Invalid strategy")

    try:
        with driver.session() as session:
            result = session.run(query)
            print(result)
            return {
                "data": [record.data() for record in result],
                "order": order.upper(),
                "strategy": strategy,
                "query": query
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
       session.close()

# En su opinión, ¿Cuáles serían los 10 países a tomar como referencia?
# En su opinión, ¿Cuáles serían los 10 países donde más oportunidad hay? Y ¿qué les beneficiaría más?
@app.get("/api/metrics/top-countries")
async def get_top_countries(order: Optional[str] = 'DESC'):
    if order.upper() not in ['ASC', 'DESC']:
        raise HTTPException(status_code=400, detail="Invalid ordering")
    
    query = f"""
    MATCH (:Country)-[measured:MEASURED]->(metric:Metric)
    WHERE measured.value IS NOT NULL
    WITH metric, toFloat(measured.value) AS numericValue

    WITH metric,
      min(numericValue * metric.multiplier) AS minValue,
      max(numericValue * metric.multiplier) AS maxValue

    CALL {{
      WITH metric, minValue, maxValue

      MATCH (c:Country)-[m:MEASURED]->(metric)
      WHERE m.value IS NOT NULL
      WITH c, metric, toFloat(m.value) AS value, minValue, maxValue,
        toFloat(metric.multiplier) AS multiplier

      RETURN c, metric AS met, ((value * multiplier - minValue) / (maxValue - minValue)) AS normalizedValue
    }}

    WITH c, AVG(normalizedValue) AS averageNormalizedValue
    RETURN c.code AS country, AVG(averageNormalizedValue) AS value
    ORDER BY value {order.upper()}
    LIMIT 10
    """
    
    try:
      with driver.session() as session:
        result = session.run(query)
        return {
            "data": [record.data() for record in result],
            "order": order.upper()
        }
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
    finally:
      session.close()