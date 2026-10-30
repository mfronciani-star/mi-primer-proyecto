import dlt
from pyspark.sql import functions as F

# Bronze: copia fiel de los CSV originales. Todo queda como texto y solo se
# agregan columnas de trazabilidad (archivo de origen y momento de ingesta).

RAW = "/Volumes/workspace/tp_transfermarkt/raw/transfermarkt/"
TABLAS = ["competitions", "clubs", "players", "games",
          "appearances", "player_valuations", "transfers"]


def crear_bronze(nombre):
    @dlt.table(
        name=f"bronze_{nombre}",
        comment=f"Datos crudos de {nombre}.csv.gz tal cual llegan, sin tipar ni limpiar.",
    )
    def tabla_bronze():
        return (
            spark.read
            .option("header", True)
            .option("inferSchema", False)
            .option("escape", '"')
            .csv(RAW + f"{nombre}.csv.gz")
            .withColumn("_source_file", F.col("_metadata.file_path"))
            .withColumn("_ingested_at", F.current_timestamp())
        )


for t in TABLAS:
    crear_bronze(t)
