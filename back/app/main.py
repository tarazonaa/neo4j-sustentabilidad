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
    query = "MATCH (m:Metric) RETURN m.id AS code, m.name AS name, m.periodicity AS periodicity, m.definition AS definition LIMIT 10"
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

        query = """
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
            WHERE NOT isnan(yearly_percentage_change) AND NOT yearly_percentage_change = 'Infinity'
            WITH c.name as country, AVG(yearly_percentage_change) AS avg_percentage_change
            ORDER BY avg_percentage_change DESC

            WITH COLLECT({country: country, avg_percentage_change: avg_percentage_change}) AS results
            WITH results, SIZE(results) AS total
            WITH results,
                 results[0] AS best_1,
                 results[1] as best_2,
                 results[2] as best_3,
                 results[toInteger(total / 2)] AS middle_1,
                 results[toInteger(total/2) + 1] as middle_2,
                 results[toInteger(total/2) - 1] as middle_3,
                 results[total - 1] AS lowest_1,
                 results[total - 2] AS lowest_2,
                 results[total - 3] AS lowest_3

            WITH [best_1, best_2, best_3, middle_1, middle_2, middle_3, lowest_1, lowest_2, lowest_3] AS main_results, results
            UNWIND main_results AS main
            MATCH (start:Country {name: main.country})

            CALL apoc.path.subgraphNodes(start, {
              relationshipFilter: "NEIGHBORS",
              minLevel: 1,
              maxLevel: 2,
              limit: 100
            }) YIELD node AS neighbor

            WITH main, neighbor, results
            UNWIND results AS result
            MATCH (neighbor:Country {name: result.country})
            RETURN main.country AS main_country, 
                   main.avg_percentage_change AS main_avg_percentage_change,
                   neighbor.name AS neighbor_country, 
                   result.avg_percentage_change AS neighbor_avg_percentage_change
            ORDER BY main_country, neighbor_avg_percentage_change DESC
        """
        result = session.run(query)
        records = [record.data() for record in result]
        data = {}
        for record in records:
            if record["main_country"] not in data:
                data[record["main_country"]] = {
                    "main_country_percentage": record["main_avg_percentage_change"],
                    "neighboring_countries": {},
                }
            data[record["main_country"]]["neighboring_countries"][
                record["neighbor_country"]
            ] = record["neighbor_avg_percentage_change"]

        return {"data": data}


@app.get("/api/metrics/changes_income")
async def get_metrics_changes_income(order: str = "ASC"):
    # Consulta para obtener las métricas con los mayores cambios promedio positivos
    query_positive = """
    MATCH (c:Country)-[r:MEASURED]->(m:Metric)
    MATCH (c)-[:IS_PART_OF]->(i:IncomeGroup)
    WITH m.name AS Metric, r.year AS Year, toFloat(r.value) AS Value, i.name as IncomeGroup
    ORDER BY Metric, Year
    WITH Metric, IncomeGroup, collect(Value) AS Values, collect(Year) AS Years
    WITH Metric, IncomeGroup, apoc.coll.pairsMin(Values) AS Changes, Years
    UNWIND range(0, size(Changes) - 1) AS i
    WITH Metric, Changes[i] AS Change, Years[i + 1] AS Year, IncomeGroup
    WITH Metric, (Change[1] - Change[0]) AS Change, Year, IncomeGroup
    RETURN Metric, avg(Change) AS AvgChange, Year, IncomeGroup
    ORDER BY AvgChange DESC
    LIMIT 3
    """

    # Consulta para obtener las métricas con los mayores cambios promedio negativos
    query_negative = """
    MATCH (c:Country)-[r:MEASURED]->(m:Metric)
    MATCH (c)-[:IS_PART_OF]->(i:IncomeGroup)
    WITH m.name AS Metric, r.year AS Year, toFloat(r.value) AS Value, i.name as IncomeGroup
    ORDER BY Metric, Year
    WITH Metric, collect(Value) AS Values, collect(Year) AS Years, IncomeGroup
    WITH Metric, apoc.coll.pairsMin(Values) AS Changes, Years, IncomeGroup
    UNWIND range(0, size(Changes) - 1) AS i
    WITH Metric, Changes[i] AS Change, Years[i + 1] AS Year, IncomeGroup
    WITH Metric, (Change[1] - Change[0]) AS Change, Year, IncomeGroup
    RETURN Metric, avg(Change) AS AvgChange, Year, IncomeGroup
    ORDER BY AvgChange ASC
    LIMIT 3
    """

    try:
        with driver.session() as session:
            # Ejecutar la consulta de cambios positivos
            result_positive = session.run(query_positive)
            data_positive = [
                {
                    "Metric": record["Metric"],
                    "AvgChange": record["AvgChange"],
                    "Year": record["Year"],
                    "IncomeGroup": record["IncomeGroup"],
                }
                for record in result_positive
            ]

            # Ejecutar la consulta de cambios negativos
            result_negative = session.run(query_negative)
            data_negative = [
                {
                    "Metric": record["Metric"],
                    "AvgChange": record["AvgChange"],
                    "Year": record["Year"],
                    "IncomeGroup": record["IncomeGroup"],
                }
                for record in result_negative
            ]

        # Verificar si no se obtuvieron datos
        if not data_positive and not data_negative:
            raise HTTPException(
                status_code=404, detail="No data retrieved from the database"
            )

        # Combinar los datos de cambios positivos y negativos
        combined_data = data_positive + data_negative

        # Ordenar los datos combinados según el parámetro de orden
        combined_data = sorted(
            combined_data,
            key=lambda x: x["AvgChange"],
            reverse=(order.upper() == "DESC"),
        )

        # Retornar la respuesta con los datos combinados y el orden
        return {"data": combined_data, "order": order.upper()}
    except Exception as e:
        # Manejo de errores y respuesta con código de estado 500
        print("Error:", str(e))
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )


@app.get("/api/metrics/changes")
async def get_metrics_changes(order: str = "ASC"):
    # Consulta para obtener las métricas con los mayores cambios promedio positivos
    query_positive = """
    MATCH (c:Country)-[r:MEASURED]->(m:Metric)
    WITH m.name AS Metric, r.year AS Year, toFloat(r.value) AS Value
    ORDER BY Metric, Year
    WITH Metric, collect(Value) AS Values, collect(Year) AS Years
    WITH Metric, apoc.coll.pairsMin(Values) AS Changes, Years
    UNWIND range(0, size(Changes) - 1) AS i
    WITH Metric, Changes[i] AS Change, Years[i + 1] AS Year
    WITH Metric, (Change[1] - Change[0]) AS Change, Year
    RETURN Metric, avg(Change) AS AvgChange, Year
    ORDER BY AvgChange DESC
    LIMIT 3
    """

    # Consulta para obtener las métricas con los mayores cambios promedio negativos
    query_negative = """
    MATCH (c:Country)-[r:MEASURED]->(m:Metric)
    WITH m.name AS Metric, r.year AS Year, toFloat(r.value) AS Value
    ORDER BY Metric, Year
    WITH Metric, collect(Value) AS Values, collect(Year) AS Years
    WITH Metric, apoc.coll.pairsMin(Values) AS Changes, Years
    UNWIND range(0, size(Changes) - 1) AS i
    WITH Metric, Changes[i] AS Change, Years[i + 1] AS Year
    WITH Metric, (Change[1] - Change[0]) AS Change, Year
    RETURN Metric, avg(Change) AS AvgChange, Year
    ORDER BY AvgChange ASC
    LIMIT 3
    """

    try:
        with driver.session() as session:
            # Ejecutar la consulta de cambios positivos
            result_positive = session.run(query_positive)
            data_positive = [
                {
                    "Metric": record["Metric"],
                    "AvgChange": record["AvgChange"],
                    "Year": record["Year"],
                }
                for record in result_positive
            ]

            # Ejecutar la consulta de cambios negativos
            result_negative = session.run(query_negative)
            data_negative = [
                {
                    "Metric": record["Metric"],
                    "AvgChange": record["AvgChange"],
                    "Year": record["Year"],
                }
                for record in result_negative
            ]

        # Verificar si no se obtuvieron datos
        if not data_positive and not data_negative:
            raise HTTPException(
                status_code=404, detail="No data retrieved from the database"
            )

        # Combinar los datos de cambios positivos y negativos
        combined_data = data_positive + data_negative

        # Ordenar los datos combinados según el parámetro de orden
        combined_data = sorted(
            combined_data,
            key=lambda x: x["AvgChange"],
            reverse=(order.upper() == "DESC"),
        )

        # Retornar la respuesta con los datos combinados y el orden
        return {"data": combined_data, "order": order.upper()}
    except Exception as e:
        # Manejo de errores y respuesta con código de estado 500
        print("Error:", str(e))
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )


# En que regiones se ha avanzado / retrocedido por métrica en mayor / menor medida
@app.get("/api/metrics/by-region")
async def get_regions_by_metric(
    strategy: Optional[str] = "relative", order: Optional[str] = "DESC"
):
    if order.upper() not in ["ASC", "DESC"]:
        raise HTTPException(status_code=400, detail="Invalid ordering")

    query = None

    if strategy == "relative":
        query = f"""
      MATCH (reg:Region)<-[:IS_IN]-(c:Country)-[r:MEASURED]->(m:Metric)
      WITH reg, c, m, MIN(r.year) AS firstYear, MAX(r.year) AS lastYear

      MATCH (reg)<-[:IS_IN]-(c)-[first:MEASURED {{year: firstYear}}]->(m)
      WITH reg, c, m, firstYear, toFloat(first.value) AS firstValue, lastYear

      MATCH (reg)<-[:IS_IN]-(c)-[last:MEASURED {{year: lastYear}}]->(m)
      WITH reg, c, m, firstYear, firstValue, lastYear, toFloat(last.value) AS lastValue

      WITH reg, c, m, firstYear, firstValue, lastYear, lastValue,
        CASE 
          WHEN firstValue <> 0.0 THEN (lastValue - firstValue) / firstValue 
          ELSE 0 
        END AS idx

      WITH reg, m, AVG(idx) AS averageIndicator
      ORDER BY m.name, averageIndicator {order.upper()}

      WITH m.name AS metric, COLLECT({{region: reg.name, avgIndicator: averageIndicator }}) AS regionChanges
      RETURN metric, regionChanges[0].region AS region, regionChanges[0].avgIndicator AS value
      ORDER BY metric
      """

    elif strategy == "absolute":
        query = f"""
      MATCH (reg:Region)<-[:IS_IN]-(c:Country)-[r:MEASURED]->(m:Metric)
      WITH reg, c, m, MAX(r.year) AS lastYear

      MATCH (reg)<-[:IS_IN]-(c)-[last:MEASURED {{year: lastYear}}]->(m)
      WITH reg, c, m, toFloat(last.value) AS lastValue

      WITH reg, m, AVG(lastValue) AS averageIndicator
      ORDER BY m.name, averageIndicator {order.upper()}

      WITH m.name AS metric, COLLECT({{region: reg.name, avgIndicator: averageIndicator }}) AS regionChanges
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
                "query": query,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# Que países han avanzado / retrocedido comparado vs otros en su región
@app.get("/api/metrics/by-country")
async def get_countries_by_metric(
    strategy: Optional[str] = "relative", order: Optional[str] = "DESC"
):
    if order.upper() not in ["ASC", "DESC"]:
        raise HTTPException(status_code=400, detail="Invalid ordering")

    query = None

    if strategy == "relative":
        query = f"""
      MATCH (c:Country)-[r:MEASURED]->(m:Metric)
      WITH c, m, MIN(r.year) AS firstYear, MAX(r.year) AS lastYear

      MATCH (c)-[first:MEASURED {{year: firstYear}}]->(m)
      WITH c, m, firstYear, toFloat(first.value) AS firstValue, lastYear

      MATCH (c)-[last:MEASURED {{year: lastYear}}]->(m)
      WITH c, m, firstYear, firstValue, lastYear, toFloat(last.value) AS lastValue

      WITH c, m, firstYear, firstValue, lastYear, lastValue,
        CASE 
          WHEN firstValue <> 0.0 THEN (lastValue - firstValue) / firstValue 
          ELSE 0 
        END AS idx
      ORDER BY m.name, idx {order.upper()}
        
      WITH m.name AS metric, COLLECT({{country: c.code, index: idx }}) AS countryChanges
      RETURN metric, countryChanges[0].country AS country, countryChanges[0].index AS value
      ORDER BY metric
      """
    elif strategy == "absolute":
        query = f"""
      MATCH (c:Country)-[r:MEASURED]->(m:Metric)
      WITH c, m, MAX(r.year) AS lastYear

      MATCH (c)-[last:MEASURED {{year: lastYear}}]->(m)
      WITH c, m, toFloat(last.value) AS lastValue
      ORDER BY m.name, lastValue {order.upper()}

      WITH m.name AS metric, COLLECT({{country: c.code, value: lastValue }}) AS countryChanges
      RETURN metric, countryChanges[0].country AS country, countryChanges[0].value AS value
      ORDER BY metric
      """
    else:
        raise HTTPException(status_code=400, detail="Invalid strategy")

    try:
        with driver.session() as session:
            # result = session.run(query)
            # return {
            #     "data": [record.data() for record in result],
            #     "order": order.upper(),
            #     "strategy": strategy,
            #     "query": query,
            # }
            return {
    "data": [
        {
            "metric": "Access to clean fuels and technologies for cooking (% of population)",
            "country": "AND",
            "value": 100.0
        },
        {
            "metric": "Access to electricity (% of population)",
            "country": "AUT",
            "value": 100.0
        },
        {
            "metric": "Access to electricity, rural (% of rural population)",
            "country": "TJK",
            "value": 100.0
        },
        {
            "metric": "Access to electricity, urban (% of urban population)",
            "country": "ATG",
            "value": 100.0
        },
        {
            "metric": "Account ownership at a financial institution or with a mobile-money-service provider (% of population ages 15+)",
            "country": "DNK",
            "value": 99.91737366
        },
        {
            "metric": "Account ownership at a financial institution or with a mobile-money-service provider, female (% of population ages 15+)",
            "country": "SWE",
            "value": 100.0
        },
        {
            "metric": "Account ownership at a financial institution or with a mobile-money-service provider, male (% of population ages 15+)",
            "country": "FIN",
            "value": 100.0
        },
        {
            "metric": "Account ownership at a financial institution or with a mobile-money-service provider, older adults (% of population ages 25+)",
            "country": "DNK",
            "value": 99.90249634
        },
        {
            "metric": "Account ownership at a financial institution or with a mobile-money-service provider, poorest 40% (% of population ages 15+)",
            "country": "DNK",
            "value": 100.0
        },
        {
            "metric": "Account ownership at a financial institution or with a mobile-money-service provider, primary education or less (% of population ages 15+)",
            "country": "AUS",
            "value": 100.0
        },
        {
            "metric": "Account ownership at a financial institution or with a mobile-money-service provider, richest 60% (% of population ages 15+)",
            "country": "FIN",
            "value": 100.0
        },
        {
            "metric": "Account ownership at a financial institution or with a mobile-money-service provider, secondary education or more (% of population ages 15+)",
            "country": "FIN",
            "value": 100.0
        },
        {
            "metric": "Account ownership at a financial institution or with a mobile-money-service provider, young adults (% of population ages 15-24)",
            "country": "DNK",
            "value": 100.0
        },
        {
            "metric": "Adjusted net savings, excluding particulate emission damage (% of GNI)",
            "country": "KIR",
            "value": 59.88434925
        },
        {
            "metric": "Adolescent fertility rate (births per 1,000 women ages 15-19)",
            "country": "NER",
            "value": 191.984
        },
        {
            "metric": "Adolescents out of school (% of lower secondary school age)",
            "country": "TZA",
            "value": 73.32218933
        },
        {
            "metric": "Adolescents out of school, female (% of female lower secondary school age)",
            "country": "TCD",
            "value": 69.73795319
        },
        {
            "metric": "Adolescents out of school, male (% of male lower secondary school age)",
            "country": "NER",
            "value": 60.64014053
        },
        {
            "metric": "Agriculture, value added per worker (constant 2010 US$)",
            "country": "ARG",
            "value": 2893899.787
        },
        {
            "metric": "Air transport, freight (million ton-km)",
            "country": "USA",
            "value": 41591.55177
        },
        {
            "metric": "Air transport, passengers carried",
            "country": "USA",
            "value": 849403000.0
        },
        {
            "metric": "Annual freshwater withdrawals, agriculture (% of total freshwater withdrawal)",
            "country": "SOM",
            "value": 99.48
        },
        {
            "metric": "Annual freshwater withdrawals, domestic (% of total freshwater withdrawal)",
            "country": "VCT",
            "value": 100.0
        },
        {
            "metric": "Annual freshwater withdrawals, industry (% of total freshwater withdrawal)",
            "country": "EST",
            "value": 96.22
        },
        {
            "metric": "Annual freshwater withdrawals, total (% of internal resources)",
            "country": "BHR",
            "value": 5967.5
        },
        {
            "metric": "Annual freshwater withdrawals, total (billion cubic meters)",
            "country": "IND",
            "value": 647.5
        },
        {
            "metric": "Annualized average growth rate in per capita real survey mean consumption or income, bottom 40% of population (%)",
            "country": "CHN",
            "value": 9.13
        },
        {
            "metric": "Annualized average growth rate in per capita real survey mean consumption or income, total population (%)",
            "country": "LTU",
            "value": 8.1
        },
        {
            "metric": "Aquaculture production (metric tons)",
            "country": "CHN",
            "value": 63700000.0
        },
        {
            "metric": "Average transaction cost of sending remittances from a specific country (%)",
            "country": "AGO",
            "value": 27.64125466
        },
        {
            "metric": "Average transaction cost of sending remittances to a specific country (%)",
            "country": "NAM",
            "value": 27.645
        },
        {
            "metric": "Battle-related deaths (number of people)",
            "country": "SYR",
            "value": 24950.0
        },
        {
            "metric": "Bird species, threatened",
            "country": "BRA",
            "value": 175.0
        },
        {
            "metric": "Births attended by skilled health staff (% of total)",
            "country": "TKM",
            "value": 100.0
        },
        {
            "metric": "Bribery incidence (% of firms experiencing at least one bribe payment request)",
            "country": "SYR",
            "value": 69.6
        },
        {
            "metric": "CO2 emissions (kg per 2010 US$ of GDP)",
            "country": "TTO",
            "value": 2.052929509
        },
        {
            "metric": "CO2 emissions (kg per 2011 PPP $ of GDP)",
            "country": "TTO",
            "value": 1.095614089
        },
        {
            "metric": "CO2 emissions (kg per PPP $ of GDP)",
            "country": "TTO",
            "value": 1.036841448
        },
        {
            "metric": "CO2 emissions (metric tons per capita)",
            "country": "QAT",
            "value": 45.42323996
        },
        {
            "metric": "Capture fisheries production (metric tons)",
            "country": "CHN",
            "value": 17800000.0
        },
        {
            "metric": "Cereal yield (kg per hectare)",
            "country": "VCT",
            "value": 26110.2
        },
        {
            "metric": "Children in employment, female (% of female children ages 7-14)",
            "country": "GNB",
            "value": 62.45933388
        },
        {
            "metric": "Children in employment, male (% of male children ages 7-14)",
            "country": "GNB",
            "value": 65.34952483
        },
        {
            "metric": "Children in employment, total (% of children ages 7-14)",
            "country": "GNB",
            "value": 63.91617878
        },
        {
            "metric": "Children out of school (% of primary school age)",
            "country": "AFG",
            "value": 71.82878876
        },
        {
            "metric": "Children out of school, female (% of female primary school age)",
            "country": "AFG",
            "value": 85.61157227
        },
        {
            "metric": "Children out of school, male (% of male primary school age)",
            "country": "SSD",
            "value": 63.55094147
        },
        {
            "metric": "Children out of school, primary",
            "country": "CHN",
            "value": 14051869.0
        },
        {
            "metric": "Children out of school, primary, female",
            "country": "CHN",
            "value": 7387977.0
        },
        {
            "metric": "Children out of school, primary, male",
            "country": "CHN",
            "value": 6663892.0
        },
        {
            "metric": "Coal rents (% of GDP)",
            "country": "MNG",
            "value": 9.62525729
        },
        {
            "metric": "Commercial bank branches (per 100,000 adults)",
            "country": "SMR",
            "value": 189.926843
        },
        {
            "metric": "Completeness of birth registration (%)",
            "country": "NLD",
            "value": 100.0
        },
        {
            "metric": "Completeness of birth registration, female (%)",
            "country": "CUB",
            "value": 100.0
        },
        {
            "metric": "Completeness of birth registration, male (%)",
            "country": "CUB",
            "value": 100.0
        },
        {
            "metric": "Completeness of birth registration, rural (%)",
            "country": "UKR",
            "value": 100.0
        },
        {
            "metric": "Completeness of birth registration, urban (%)",
            "country": "PRK",
            "value": 100.0
        },
        {
            "metric": "Compulsory education, duration (years)",
            "country": "GTM",
            "value": 16.0
        },
        {
            "metric": "Contributing family workers, female (% of female employment) (modeled ILO estimate)",
            "country": "AFG",
            "value": 71.78099823
        },
        {
            "metric": "Contributing family workers, male (% of male employment) (modeled ILO estimate)",
            "country": "CAF",
            "value": 32.93899918
        },
        {
            "metric": "Coverage of social insurance programs (% of population)",
            "country": "GHA",
            "value": 59.52041378
        },
        {
            "metric": "Coverage of social insurance programs in 2nd quintile (% of population)",
            "country": "RUS",
            "value": 63.18765623
        },
        {
            "metric": "Coverage of social insurance programs in 3rd quintile (% of population)",
            "country": "HUN",
            "value": 63.67541506
        },
        {
            "metric": "Coverage of social insurance programs in 4th quintile (% of population)",
            "country": "LBN",
            "value": 66.10151624
        },
        {
            "metric": "Coverage of social insurance programs in poorest quintile (% of population)",
            "country": "GHA",
            "value": 60.57968071
        },
        {
            "metric": "Coverage of social insurance programs in richest quintile (% of population)",
            "country": "LBN",
            "value": 79.73951939
        },
        {
            "metric": "Coverage of social safety net programs (% of population)",
            "country": "MNG",
            "value": 99.83052731
        },
        {
            "metric": "Coverage of social safety net programs in 2nd quintile (% of population)",
            "country": "MNG",
            "value": 99.8336716
        },
        {
            "metric": "Coverage of social safety net programs in 3rd quintile (% of population)",
            "country": "MNG",
            "value": 99.91669892
        },
        {
            "metric": "Coverage of social safety net programs in 4th quintile (% of population)",
            "country": "MNG",
            "value": 99.95052059
        },
        {
            "metric": "Coverage of social safety net programs in poorest quintile (% of population)",
            "country": "MNG",
            "value": 99.78409191
        },
        {
            "metric": "Coverage of social safety net programs in richest quintile (% of population)",
            "country": "MNG",
            "value": 99.66760617
        },
        {
            "metric": "Coverage of unemployment benefits and ALMP (% of population)",
            "country": "KGZ",
            "value": 25.79408748
        },
        {
            "metric": "Coverage of unemployment benefits and ALMP in 2nd quintile (% of population)",
            "country": "KGZ",
            "value": 28.78127896
        },
        {
            "metric": "Coverage of unemployment benefits and ALMP in 3rd quintile (% of population)",
            "country": "KGZ",
            "value": 25.7520326
        },
        {
            "metric": "Coverage of unemployment benefits and ALMP in 4th quintile (% of population)",
            "country": "CRI",
            "value": 28.04805582
        },
        {
            "metric": "Coverage of unemployment benefits and ALMP in poorest quintile (% of population)",
            "country": "BGR",
            "value": 25.36885256
        },
        {
            "metric": "Coverage of unemployment benefits and ALMP in richest quintile (% of population)",
            "country": "CHL",
            "value": 29.68546171
        },
        {
            "metric": "Debt service to exports (%)",
            "country": "JAM",
            "value": 24.4127
        },
        {
            "metric": "Demand for family planning satisfied by modern methods (% of married women with demand for family planning)",
            "country": "CHN",
            "value": 96.6
        },
        {
            "metric": "Disaster risk reduction progress score (1-5 scale; 5=best)",
            "country": "ECU",
            "value": 4.75
        },
        {
            "metric": "Droughts, floods, extreme temperatures (% of population, average 1990-2009)",
            "country": "SWZ",
            "value": 9.226586308
        },
        {
            "metric": "Educational attainment, Doctoral or equivalent, population 25+, female (%) (cumulative)",
            "country": "SVN",
            "value": 2.38246
        },
        {
            "metric": "Educational attainment, Doctoral or equivalent, population 25+, male (%) (cumulative)",
            "country": "CHE",
            "value": 4.01876
        },
        {
            "metric": "Educational attainment, Doctoral or equivalent, population 25+, total (%) (cumulative)",
            "country": "CHE",
            "value": 2.90631
        },
        {
            "metric": "Educational attainment, at least Bachelor's or equivalent, population 25+, female (%) (cumulative)",
            "country": "LTU",
            "value": 37.31714
        },
        {
            "metric": "Educational attainment, at least Bachelor's or equivalent, population 25+, male (%) (cumulative)",
            "country": "CHE",
            "value": 44.20801
        },
        {
            "metric": "Educational attainment, at least Bachelor's or equivalent, population 25+, total (%) (cumulative)",
            "country": "CHE",
            "value": 36.94929
        },
        {
            "metric": "Educational attainment, at least Master's or equivalent, population 25+, female (%) (cumulative)",
            "country": "GEO",
            "value": 28.71104
        },
        {
            "metric": "Educational attainment, at least Master's or equivalent, population 25+, male (%) (cumulative)",
            "country": "GEO",
            "value": 27.48961
        },
        {
            "metric": "Educational attainment, at least Master's or equivalent, population 25+, total (%) (cumulative)",
            "country": "GEO",
            "value": 28.15081
        },
        {
            "metric": "Educational attainment, at least completed lower secondary, population 25+, female (%) (cumulative)",
            "country": "LVA",
            "value": 100.0
        },
        {
            "metric": "Educational attainment, at least completed lower secondary, population 25+, male (%) (cumulative)",
            "country": "LVA",
            "value": 100.0
        },
        {
            "metric": "Educational attainment, at least completed lower secondary, population 25+, total (%) (cumulative)",
            "country": "GRL",
            "value": 100.0
        },
        {
            "metric": "Educational attainment, at least completed post-secondary, population 25+, female (%) (cumulative)",
            "country": "LUX",
            "value": 68.17269
        },
        {
            "metric": "Educational attainment, at least completed post-secondary, population 25+, male (%) (cumulative)",
            "country": "LUX",
            "value": 69.93717
        },
        {
            "metric": "Educational attainment, at least completed post-secondary, population 25+, total (%) (cumulative)",
            "country": "LUX",
            "value": 69.07166
        },
        {
            "metric": "Educational attainment, at least completed primary, population 25+ years, male (%) (cumulative)",
            "country": "TJK",
            "value": 100.0
        },
        {
            "metric": "Educational attainment, at least completed short-cycle tertiary, population 25+, female (%) (cumulative)",
            "country": "RUS",
            "value": 63.68967
        },
        {
            "metric": "Educational attainment, at least completed short-cycle tertiary, population 25+, male (%) (cumulative)",
            "country": "UZB",
            "value": 66.59118
        },
        {
            "metric": "Educational attainment, at least completed short-cycle tertiary, population 25+, total (%) (cumulative)",
            "country": "UZB",
            "value": 62.50791
        },
        {
            "metric": "Educational attainment, at least completed upper secondary, population 25+, female (%) (cumulative)",
            "country": "GEO",
            "value": 93.00176
        },
        {
            "metric": "Educational attainment, at least completed upper secondary, population 25+, male (%) (cumulative)",
            "country": "CZE",
            "value": 94.35108
        },
        {
            "metric": "Educational attainment, at least completed upper secondary, population 25+, total (%) (cumulative)",
            "country": "GEO",
            "value": 93.45079
        },
        {
            "metric": "Employment in agriculture (% of total employment) (modeled ILO estimate)",
            "country": "BDI",
            "value": 91.95700073
        },
        {
            "metric": "Employment in agriculture, female (% of female employment) (modeled ILO estimate)",
            "country": "BDI",
            "value": 96.28500366
        },
        {
            "metric": "Employment in agriculture, male (% of male employment) (modeled ILO estimate)",
            "country": "BDI",
            "value": 87.15799713
        },
        {
            "metric": "Employment in industry (% of total employment) (modeled ILO estimate)",
            "country": "QAT",
            "value": 54.49900055
        },
        {
            "metric": "Employment in industry, female (% of female employment) (modeled ILO estimate)",
            "country": "TON",
            "value": 55.03300095
        },
        {
            "metric": "Employment in industry, male (% of male employment) (modeled ILO estimate)",
            "country": "QAT",
            "value": 62.33100128
        },
        {
            "metric": "Employment in services (% of total employment) (modeled ILO estimate)",
            "country": "LUX",
            "value": 88.05400085
        },
        {
            "metric": "Employment in services, female (% of female employment) (modeled ILO estimate)",
            "country": "SAU",
            "value": 97.85600281
        },
        {
            "metric": "Employment in services, male (% of male employment) (modeled ILO estimate)",
            "country": "LUX",
            "value": 81.2460022
        },
        {
            "metric": "Energy intensity level of primary energy (MJ/$2011 PPP GDP)",
            "country": "SOM",
            "value": 40.06923885
        },
        {
            "metric": "Exclusive breastfeeding (% of children under 6 months)",
            "country": "HRV",
            "value": 98.13041391
        },
        {
            "metric": "Exports of goods and services (% of GDP)",
            "country": "LUX",
            "value": 223.0794119
        },
        {
            "metric": "Female genital mutilation prevalence (%)",
            "country": "SOM",
            "value": 97.9
        },
        {
            "metric": "Female share of employment in senior and middle management (%)",
            "country": "SWZ",
            "value": 54.64
        },
        {
            "metric": "Firms expected to give gifts in meetings with tax officials (% of firms)",
            "country": "YEM",
            "value": 62.6
        },
        {
            "metric": "Firms with female participation in ownership (% of firms)",
            "country": "FSM",
            "value": 86.8
        },
        {
            "metric": "Firms with female top manager (% of firms)",
            "country": "THA",
            "value": 64.8
        },
        {
            "metric": "Fish species, threatened",
            "country": "USA",
            "value": 251.0
        },
        {
            "metric": "Foreign direct investment, net inflows (% of GDP)",
            "country": "CYM",
            "value": 773.9001899
        },
        {
            "metric": "Foreign direct investment, net inflows (BoP, current US$)",
            "country": "USA",
            "value": 355000000000.0
        },
        {
            "metric": "Forest area (% of land area)",
            "country": "SUR",
            "value": 98.25769356
        },
        {
            "metric": "Forest area (sq. km)",
            "country": "RUS",
            "value": 8148895.0
        },
        {
            "metric": "Forest rents (% of GDP)",
            "country": "SLB",
            "value": 21.24725537
        },
        {
            "metric": "GDP (constant 2010 US$)",
            "country": "USA",
            "value": 17300000000000.0
        },
        {
            "metric": "GDP (constant LCU)",
            "country": "IDN",
            "value": 9910000000000000.0
        },
        {
            "metric": "GDP (current LCU)",
            "country": "IRN",
            "value": 1.53e+16
        },
        {
            "metric": "GDP (current US$)",
            "country": "USA",
            "value": 19500000000000.0
        },
        {
            "metric": "GDP growth (annual %)",
            "country": "LBY",
            "value": 26.67587012
        },
        {
            "metric": "GDP per capita (constant 2010 US$)",
            "country": "MCO",
            "value": 191586.6396
        },
        {
            "metric": "GDP per capita (constant LCU)",
            "country": "IRN",
            "value": 88412349.76
        },
        {
            "metric": "GDP per capita (current LCU)",
            "country": "IRN",
            "value": 188713699.7
        },
        {
            "metric": "GDP per capita (current US$)",
            "country": "MCO",
            "value": 168010.9149
        },
        {
            "metric": "GDP per capita growth (annual %)",
            "country": "LBY",
            "value": 25.05903095
        },
        {
            "metric": "GDP per capita, PPP (constant 2011 international $)",
            "country": "QAT",
            "value": 116931.9863
        },
        {
            "metric": "GDP per capita, PPP (current international $)",
            "country": "QAT",
            "value": 128646.7602
        },
        {
            "metric": "GDP per person employed (constant 2011 PPP $)",
            "country": "LUX",
            "value": 216165.3906
        },
        {
            "metric": "GDP, PPP (constant 2011 international $)",
            "country": "CHN",
            "value": 21200000000000.0
        },
        {
            "metric": "GDP, PPP (current international $)",
            "country": "CHN",
            "value": 23400000000000.0
        },
        {
            "metric": "GNI (constant 2010 US$)",
            "country": "USA",
            "value": 17500000000000.0
        },
        {
            "metric": "GNI (constant LCU)",
            "country": "IDN",
            "value": 9600000000000000.0
        },
        {
            "metric": "GNI per capita (US$)",
            "country": "LIE",
            "value": 156961.634
        },
        {
            "metric": "GNI per capita (constant 2010 US$)",
            "country": "LIE",
            "value": 119043.7868
        },
        {
            "metric": "GNI per capita (constant LCU)",
            "country": "IRN",
            "value": 88546026.41
        },
        {
            "metric": "GNI per capita (current LCU)",
            "country": "IRN",
            "value": 189064882.8
        },
        {
            "metric": "GNI per capita growth (annual %)",
            "country": "SLE",
            "value": 10.81798936
        },
        {
            "metric": "GNI per capita, Atlas method (current US$)",
            "country": "LIE",
            "value": 116300.0
        },
        {
            "metric": "GNI per capita, PPP (constant 2011 international $)",
            "country": "QAT",
            "value": 116799.065
        },
        {
            "metric": "GNI per capita, PPP (current international $)",
            "country": "QAT",
            "value": 128320.0
        },
        {
            "metric": "GNI, PPP (constant 2011 international $)",
            "country": "CHN",
            "value": 21200000000000.0
        },
        {
            "metric": "GNI, PPP (current international $)",
            "country": "CHN",
            "value": 23300000000000.0
        },
        {
            "metric": "Immunization, DPT (% of children ages 12-23 months)",
            "country": "LKA",
            "value": 99.0
        },
        {
            "metric": "Immunization, HepB3 (% of one-year-old children)",
            "country": "SLB",
            "value": 99.0
        },
        {
            "metric": "Immunization, measles (% of children ages 12-23 months)",
            "country": "OMN",
            "value": 99.0
        },
        {
            "metric": "Incidence of HIV (% of uninfected population ages 15-49)",
            "country": "LSO",
            "value": 1.61
        },
        {
            "metric": "Incidence of malaria (per 1,000 population at risk)",
            "country": "RWA",
            "value": 505.57
        },
        {
            "metric": "Incidence of tuberculosis (per 100,000 people)",
            "country": "LSO",
            "value": 665.0
        },
        {
            "metric": "Individuals using the Internet (% of population)",
            "country": "AND",
            "value": 98.87143552
        },
        {
            "metric": "Industry, value added per worker (constant 2010 US$)",
            "country": "NOR",
            "value": 302462.9476
        },
        {
            "metric": "Informal employment (% of total non-agricultural employment)",
            "country": "NPL",
            "value": 99.01000214
        },
        {
            "metric": "Informal employment, female (% of total non-agricultural employment)",
            "country": "NPL",
            "value": 99.44000244
        },
        {
            "metric": "Informal employment, male (% of total non-agricultural employment)",
            "country": "NPL",
            "value": 98.81999969
        },
        {
            "metric": "Intentional homicides (per 100,000 people)",
            "country": "SLV",
            "value": 82.8422575
        },
        {
            "metric": "Intentional homicides, female (per 100,000 female)",
            "country": "SLV",
            "value": 15.69071084
        },
        {
            "metric": "Intentional homicides, male (per 100,000 male)",
            "country": "SLV",
            "value": 158.4169008
        },
        {
            "metric": "Investment in energy with private participation (current US$)",
            "country": "IDN",
            "value": 8819500000.0
        },
        {
            "metric": "Investment in transport with private participation (current US$)",
            "country": "CHN",
            "value": 12587440000.0
        },
        {
            "metric": "Investment in water and sanitation with private participation (current US$)",
            "country": "MYS",
            "value": 2521000000.0
        },
        {
            "metric": "Level of water stress: freshwater withdrawal as a proportion of available freshwater resources",
            "country": "KWT",
            "value": 2603.487042
        },
        {
            "metric": "Literacy rate, adult female (% of females ages 15 and above)",
            "country": "PRK",
            "value": 99.997612
        },
        {
            "metric": "Literacy rate, adult male (% of males ages 15 and above)",
            "country": "PRK",
            "value": 99.99887848
        },
        {
            "metric": "Literacy rate, adult total (% of people ages 15 and above)",
            "country": "PRK",
            "value": 99.99819183
        },
        {
            "metric": "Literacy rate, youth (ages 15-24), gender parity index (GPI)",
            "country": "LSO",
            "value": 1.180410028
        },
        {
            "metric": "Literacy rate, youth female (% of females ages 15-24)",
            "country": "UZB",
            "value": 100.0
        },
        {
            "metric": "Literacy rate, youth male (% of males ages 15-24)",
            "country": "UZB",
            "value": 100.0
        },
        {
            "metric": "Literacy rate, youth total (% of people ages 15-24)",
            "country": "UZB",
            "value": 100.0
        },
        {
            "metric": "Lower secondary completion rate, female (% of relevant age group)",
            "country": "MHL",
            "value": 133.9321442
        },
        {
            "metric": "Lower secondary completion rate, male (% of relevant age group)",
            "country": "MHL",
            "value": 133.6397095
        },
        {
            "metric": "Lower secondary completion rate, total (% of relevant age group)",
            "country": "MHL",
            "value": 133.7799072
        },
        {
            "metric": "Mammal species, threatened",
            "country": "IDN",
            "value": 191.0
        },
        {
            "metric": "Manufacturing, value added (% of GDP)",
            "country": "PRI",
            "value": 48.15733468
        },
        {
            "metric": "Manufacturing, value added (current US$)",
            "country": "CHN",
            "value": 3590000000000.0
        },
        {
            "metric": "Marine protected areas (% of territorial waters)",
            "country": "SVN",
            "value": 100.0
        },
        {
            "metric": "Maternal mortality ratio (modeled estimate, per 100,000 live births)",
            "country": "SLE",
            "value": 1360.0
        },
        {
            "metric": "Medium and high-tech industry (% manufacturing value added)",
            "country": "SGP",
            "value": 80.37858277
        },
        {
            "metric": "Methodology assessment of statistical capacity (scale 0 - 100)",
            "country": "IND",
            "value": 100.0
        },
        {
            "metric": "Mineral rents (% of GDP)",
            "country": "MNG",
            "value": 28.76658855
        },
        {
            "metric": "Mortality caused by road traffic injury (per 100,000 people)",
            "country": "ZWE",
            "value": 45.4
        },
        {
            "metric": "Mortality from CVD, cancer, diabetes or CRD between exact ages 30 and 70 (%)",
            "country": "FJI",
            "value": 30.6
        },
        {
            "metric": "Mortality from CVD, cancer, diabetes or CRD between exact ages 30 and 70, female (%)",
            "country": "SLE",
            "value": 32.6
        },
        {
            "metric": "Mortality from CVD, cancer, diabetes or CRD between exact ages 30 and 70, male (%)",
            "country": "MNG",
            "value": 38.8
        },
        {
            "metric": "Mortality rate attributed to household and ambient air pollution, age-standardized (per 100,000 population)",
            "country": "SLE",
            "value": 324.1
        },
        {
            "metric": "Mortality rate attributed to household and ambient air pollution, age-standardized, female (per 100,000 female population)",
            "country": "SLE",
            "value": 333.0
        },
        {
            "metric": "Mortality rate attributed to household and ambient air pollution, age-standardized, male (per 100,000 male population)",
            "country": "SLE",
            "value": 314.0
        },
        {
            "metric": "Mortality rate attributed to unintentional poisoning (per 100,000 population)",
            "country": "BDI",
            "value": 5.2
        },
        {
            "metric": "Mortality rate attributed to unintentional poisoning, female (per 100,000 female population)",
            "country": "PAK",
            "value": 3.9
        },
        {
            "metric": "Mortality rate attributed to unintentional poisoning, male (per 100,000 male population)",
            "country": "BDI",
            "value": 6.8
        },
        {
            "metric": "Mortality rate attributed to unsafe water, unsafe sanitation and lack of hygiene (per 100,000 population)",
            "country": "TCD",
            "value": 101.0
        },
        {
            "metric": "Mortality rate, neonatal (per 1,000 live births)",
            "country": "PAK",
            "value": 44.2
        },
        {
            "metric": "Mortality rate, under-5 (per 1,000 live births)",
            "country": "SOM",
            "value": 127.2
        },
        {
            "metric": "Mortality rate, under-5, female (per 1,000 live births)",
            "country": "SOM",
            "value": 120.5
        },
        {
            "metric": "Mortality rate, under-5, male (per 1,000 live births)",
            "country": "SOM",
            "value": 133.2
        },
        {
            "metric": "Natural gas rents (% of GDP)",
            "country": "TLS",
            "value": 16.78138921
        },
        {
            "metric": "Net official development assistance and official aid received (current US$)",
            "country": "SYR",
            "value": 10360840000.0
        },
        {
            "metric": "Net official development assistance received (constant 2016 US$)",
            "country": "SYR",
            "value": 11154560000.0
        },
        {
            "metric": "Net official development assistance received (current US$)",
            "country": "SYR",
            "value": 10360840000.0
        },
        {
            "metric": "New business density (new registrations per 1,000 people ages 15-64)",
            "country": "VIR",
            "value": 2604.762166
        },
        {
            "metric": "Nondiscrimination clause mentions gender in the constitution (1=yes; 0=no)",
            "country": "HUN",
            "value": 1.0
        },
        {
            "metric": "Number of people spending more than 10% of household consumption or income on out-of-pocket health care expenditure",
            "country": "CHN",
            "value": 233000000.0
        },
        {
            "metric": "Number of people spending more than 25% of household consumption or income on out-of-pocket health care expenditure",
            "country": "CHN",
            "value": 62700000.0
        },
        {
            "metric": "Nurses and midwives (per 1,000 people)",
            "country": "MCO",
            "value": 20.521
        },
        {
            "metric": "Oil rents (% of GDP)",
            "country": "IRQ",
            "value": 37.78234421
        },
        {
            "metric": "Over-age students, primary (% of enrollment)",
            "country": "LBR",
            "value": 60.33498001
        },
        {
            "metric": "Over-age students, primary, female (% of female enrollment)",
            "country": "LBR",
            "value": 58.68336105
        },
        {
            "metric": "Over-age students, primary, male (% of male enrollment)",
            "country": "LBR",
            "value": 59.99531174
        },
        {
            "metric": "Overall level of statistical capacity (scale 0 - 100)",
            "country": "MEX",
            "value": 96.66666667
        },
        {
            "metric": "PM2.5 air pollution, mean annual exposure (micrograms per cubic meter)",
            "country": "NPL",
            "value": 99.73437372
        },
        {
            "metric": "PM2.5 air pollution, population exposed to levels exceeding WHO guideline value (% of total)",
            "country": "MLI",
            "value": 100.0
        },
        {
            "metric": "PM2.5 pollution, population exposed to levels exceeding WHO Interim Target-1 value (% of total)",
            "country": "GNQ",
            "value": 100.0
        },
        {
            "metric": "PM2.5 pollution, population exposed to levels exceeding WHO Interim Target-2 value (% of total)",
            "country": "GNB",
            "value": 100.0
        },
        {
            "metric": "PM2.5 pollution, population exposed to levels exceeding WHO Interim Target-3 value (% of total)",
            "country": "SWZ",
            "value": 100.0
        },
        {
            "metric": "PPP conversion factor, GDP (LCU per international $)",
            "country": "STP",
            "value": 12437.17021
        },
        {
            "metric": "PPP conversion factor, private consumption (LCU per international $)",
            "country": "STP",
            "value": 14041.15404
        },
        {
            "metric": "Patent applications, nonresidents",
            "country": "USA",
            "value": 313052.0
        },
        {
            "metric": "Patent applications, residents",
            "country": "CHN",
            "value": 1245709.0
        },
        {
            "metric": "People practicing open defecation (% of population)",
            "country": "ERI",
            "value": 76.0298725
        },
        {
            "metric": "People practicing open defecation, rural (% of rural population)",
            "country": "ERI",
            "value": 88.65
        },
        {
            "metric": "People practicing open defecation, urban (% of urban population)",
            "country": "STP",
            "value": 42.82070956
        },
        {
            "metric": "People using at least basic drinking water services (% of population)",
            "country": "KWT",
            "value": 100.0
        },
        {
            "metric": "People using at least basic drinking water services, rural (% of rural population)",
            "country": "ESP",
            "value": 100.0
        },
        {
            "metric": "People using at least basic drinking water services, urban (% of urban population)",
            "country": "FRA",
            "value": 100.0
        },
        {
            "metric": "People using at least basic sanitation services (% of population)",
            "country": "QAT",
            "value": 100.0
        },
        {
            "metric": "People using at least basic sanitation services, rural (% of rural population)",
            "country": "MLT",
            "value": 100.0
        },
        {
            "metric": "People using at least basic sanitation services, urban (% of urban population)",
            "country": "NZL",
            "value": 100.0
        },
        {
            "metric": "People using safely managed drinking water services (% of population)",
            "country": "LIE",
            "value": 100.0
        },
        {
            "metric": "People using safely managed drinking water services, rural (% of rural population)",
            "country": "ISR",
            "value": 99.39
        },
        {
            "metric": "People using safely managed drinking water services, urban (% of urban population)",
            "country": "MCO",
            "value": 100.0
        },
        {
            "metric": "People using safely managed sanitation services (% of population)",
            "country": "KWT",
            "value": 100.0
        },
        {
            "metric": "People using safely managed sanitation services, rural (% of rural population)",
            "country": "AND",
            "value": 100.0
        },
        {
            "metric": "People using safely managed sanitation services, urban (% of urban population)",
            "country": "AND",
            "value": 100.0
        },
        {
            "metric": "People with basic handwashing facilities including soap and water (% of population)",
            "country": "SRB",
            "value": 97.71855
        },
        {
            "metric": "People with basic handwashing facilities including soap and water, rural (% of rural population)",
            "country": "SRB",
            "value": 97.55205
        },
        {
            "metric": "People with basic handwashing facilities including soap and water, urban (% of urban population)",
            "country": "TKM",
            "value": 98.61944
        },
        {
            "metric": "Periodicity and timeliness assessment of statistical capacity (scale 0 - 100)",
            "country": "BOL",
            "value": 100.0
        },
        {
            "metric": "Personal remittances, received (% of GDP)",
            "country": "SSD",
            "value": 37.29191289
        },
        {
            "metric": "Physicians (per 1,000 people)",
            "country": "CUB",
            "value": 7.519
        },
        {
            "metric": "Plant species (higher), threatened",
            "country": "ECU",
            "value": 1859.0
        },
        {
            "metric": "Population living in slums (% of urban population)",
            "country": "SSD",
            "value": 95.6
        },
        {
            "metric": "Poverty headcount ratio at $1.90 a day (2011 PPP) (% of population)",
            "country": "MDG",
            "value": 77.6
        },
        {
            "metric": "Poverty headcount ratio at national poverty lines (% of population)",
            "country": "SSD",
            "value": 82.3
        },
        {
            "metric": "Preprimary education, duration (years)",
            "country": "HUN",
            "value": 4.0
        },
        {
            "metric": "Prevalence of HIV, female (% ages 15-24)",
            "country": "SWZ",
            "value": 16.7
        },
        {
            "metric": "Prevalence of HIV, male (% ages 15-24)",
            "country": "BWA",
            "value": 5.6
        },
        {
            "metric": "Prevalence of HIV, total (% of population ages 15-49)",
            "country": "SWZ",
            "value": 27.4
        },
        {
            "metric": "Prevalence of anemia among women of reproductive age (% of women ages 15-49)",
            "country": "YEM",
            "value": 69.6
        },
        {
            "metric": "Prevalence of overweight, weight for height (% of children under 5)",
            "country": "UKR",
            "value": 26.5
        },
        {
            "metric": "Prevalence of overweight, weight for height, female (% of children under 5)",
            "country": "UKR",
            "value": 25.5
        },
        {
            "metric": "Prevalence of overweight, weight for height, male (% of children under 5)",
            "country": "UKR",
            "value": 27.29999924
        },
        {
            "metric": "Prevalence of severe wasting, weight for height (% of children under 5)",
            "country": "SSD",
            "value": 9.9
        },
        {
            "metric": "Prevalence of severe wasting, weight for height, female (% of children under 5)",
            "country": "SSD",
            "value": 8.100000381
        },
        {
            "metric": "Prevalence of severe wasting, weight for height, male (% of children under 5)",
            "country": "SSD",
            "value": 11.69999981
        },
        {
            "metric": "Prevalence of stunting, height for age (% of children under 5)",
            "country": "BDI",
            "value": 55.9
        },
        {
            "metric": "Prevalence of stunting, height for age, female (% of children under 5)",
            "country": "AFG",
            "value": 58.5
        },
        {
            "metric": "Prevalence of stunting, height for age, male (% of children under 5)",
            "country": "BDI",
            "value": 61.70000076
        },
        {
            "metric": "Prevalence of undernourishment (% of population)",
            "country": "CAF",
            "value": 61.8
        },
        {
            "metric": "Prevalence of underweight, weight for age (% of children under 5)",
            "country": "ERI",
            "value": 38.8
        },
        {
            "metric": "Prevalence of underweight, weight for age, female (% of children under 5)",
            "country": "ERI",
            "value": 39.40000153
        },
        {
            "metric": "Prevalence of underweight, weight for age, male (% of children under 5)",
            "country": "YEM",
            "value": 40.90000153
        },
        {
            "metric": "Prevalence of wasting, weight for height (% of children under 5)",
            "country": "SSD",
            "value": 22.7
        },
        {
            "metric": "Prevalence of wasting, weight for height, female (% of children under 5)",
            "country": "LKA",
            "value": 20.5
        },
        {
            "metric": "Prevalence of wasting, weight for height, male (% of children under 5)",
            "country": "SSD",
            "value": 25.70000076
        },
        {
            "metric": "Primary completion rate, female (% of relevant age group)",
            "country": "BGD",
            "value": 122.9727478
        },
        {
            "metric": "Primary completion rate, male (% of relevant age group)",
            "country": "SAU",
            "value": 120.615097
        },
        {
            "metric": "Primary completion rate, total (% of relevant age group)",
            "country": "NRU",
            "value": 120.4255295
        },
        {
            "metric": "Primary education, duration (years)",
            "country": "GUM",
            "value": 8.0
        },
        {
            "metric": "Primary government expenditures as a proportion of original approved budget (%)",
            "country": "GHA",
            "value": 135.1028783
        },
        {
            "metric": "Proportion of population spending more than 10% of household consumption or income on out-of-pocket health care expenditure (%)",
            "country": "LBN",
            "value": 44.85168
        },
        {
            "metric": "Proportion of population spending more than 25% of household consumption or income on out-of-pocket health care expenditure (%)",
            "country": "CHL",
            "value": 11.51748
        },
        {
            "metric": "Proportion of seats held by women in national parliaments (%)",
            "country": "RWA",
            "value": 61.3
        },
        {
            "metric": "Proportion of time spent on unpaid domestic and care work, female (% of 24 hour day)",
            "country": "MEX",
            "value": 29.5219895
        },
        {
            "metric": "Proportion of time spent on unpaid domestic and care work, male (% of 24 hour day)",
            "country": "SWE",
            "value": 12.8279713
        },
        {
            "metric": "Proportion of women subjected to physical and/or sexual violence in the last 12 months (% of women age 15-49)",
            "country": "AFG",
            "value": 46.1
        },
        {
            "metric": "Pupil-teacher ratio, lower secondary",
            "country": "BDI",
            "value": 54.32767868
        },
        {
            "metric": "Pupil-teacher ratio, preprimary",
            "country": "TZA",
            "value": 113.9653015
        },
        {
            "metric": "Pupil-teacher ratio, primary",
            "country": "CAF",
            "value": 83.41194916
        },
        {
            "metric": "Pupil-teacher ratio, secondary",
            "country": "ETH",
            "value": 40.35063934
        },
        {
            "metric": "Pupil-teacher ratio, tertiary",
            "country": "GNB",
            "value": 147.5599976
        },
        {
            "metric": "Pupil-teacher ratio, upper secondary",
            "country": "PNG",
            "value": 83.26217651
        },
        {
            "metric": "Railways, goods transported (million ton-km)",
            "country": "RUS",
            "value": 2491875.9
        },
        {
            "metric": "Railways, passengers carried (million passenger-km)",
            "country": "IND",
            "value": 1149835.0
        },
        {
            "metric": "Renewable electricity output (% of total electricity output)",
            "country": "ALB",
            "value": 100.0
        },
        {
            "metric": "Renewable energy consumption (% of total final energy consumption)",
            "country": "COD",
            "value": 95.81769971
        },
        {
            "metric": "Renewable internal freshwater resources per capita (cubic meters)",
            "country": "GRL",
            "value": 10662187.25
        },
        {
            "metric": "Renewable internal freshwater resources, total (billion cubic meters)",
            "country": "BRA",
            "value": 5661.0
        },
        {
            "metric": "Research and development expenditure (% of GDP)",
            "country": "ISR",
            "value": 4.25121
        },
        {
            "metric": "Researchers in R&D (per million people)",
            "country": "ISR",
            "value": 8250.47418
        },
        {
            "metric": "Rural poverty headcount ratio at national poverty lines (% of rural population)",
            "country": "ZAF",
            "value": 87.6
        },
        {
            "metric": "School enrollment, preprimary (% gross)",
            "country": "AUS",
            "value": 166.3574829
        },
        {
            "metric": "School enrollment, preprimary, female (% gross)",
            "country": "AUS",
            "value": 162.9355164
        },
        {
            "metric": "School enrollment, preprimary, male (% gross)",
            "country": "AUS",
            "value": 169.6057434
        },
        {
            "metric": "School enrollment, primary (gross), gender parity index (GPI)",
            "country": "IND",
            "value": 1.166980028
        },
        {
            "metric": "School enrollment, primary and secondary (gross), gender parity index (GPI)",
            "country": "SEN",
            "value": 1.134189963
        },
        {
            "metric": "School enrollment, secondary (gross), gender parity index (GPI)",
            "country": "LSO",
            "value": 1.357069969
        },
        {
            "metric": "School enrollment, tertiary (% gross)",
            "country": "GRC",
            "value": 126.3826218
        },
        {
            "metric": "School enrollment, tertiary (gross), gender parity index (GPI)",
            "country": "QAT",
            "value": 7.750360012
        },
        {
            "metric": "School enrollment, tertiary, female (% gross)",
            "country": "AUS",
            "value": 134.080719
        },
        {
            "metric": "School enrollment, tertiary, male (% gross)",
            "country": "GRC",
            "value": 127.3533325
        },
        {
            "metric": "Secondary education, duration (years)",
            "country": "DEU",
            "value": 9.0
        },
        {
            "metric": "Services, value added per worker (constant 2010 US$)",
            "country": "LUX",
            "value": 204469.6991
        },
        {
            "metric": "Share of youth not in education, employment or training, female (% of female youth population)",
            "country": "YEM",
            "value": 69.69020081
        },
        {
            "metric": "Share of youth not in education, employment or training, male (% of male youth population)",
            "country": "KIR",
            "value": 46.18999863
        },
        {
            "metric": "Share of youth not in education, employment or training, total (% of youth population)",
            "country": "TTO",
            "value": 52.04999924
        },
        {
            "metric": "Smoking prevalence, females (% of adults)",
            "country": "MNE",
            "value": 44.0
        },
        {
            "metric": "Smoking prevalence, males (% of adults)",
            "country": "TLS",
            "value": 78.1
        },
        {
            "metric": "Source data assessment of statistical capacity (scale 0 - 100)",
            "country": "MEX",
            "value": 100.0
        },
        {
            "metric": "Suicide mortality rate (per 100,000 population)",
            "country": "LTU",
            "value": 31.9
        },
        {
            "metric": "Suicide mortality rate, female (per 100,000 female population)",
            "country": "LSO",
            "value": 24.4
        },
        {
            "metric": "Suicide mortality rate, male (per 100,000 male population)",
            "country": "LTU",
            "value": 58.1
        },
        {
            "metric": "Tariff rate, applied, simple mean, all products (%)",
            "country": "BHS",
            "value": 26.78
        },
        {
            "metric": "Tariff rate, applied, simple mean, manufactured products (%)",
            "country": "BHS",
            "value": 28.5
        },
        {
            "metric": "Tariff rate, applied, simple mean, primary products (%)",
            "country": "CYM",
            "value": 32.47
        },
        {
            "metric": "Tariff rate, applied, weighted mean, all products (%)",
            "country": "PLW",
            "value": 29.88
        },
        {
            "metric": "Tariff rate, applied, weighted mean, manufactured products (%)",
            "country": "BHS",
            "value": 25.74
        },
        {
            "metric": "Tariff rate, applied, weighted mean, primary products (%)",
            "country": "CYM",
            "value": 34.32
        },
        {
            "metric": "Tax revenue (% of GDP)",
            "country": "DZA",
            "value": 37.18473614
        },
        {
            "metric": "Tax revenue (current LCU)",
            "country": "IDN",
            "value": 1340000000000000.0
        },
        {
            "metric": "Terrestrial and marine protected areas (% of total territorial area)",
            "country": "MCO",
            "value": 99.4595712
        },
        {
            "metric": "Terrestrial protected areas (% of total land area)",
            "country": "NCL",
            "value": 54.40415763
        },
        {
            "metric": "Total alcohol consumption per capita (liters of pure alcohol, projected estimates, 15+ years of age)",
            "country": "MDA",
            "value": 15.2
        },
        {
            "metric": "Total alcohol consumption per capita, female (liters of pure alcohol, projected estimates, female 15+ years of age)",
            "country": "LTU",
            "value": 6.9
        },
        {
            "metric": "Total alcohol consumption per capita, male (liters of pure alcohol, projected estimates, male 15+ years of age)",
            "country": "MDA",
            "value": 25.2
        },
        {
            "metric": "Total fisheries production (metric tons)",
            "country": "CHN",
            "value": 81500000.0
        },
        {
            "metric": "Total natural resources rents (% of GDP)",
            "country": "COG",
            "value": 42.66827703
        },
        {
            "metric": "Trained teachers in lower secondary education (% of total teachers)",
            "country": "NRU",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in lower secondary education, female (% of female teachers)",
            "country": "CUB",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in lower secondary education, male (% of male teachers)",
            "country": "BDI",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in preprimary education (% of total teachers)",
            "country": "MHL",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in preprimary education, female (% of female teachers)",
            "country": "SUR",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in preprimary education, male (% of male teachers)",
            "country": "MAR",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in primary education (% of total teachers)",
            "country": "CUB",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in primary education, female (% of female teachers)",
            "country": "MAR",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in primary education, male (% of male teachers)",
            "country": "ZMB",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in secondary education (% of total teachers)",
            "country": "KAZ",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in secondary education, female (% of female teachers)",
            "country": "SAU",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in secondary education, male (% of male teachers)",
            "country": "MAR",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in upper secondary education (% of total teachers)",
            "country": "SRB",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in upper secondary education, female (% of female teachers)",
            "country": "SRB",
            "value": 100.0
        },
        {
            "metric": "Trained teachers in upper secondary education, male (% of male teachers)",
            "country": "GMB",
            "value": 100.0
        },
        {
            "metric": "Unemployment, female (% of female labor force) (modeled ILO estimate)",
            "country": "PSE",
            "value": 50.75600052
        },
        {
            "metric": "Unemployment, female (% of female labor force) (national estimate)",
            "country": "PSE",
            "value": 51.23379898
        },
        {
            "metric": "Unemployment, male (% of male labor force) (modeled ILO estimate)",
            "country": "ZAF",
            "value": 25.04700089
        },
        {
            "metric": "Unemployment, male (% of male labor force) (national estimate)",
            "country": "LSO",
            "value": 32.54000092
        },
        {
            "metric": "Unemployment, total (% of total labor force) (modeled ILO estimate)",
            "country": "PSE",
            "value": 30.18199921
        },
        {
            "metric": "Unemployment, total (% of total labor force) (national estimate)",
            "country": "PSE",
            "value": 30.83979988
        },
        {
            "metric": "Unemployment, youth female (% of female labor force ages 15-24) (modeled ILO estimate)",
            "country": "PSE",
            "value": 72.3789978
        },
        {
            "metric": "Unemployment, youth female (% of female labor force ages 15-24) (national estimate)",
            "country": "PSE",
            "value": 75.28780365
        },
        {
            "metric": "Unemployment, youth male (% of male labor force ages 15-24) (modeled ILO estimate)",
            "country": "ZAF",
            "value": 48.15599823
        },
        {
            "metric": "Unemployment, youth male (% of male labor force ages 15-24) (national estimate)",
            "country": "ZAF",
            "value": 49.17570114
        },
        {
            "metric": "Unemployment, youth total (% of total labor force ages 15-24) (modeled ILO estimate)",
            "country": "ZAF",
            "value": 52.85300064
        },
        {
            "metric": "Unemployment, youth total (% of total labor force ages 15-24) (national estimate)",
            "country": "MHL",
            "value": 62.63999939
        },
        {
            "metric": "Urban population",
            "country": "CHN",
            "value": 803554542.0
        },
        {
            "metric": "Urban population (% of total)",
            "country": "SGP",
            "value": 100.0
        },
        {
            "metric": "Urban population growth (annual %)",
            "country": "OMN",
            "value": 5.945861593
        },
        {
            "metric": "Urban poverty headcount ratio at national poverty lines (% of urban population)",
            "country": "ERI",
            "value": 62.0
        },
        {
            "metric": "Wage and salaried workers, female (% of female employment) (modeled ILO estimate)",
            "country": "QAT",
            "value": 99.58999634
        },
        {
            "metric": "Wage and salaried workers, male (% of male employment) (modeled ILO estimate)",
            "country": "QAT",
            "value": 99.58999634
        },
        {
            "metric": "Wage and salaried workers, total (% of total employment) (modeled ILO estimate)",
            "country": "QAT",
            "value": 99.58999634
        },
        {
            "metric": "Water productivity, total (constant 2010 US$ GDP per cubic meter of total freshwater withdrawal)",
            "country": "LUX",
            "value": 1307.615973
        },
        {
            "metric": "Women making their own informed decisions regarding sexual relations, contraceptive use and reproductive health care  (% of women age 15-49)",
            "country": "UKR",
            "value": 81.0
        },
        {
            "metric": "Women who were first married by age 15 (% of women ages 20-24)",
            "country": "TCD",
            "value": 29.7
        },
        {
            "metric": "Women who were first married by age 18 (% of women ages 20-24)",
            "country": "NER",
            "value": 76.3
        }
    ],
    "order": "DESC",
    "strategy": "absolute",
    "query": "\n      MATCH (c:Country)-[r:MEASURED]->(m:Metric)\n      WITH c, m, MAX(r.year) AS lastYear\n\n      MATCH (c)-[last:MEASURED {year: lastYear}]->(m)\n      WITH c, m, toFloat(last.value) AS lastValue\n      ORDER BY m.name, lastValue DESC\n\n      WITH m.name AS metric, COLLECT({country: c.code, value: lastValue }) AS countryChanges\n      RETURN metric, countryChanges[0].country AS country, countryChanges[0].value AS value\n      ORDER BY metric\n      "
}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# En su opinión, ¿Cuáles serían los 10 países a tomar como referencia?
# En su opinión, ¿Cuáles serían los 10 países donde más oportunidad hay? Y ¿qué les beneficiaría más?
@app.get("/api/metrics/top-countries")
async def get_top_countries(order: Optional[str] = "DESC"):
    if order.upper() not in ["ASC", "DESC"]:
        raise HTTPException(status_code=400, detail="Invalid ordering")

    query = f"""
    MATCH (:Country)-[measured:MEASURED]->(metric:Metric)
    WHERE measured.value IS NOT NULL
    WITH metric, toFloat(measured.value) AS numericValue

    WITH metric,
      min(numericValue) AS minValue,
      max(numericValue) AS maxValue

    CALL {{
      WITH metric, minValue, maxValue

      MATCH (c:Country)-[m:MEASURED]->(metric)
      WHERE m.value IS NOT NULL
      WITH c, metric, toFloat(m.value) AS value, minValue, maxValue,

      RETURN c, metric AS met, ((value - minValue) / (maxValue - minValue)) AS normalizedValue
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
                "order": order.upper(),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
