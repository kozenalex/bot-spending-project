import sqlite3
import datetime

CATEGORIES = (
    'Продукты',
    'Аптека',
    'Авто',
    'Кафе'
)

def db_init():
    conn = sqlite3.connect('spending.db')
    cur = conn.cursor()
    return (cur, conn)

def create_tables(cur, conn, user_name):
    now = datetime.datetime.now()
    suffix = str(now.year) + str(now.month)
    cur.execute("""CREATE TABLE IF NOT EXISTS """+ user_name + suffix + """(
    id INT PRIMARY KEY,
    category TEXT,
    sum REAL);
    """)
    conn.commit()