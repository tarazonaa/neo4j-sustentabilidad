# Ecology Hackathon 🤖🍃

## Introducción

Se nos ha pedido que respondamos a las siguiente preguntas a través de queries de `Cypher`:

1. ¿En qué regiones se ha avanzado / retrocedido por métrica en mayor / menor medida?
2. ¿Qué países han avanzado / retrocedido comparado vs otros en su región?
3. ¿Qué métricas son las que más han avanzado / retrocedido globalmente?
4. Estos insights, ¿varían dependiendo del income group?
5. En su opinión, ¿Cuáles serían los 10 países a tomar como referencia?
6. En su opinión, ¿Cuáles serían los 10 países donde más oportunidad hay? Y ¿qué les beneficiaría más?
7. **Bono**: La distancia entre países, ¿afecta en algo los resultados? Por ejemplo, ¿la cercanía a un país con malas metricas perjudica las mías?

Junto con la capacitación que se nos fue proporcionada con Cypher, y con recursos externos, se pudieron responder las preguntas a base de queries de `Cypher`.

## Queries

Nuestras queries para responder a las siguientes preguntas fueron las siguientes:

### 1. ¿En qué regiones se ha avanzado / retrocedido por métrica en mayor / menor medida?

```cypher
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
```

### 2. ¿Qué países han avanzado / retrocedido comparado vs otros en su región?

"Relative" Strategy:

```cypher
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
```

"Absolute" Strategy:

```cypher
MATCH (c:Country)-[r:MEASURED]->(m:Metric)
WITH c, m, MAX(r.year) AS lastYear

MATCH (c)-[last:MEASURED {{year: lastYear}}]->(m)
WITH c, m, toFloat(last.value) AS lastValue
ORDER BY m.name, lastValue {order.upper()}

WITH m.name AS metric, COLLECT({{country: c.code, value: lastValue * m.multiplier}}) AS countryChanges
RETURN metric, countryChanges[0].country AS country, countryChanges[0].value AS value
ORDER BY metric
```

### 3. ¿Qué métricas son las que más han avanzado / retrocedido globalmente?

```cypher

```

### 4. Estos insights, ¿varían dependiendo del income group?

```cypher

```

### 5. En su opinión, ¿Cuáles serían los 10 países a tomar como referencia?

Aquí, usamos una variable `order.uuper() = "DESC"`, donde ordenamos por "asc" o "desc:

```cypher
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
```

### 6. En su opinión, ¿Cuáles serían los 10 países donde más oportunidad hay? Y ¿qué les beneficiaría más?

En esta se usa `order.upper() = ASC`

```cypher
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
```

### 7. **Bono**: La distancia entre países, ¿afecta en algo los resultados? Por ejemplo, ¿la cercanía a un país con malas metricas perjudica las mías?

En esta pregunta, decidimos usar el promedio de cambio de cada pais para TODAS las metricas, y escoger 3 de en medio, 3 de los más bajos, y 3 de los más altos. Después de tener estos tres paises, se hace un `CALL apoc.path.subgraphNodes()` que regresa los paises cercanos a los iniciales a través de si relación `:NEIGHBORS`. Después se regresa el cambio porcentual de los mismos. 

```cypher
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
WHERE NOT isnan(yearly_percentage_change) AND NOT yearly_percentage_change = 'Infinity'
WITH main, neighbor, AVG(yearly_percentage_change) AS neighbor_avg_percentage_change

RETURN main.country AS main_country, main.avg_percentage_change AS main_avg_percentage_change,
       neighbor.name AS neighbor_country, neighbor_avg_percentage_change
ORDER BY main_country, neighbor_avg_percentage_change DESC
```

Probablemente podríamos haber guardado en Python el resultado de los porcentajes y solamente indexarlo una vez que regresemos la respuesta, pero con puro Cypher, esta parece ser la solución.
