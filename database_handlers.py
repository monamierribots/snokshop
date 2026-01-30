import sqlite3
import asyncio


async def create_db():

    db = sqlite3.connect('shop.db')

    cur = db.cursor()

    cur.execute("""    

        CREATE TABLE IF NOT EXISTS products (
                
                id INTEGER PRIMARY KEY,
                color TEXT,
                quantity INTEGER,
                price INTEGER   
                                
    )""")

    db.commit()

    db.close()
