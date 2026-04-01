# F1-Analytics

## Overview
F1 data pipeline project using the [Fast-F1](https://github.com/theOehrly/Fast-F1) Python library to fetch Formula 1 timing data, load it into DuckDB, and push to MotherDuck.

## Data Source: Fast-F1 Library
All data comes from the official F1 live timing API via Fast-F1. Data is stored as parquet files in `data/`.

### Currently Pulled Data

**Laps** (`*_laps.parquet`) — One row per driver per lap.
- `Time`, `Driver`, `DriverNumber`, `LapTime`, `LapNumber`, `LapStartTime`, `LapStartDate`
- Sectors: `Sector1Time`, `Sector2Time`, `Sector3Time`, `Sector1SessionTime`, `Sector2SessionTime`, `Sector3SessionTime`
- Speed traps: `SpeedI1`, `SpeedI2`, `SpeedFL` (finish line), `SpeedST` (longest straight) — all km/h
- Tires: `Compound` (SOFT/MEDIUM/HARD/INTERMEDIATE/WET), `TyreLife`, `FreshTyre`, `Stint`
- Pit: `PitInTime`, `PitOutTime`
- Classification: `Position`, `Team`, `IsPersonalBest`, `IsAccurate`
- Track: `TrackStatus` (flag codes active during lap)
- Deletion: `Deleted`, `DeletedReason`

**Results** (`*_results.parquet`) — One row per driver per session.
- Identity: `DriverNumber`, `Abbreviation`, `FullName`, `FirstName`, `LastName`, `BroadcastName`, `DriverId`
- Team: `TeamName`, `TeamColor`, `TeamId`
- Classification: `Position`, `ClassifiedPosition`, `GridPosition`, `Time`, `Status`, `Points`, `Laps`
- Qualifying: `Q1`, `Q2`, `Q3` (only in qualifying sessions)
- Metadata: `HeadshotUrl`, `CountryCode`

**Weather** (`*_weather.parquet`) — Sampled ~once per minute.
- `Time`, `AirTemp` (C), `TrackTemp` (C), `Humidity` (%), `Pressure` (mbar)
- `Rainfall` (bool), `WindDirection` (degrees 0-359), `WindSpeed` (m/s)

### Available But Not Yet Pulled

**Telemetry** — ~240ms resolution per driver. The most granular data.
- Car data: `Speed` (km/h), `RPM`, `nGear`, `Throttle` (0-100%), `Brake` (bool), `DRS` (status code)
- Position data: `X`, `Y`, `Z` (1/10 meter), `Status` (OnTrack/OffTrack)
- Enables: braking point comparisons, cornering speed analysis, track position visualization

**Race Control Messages** — Flags, penalties, DRS activations.
- `Category` (Flag/Drs/CarEvent/Other), `Message`, `Flag`, `Scope`, `RacingNumber`, `Lap`

**Track Status** — Safety car, VSC, red flag periods.
- Status codes: 1=Clear, 2=Yellow, 4=Safety Car, 5=Red Flag, 6=VSC, 7=VSC Ending

**Circuit Info** — Corner locations, marshal lights/sectors, track rotation angle.

**Ergast Historical Data** — Championship standings, pit stop details, historical results, circuit database. Goes back decades.

## File Naming Convention
`data/{location}_{year}_{session}_{datatype}.parquet`
- Sessions: FP1, FP2, FP3, Q (Qualifying), R (Race)
- Data types: laps, results, weather

## Infrastructure
- **DuckDB** for local analytics database
- **MotherDuck** for cloud-hosted DuckDB (push via `CREATE OR REPLACE DATABASE ... FROM CURRENT_DATABASE()`)
