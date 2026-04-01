import fastf1
import pandas as pd
import duckdb
import os

# ── Config ───────────────────────────────────────────────────────────────────
# Which years and races to pull. Races can be country names, event names,
# locations, or round numbers — anything fastf1.get_session() accepts.
YEARS = [2026]
RACES = ["Japan", "Australia"]
SESSIONS = ["FP1", "FP2", "FP3", "Q", "R"]
DB_PATH = "f1.duckdb"
# ─────────────────────────────────────────────────────────────────────────────

TABLE_TYPES = ["laps", "results", "weather", "telemetry"]

os.makedirs("cache", exist_ok=True)
os.makedirs("data", exist_ok=True)
fastf1.Cache.enable_cache("cache")


def validate_config():
    """Validate that all configured races exist in the F1 schedule for each year."""
    for year in YEARS:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        valid_names = set()
        for col in ["Country", "Location", "EventName"]:
            valid_names.update(schedule[col].str.lower())

        for race in RACES:
            # round numbers are always valid if in range
            if isinstance(race, int):
                max_round = schedule["RoundNumber"].max()
                if race < 1 or race > max_round:
                    raise ValueError(
                        f"Round {race} is out of range for {year} (1-{max_round})"
                    )
            elif race.lower() not in valid_names:
                valid_list = sorted(schedule["EventName"].tolist())
                raise ValueError(
                    f"'{race}' is not a valid race for {year}. "
                    f"Valid event names:\n  " + "\n  ".join(valid_list)
                )

    print("Config validated — all races and years are valid.")


def _file_prefix(year, race):
    """Build a consistent file prefix from year and race name."""
    # normalize race name to lowercase with underscores for file names
    race_slug = str(race).lower().replace(" ", "_")
    return f"{race_slug}_{year}"


def session_already_fetched(year, race, session_name):
    """Check if all four parquet files already exist for a given session."""
    prefix = _file_prefix(year, race)
    return all(
        os.path.exists(f"data/{prefix}_{session_name}_{t}.parquet") for t in TABLE_TYPES
    )


def fetch_data():
    validate_config()

    for year in YEARS:
        for race in RACES:
            for session_name in SESSIONS:
                prefix = _file_prefix(year, race)

                if session_already_fetched(year, race, session_name):
                    print(
                        f"\nSkipping {race} {year} {session_name} — data already exists locally"
                    )
                    continue

                print(f"\nFetching {race} {year} {session_name}...")
                try:
                    session = fastf1.get_session(year, race, session_name)
                    session.load()

                    # Save laps
                    laps = session.laps
                    laps.to_parquet(f"data/{prefix}_{session_name}_laps.parquet")
                    print("  Saved laps")

                    # Save results
                    results = session.results
                    results.to_parquet(f"data/{prefix}_{session_name}_results.parquet")
                    print("  Saved results")

                    # Save weather
                    weather = session.weather_data
                    weather.to_parquet(f"data/{prefix}_{session_name}_weather.parquet")
                    print("  Saved weather")

                    # Save telemetry — must be fetched per driver then combined
                    all_telemetry = []
                    for driver in session.drivers:
                        try:
                            driver_laps = laps.pick_drivers(driver)
                            telemetry = driver_laps.get_telemetry()
                            telemetry["Driver"] = driver_laps.iloc[0]["Driver"]
                            telemetry["DriverNumber"] = driver
                            all_telemetry.append(telemetry)
                        except Exception as tel_error:
                            print(
                                f"    Could not get telemetry for driver {driver}: {tel_error}"
                            )

                    if all_telemetry:
                        combined_telemetry = pd.concat(all_telemetry, ignore_index=True)
                        combined_telemetry.to_parquet(
                            f"data/{prefix}_{session_name}_telemetry.parquet"
                        )
                        print(f"  Saved telemetry ({len(combined_telemetry)} rows)")

                except Exception as error:
                    print(f"  Could not fetch {race} {year} {session_name}: {error}")

    print("\nAll done! Check your data folder.")


def write_to_duckdb(db_path=DB_PATH):
    """Read all parquet files from data/ and write them into a local DuckDB database
    with four tables: laps, results, weather, telemetry. Each table combines all
    races and sessions with Year, Race, and SessionType columns."""

    con = duckdb.connect(db_path)

    for table_type in TABLE_TYPES:
        print(f"\nLoading {table_type}...")
        dfs = []
        for year in YEARS:
            for race in RACES:
                for session_name in SESSIONS:
                    prefix = _file_prefix(year, race)
                    path = f"data/{prefix}_{session_name}_{table_type}.parquet"
                    if not os.path.exists(path):
                        print(f"  Skipping {path} (not found)")
                        continue
                    df = pd.read_parquet(path)
                    df.insert(0, "Year", year)
                    df.insert(1, "Race", race)
                    df.insert(2, "SessionType", session_name)
                    dfs.append(df)

        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            con.execute(
                f"CREATE OR REPLACE TABLE {table_type} AS SELECT * FROM combined"
            )
            row_count = con.execute(f"SELECT COUNT(*) FROM {table_type}").fetchone()[0]
            print(f"  Wrote {table_type} table: {row_count} rows")

    con.close()
    print(f"\nDuckDB database saved to {db_path}")


if __name__ == "__main__":
    fetch_data()
    write_to_duckdb()
