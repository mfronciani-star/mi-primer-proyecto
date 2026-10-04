# Resolución · Práctica 1 — Ingesta y capa Bronze

- Nombre: Maxi Fronciani
- student_id: maxi_fronciani
- Escala usada: small
- Esquema: workspace.bigdata_maxi_fronciani
- Volumen: landing

## Tablas Bronze generadas

| Tabla | Filas |
|---|---|
| bronze_customers | 5,000 |
| bronze_products | 500 |
| bronze_transactions | 50,011 |
| bronze_events | 200,000 |

## Diagnóstico de calidad (bronze_transactions)

| rows | distinct_ids | invalid_amounts |
|---|---|---|
| 50,011 | 50,000 | 52 |

Hay 11 transacciones con transaction_id duplicado y 52 importes que no se pueden convertir a DECIMAL(12,2). Siguiendo el criterio de la arquitectura medallion, en Bronze no se corrigen: se registran y se resuelven en Silver.

## Observaciones sobre formatos

1. CSV/JSON: son formatos de texto sin tipos. Al leer el CSV de transacciones, amount queda como string. Incluso con inferSchema=true, los valores inválidos impiden tratarla como numérica, y además inferir obliga a recorrer los datos una vez más antes de la lectura real. JSON permite estructuras anidadas y campos que varían entre registros.
2. Parquet: es un formato columnar que guarda el esquema y los tipos dentro del archivo. Se lee sin inferencia y es más eficiente para consultas que usan pocas columnas.
3. Delta: agrega sobre Parquet un log de transacciones. Eso permite consultar el historial de cambios (DESCRIBE HISTORY), los metadatos de la tabla (DESCRIBE DETAIL), hacer escrituras atómicas y controlar el esquema, cosas que un directorio Parquet suelto no ofrece.

## Las cinco V en este caso

- Volumen: más de 255.000 registros entre las cuatro fuentes con escala small; la cantidad crece según la escala elegida (test, small, demo).
- Velocidad: los 200.000 eventos de la aplicación representan datos que se generan de forma continua y en mayor cantidad que el resto.
- Variedad: cuatro fuentes en tres formatos distintos (CSV, Parquet y JSON), con esquemas diferentes.
- Veracidad: el diagnóstico muestra 11 IDs duplicados y 52 importes inválidos, por lo que no se puede confiar en los datos sin limpiarlos.
- Valor: al integrar clientes, productos, transacciones y eventos se pueden analizar ventas, canales de pago y comportamiento de los usuarios, pero solo después de resolver los problemas de calidad.

## Reflexión final del desafío

Detectar una evolución de esquema es advertir que la fuente cambió: en este caso, apareció la columna app_version, un nuevo event_type (refund) y un evento duplicado. Aceptarla técnicamente es lograr que el pipeline la incorpore sin romperse ni perder historia: unir por nombre completando con NULL, deduplicar por event_id y escribir de forma re-ejecutable. Pero que Spark acepte el cambio no significa que el dato sea correcto. Decidir que es válido para el negocio requiere criterio de las personas responsables. La técnica garantiza que el dato entre; el negocio decide si se puede usar.
