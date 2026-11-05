import sys
sys.path.insert(0, ".")
import psycopg
from scraper_agent.classifiers.location_parser import is_usa_location, parse_location

conn = psycopg.connect('postgresql://postgres:root@localhost:5433/scraperAgent')
cur = conn.cursor()
cur.execute('SELECT id, title, location, description, city, state, country FROM jobs WHERE id = 489;')
row = cur.fetchone()
jid, title, loc, desc, city, state, country = row

print("Testing ID 489:")
print(f"Title: {title}")
print(f"Loc: {loc}")
print(f"City: {city}, State: {state}, Country: {country}")
print(f"Desc snippet: {desc[:100]}")

is_us = is_usa_location(loc, title, desc, city=city, state=state, country=country)
print(f"is_usa_location result: {is_us}")
conn.close()

