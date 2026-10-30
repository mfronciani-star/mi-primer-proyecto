import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Gold: productos de datos listos para responder preguntas de negocio.


@dlt.table(
    name="gold_player_season_stats",
    comment="Rendimiento de cada jugador por temporada. Grano: un jugador por temporada.",
)
def gold_player_season_stats():
    ap = spark.read.table("silver_appearances")
    g = spark.read.table("silver_games").select("game_id", "season")
    return (
        ap.join(g, "game_id")
        .groupBy("player_id", "season")
        .agg(
            F.first("player_name", ignorenulls=True).alias("player_name"),
            F.countDistinct("game_id").alias("partidos"),
            F.sum("minutes_played").alias("minutos"),
            F.sum("goals").alias("goles"),
            F.sum("assists").alias("asistencias"),
            F.sum("yellow_cards").alias("amarillas"),
            F.sum("red_cards").alias("rojas"),
        )
        .withColumn(
            "goles_por_90",
            F.when(F.col("minutos") > 0, F.round(F.col("goles") * 90 / F.col("minutos"), 3)),
        )
    )


@dlt.table(
    name="gold_player_market_value",
    comment="Último valor de mercado y valor máximo de cada jugador. Grano: un jugador.",
)
def gold_player_market_value():
    v = spark.read.table("silver_player_valuations")
    w = Window.partitionBy("player_id").orderBy(F.col("date").desc())
    ultimo = (
        v.withColumn("rn", F.row_number().over(w))
        .where("rn = 1")
        .select(
            "player_id",
            F.col("date").alias("fecha_ultima_valuacion"),
            F.col("market_value_in_eur").alias("valor_actual_eur"),
        )
    )
    resumen = v.groupBy("player_id").agg(
        F.max("market_value_in_eur").alias("valor_maximo_eur"),
        F.count("*").alias("cantidad_valuaciones"),
    )
    p = spark.read.table("silver_players").select(
        "player_id", "name", "position", "country_of_citizenship",
        "current_club_name", "date_of_birth",
    )
    return (
        p.join(ultimo, "player_id")
        .join(resumen, "player_id")
        .withColumn(
            "edad_en_ultima_valuacion",
            F.floor(F.months_between("fecha_ultima_valuacion", "date_of_birth") / 12),
        )
    )


@dlt.table(
    name="gold_club_transfer_balance",
    comment="Gasto, ingresos y balance por transferencias. Grano: un club por temporada de transferencias.",
)
def gold_club_transfer_balance():
    t = spark.read.table("silver_transfers")
    entradas = t.select(
        F.col("to_club_id").alias("club_id"), F.col("to_club_name").alias("club_name"),
        "transfer_season",
        F.col("transfer_fee").alias("gasto_eur"), F.lit(0.0).alias("ingreso_eur"),
        F.lit(1).alias("altas"), F.lit(0).alias("bajas"),
    )
    salidas = t.select(
        F.col("from_club_id").alias("club_id"), F.col("from_club_name").alias("club_name"),
        "transfer_season",
        F.lit(0.0).alias("gasto_eur"), F.col("transfer_fee").alias("ingreso_eur"),
        F.lit(0).alias("altas"), F.lit(1).alias("bajas"),
    )
    return (
        entradas.unionByName(salidas)
        .where("club_id IS NOT NULL")
        .groupBy("club_id", "transfer_season")
        .agg(
            F.first("club_name", ignorenulls=True).alias("club_name"),
            F.sum(F.coalesce("gasto_eur", F.lit(0.0))).alias("gasto_eur"),
            F.sum(F.coalesce("ingreso_eur", F.lit(0.0))).alias("ingreso_eur"),
            F.sum("altas").alias("altas"),
            F.sum("bajas").alias("bajas"),
        )
        .withColumn("balance_eur", F.col("ingreso_eur") - F.col("gasto_eur"))
    )


@dlt.table(
    name="gold_competition_season",
    comment="Resumen de resultados por competición y temporada. Grano: una competición por temporada.",
)
def gold_competition_season():
    g = spark.read.table("silver_games")
    c = spark.read.table("silver_competitions").select(
        "competition_id", F.col("name").alias("competition_name"), "country_name"
    )
    local = F.col("home_club_goals") > F.col("away_club_goals")
    empate = F.col("home_club_goals") == F.col("away_club_goals")
    visita = F.col("home_club_goals") < F.col("away_club_goals")
    return (
        g.join(c, "competition_id", "left")
        .groupBy("competition_id", "competition_name", "country_name", "season")
        .agg(
            F.count("*").alias("partidos"),
            F.round(F.avg(F.col("home_club_goals") + F.col("away_club_goals")), 2).alias("goles_promedio"),
            F.round(F.avg(F.when(local, 1).otherwise(0)) * 100, 1).alias("pct_gana_local"),
            F.round(F.avg(F.when(empate, 1).otherwise(0)) * 100, 1).alias("pct_empate"),
            F.round(F.avg(F.when(visita, 1).otherwise(0)) * 100, 1).alias("pct_gana_visitante"),
            F.round(F.avg("attendance")).alias("asistencia_promedio"),
        )
    )
