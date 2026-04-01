import fastf1 
import pandas as pd 


fastf1.Cache.enable_cache('cache')

try:
    session = fastf1.get_session(2026,'Japan','R')

    session.load()

    laps= session.laps

    print("Sucess! Data is available")
    print(laps.head())
    print("\nAll available columns: ")
    print(laps.columns.tolist())

except Exception as error:
    print("Data not available yet. Here is why: ")
    print(error)

