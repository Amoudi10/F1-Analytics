import fastf1 
import pandas as pd 
import os 

#create folders ( isnt there tool to catch mistakes? typos)
os.makedirs('cache', exist_ok=True)
os.makedirs('data', exist_ok=True)


#cache means we dont have to donwload the data again everytime we run the script 
#i believe the name of the file is cache which is the arument to the method 
fastf1.Cache.enable_cache('cache')

# name of sessions we want to loop through. thats why its made in a list 

sessions_to_fetch = ['FP1', 'FP2', 'FP3', 'Q', 'R']

for session_name in sessions_to_fetch:
    print(f"\nFetching {session_name}...")
#try is used incase somethign fails we dont want the script to crash its ppaired with expcept

    try:
        session = fastf1.get_session(2026, 'Japan', session_name)
        session.load()
        
        # Save laps table
        laps = session.laps
        laps.to_parquet(f'data/japan_2026_{session_name}_laps.parquet')
        print(f"Saved laps for {session_name}")
        
        # Save results table
        results = session.results
        results.to_parquet(f'data/japan_2026_{session_name}_results.parquet')
        print(f"Saved results for {session_name}")
        
        # Save weather table
        weather = session.weather_data
        weather.to_parquet(f'data/japan_2026_{session_name}_weather.parquet')
        print(f"Saved weather for {session_name}")

    except Exception as error:
        print(f"Could not fetch {session_name}. Reason: {error}")

print("\nAll done! Check your data folder.")