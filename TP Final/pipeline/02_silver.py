import dlt
from pyspark.sql import functions as F

# Silver: datos tipados, deduplicados y validados.
# Los controles de calidad se definen con expectations:
#   expect_or_drop -> la fila que no cumple se descarta (y queda contada en las métricas del pipeline)
#   expect         -> la fila se conserva, pero el incumplimiento queda registrado


def tc(col, tipo):
    """try_cast: si el valor no se puede convertir, devuelve NULL en lugar de fallar."""
    return F.expr(f"try_cast({col} AS {tipo})")


def fecha(col):
    """Convierte textos como '2020-05-01' o '2020-05-01 00:00:00' a DATE."""
    return F.expr(f"to_date(try_cast({col} AS TIMESTAMP))")


@dlt.table(name="silver_competitions", comment="Competiciones. Grano: una fila por competición.")
@dlt.expect_or_drop("competition_id_presente", "competition_id IS NOT NULL")
def silver_competitions():
    return (
        spark.read.table("bronze_competitions")
        .select(
            "competition_id", "competition_code", "name", "sub_type", "type",
            tc("country_id", "INT").alias("country_id"), "country_name",
            "confederation", tc("total_clubs", "INT").alias("total_clubs"),
        )
        .dropDuplicates(["competition_id"])
    )


@dlt.table(name="silver_clubs", comment="Clubes. Grano: una fila por club.")
@dlt.expect_or_drop("club_id_presente", "club_id IS NOT NULL")
@dlt.expect("estadio_con_capacidad_valida", "stadium_seats IS NULL OR stadium_seats > 0")
def silver_clubs():
    return (
        spark.read.table("bronze_clubs")
        .select(
            tc("club_id", "INT").alias("club_id"), "club_code", "name",
            "domestic_competition_id",
            tc("squad_size", "INT").alias("squad_size"),
            tc("average_age", "DOUBLE").alias("average_age"),
            tc("foreigners_percentage", "DOUBLE").alias("foreigners_percentage"),
            "stadium_name", tc("stadium_seats", "INT").alias("stadium_seats"),
            "coach_name", tc("last_season", "INT").alias("last_season"),
        )
        .dropDuplicates(["club_id"])
    )


@dlt.table(name="silver_players", comment="Jugadores. Grano: una fila por jugador.")
@dlt.expect_or_drop("player_id_presente", "player_id IS NOT NULL")
@dlt.expect("altura_razonable", "height_in_cm IS NULL OR height_in_cm BETWEEN 140 AND 220")
@dlt.expect("valor_no_negativo", "market_value_in_eur IS NULL OR market_value_in_eur >= 0")
def silver_players():
    return (
        spark.read.table("bronze_players")
        .select(
            tc("player_id", "INT").alias("player_id"), "name", "first_name", "last_name",
            "country_of_citizenship", "country_of_birth",
            fecha("date_of_birth").alias("date_of_birth"),
            "position", "sub_position", "foot",
            tc("height_in_cm", "INT").alias("height_in_cm"),
            tc("current_club_id", "INT").alias("current_club_id"), "current_club_name",
            "current_club_domestic_competition_id",
            tc("market_value_in_eur", "DOUBLE").alias("market_value_in_eur"),
            tc("highest_market_value_in_eur", "DOUBLE").alias("highest_market_value_in_eur"),
            fecha("contract_expiration_date").alias("contract_expiration_date"),
            tc("last_season", "INT").alias("last_season"),
        )
        .dropDuplicates(["player_id"])
    )


@dlt.table(name="silver_games", comment="Partidos. Grano: una fila por partido.")
@dlt.expect_all_or_drop({
    "game_id_presente": "game_id IS NOT NULL",
    "fecha_valida": "date IS NOT NULL",
    "goles_no_negativos": "home_club_goals >= 0 AND away_club_goals >= 0",
})
@dlt.expect("equipos_distintos", "home_club_id IS NULL OR home_club_id <> away_club_id")
def silver_games():
    return (
        spark.read.table("bronze_games")
        .select(
            tc("game_id", "INT").alias("game_id"), "competition_id",
            tc("season", "INT").alias("season"), "round",
            fecha("date").alias("date"),
            tc("home_club_id", "INT").alias("home_club_id"),
            tc("away_club_id", "INT").alias("away_club_id"),
            "home_club_name", "away_club_name",
            tc("home_club_goals", "INT").alias("home_club_goals"),
            tc("away_club_goals", "INT").alias("away_club_goals"),
            tc("attendance", "INT").alias("attendance"),
            "stadium", "referee", "competition_type",
        )
        .dropDuplicates(["game_id"])
    )


@dlt.table(name="silver_appearances",
           comment="Participaciones de un jugador en un partido. Grano: un jugador por partido.")
@dlt.expect_all_or_drop({
    "ids_presentes": "appearance_id IS NOT NULL AND game_id IS NOT NULL AND player_id IS NOT NULL",
    "minutos_validos": "minutes_played BETWEEN 0 AND 150",
    "estadisticas_no_negativas": "goals >= 0 AND assists >= 0",
})
def silver_appearances():
    return (
        spark.read.table("bronze_appearances")
        .select(
            "appearance_id",
            tc("game_id", "INT").alias("game_id"),
            tc("player_id", "INT").alias("player_id"),
            tc("player_club_id", "INT").alias("player_club_id"),
            fecha("date").alias("date"), "player_name", "competition_id",
            tc("yellow_cards", "INT").alias("yellow_cards"),
            tc("red_cards", "INT").alias("red_cards"),
            tc("goals", "INT").alias("goals"),
            tc("assists", "INT").alias("assists"),
            tc("minutes_played", "INT").alias("minutes_played"),
        )
        .dropDuplicates(["appearance_id"])
    )


@dlt.table(name="silver_player_valuations",
           comment="Historia del valor de mercado. Grano: un jugador por fecha de valuación.")
@dlt.expect_all_or_drop({
    "claves_presentes": "player_id IS NOT NULL AND date IS NOT NULL",
    "valor_positivo": "market_value_in_eur > 0",
})
def silver_player_valuations():
    return (
        spark.read.table("bronze_player_valuations")
        .select(
            tc("player_id", "INT").alias("player_id"),
            fecha("date").alias("date"),
            tc("market_value_in_eur", "DOUBLE").alias("market_value_in_eur"),
            tc("current_club_id", "INT").alias("current_club_id"), "current_club_name",
            "player_club_domestic_competition_id",
        )
        .dropDuplicates(["player_id", "date"])
    )


@dlt.table(name="silver_transfers", comment="Transferencias. Grano: un movimiento de un jugador entre clubes.")
@dlt.expect_or_drop("claves_presentes", "player_id IS NOT NULL AND transfer_date IS NOT NULL")
@dlt.expect("monto_no_negativo", "transfer_fee IS NULL OR transfer_fee >= 0")
def silver_transfers():
    return (
        spark.read.table("bronze_transfers")
        .select(
            tc("player_id", "INT").alias("player_id"), "player_name",
            fecha("transfer_date").alias("transfer_date"), "transfer_season",
            tc("from_club_id", "INT").alias("from_club_id"), "from_club_name",
            tc("to_club_id", "INT").alias("to_club_id"), "to_club_name",
            tc("transfer_fee", "DOUBLE").alias("transfer_fee"),
            tc("market_value_in_eur", "DOUBLE").alias("market_value_in_eur"),
        )
        .dropDuplicates(["player_id", "transfer_date", "from_club_id", "to_club_id"])
    )
