import sqlite3
import datetime

CATEGORIES = (
    'Продукты',
    'Аптека',
    'Авто',
    'Кафе'
)

def gen_table_suffix():
    now = datetime.datetime.now()
    return str(now.year) + str(now.month)

def db_init():
    conn = sqlite3.connect('spending.db')
    cur = conn.cursor()
    return (cur, conn)

def create_tables(user_name):
    conn = sqlite3.connect('spending.db')
    cur = conn.cursor()
    suffix = gen_table_suffix()
    cur.execute("""CREATE TABLE IF NOT EXISTS """+ user_name + suffix + """(
    category TEXT,
    sum REAL);
    """)
    conn.commit()
    conn.close()

def add_spent(user_name, data):
    conn = sqlite3.connect('spending.db')
    cur = conn.cursor()
    table_name = user_name + gen_table_suffix()
    table_exist = conn.execute(""" SELECT count(name) 
    FROM sqlite_master WHERE type='table' AND name='""" + table_name + """'""")
    if table_exist.fetchone()[0]==1 :
        cur.execute("INSERT INTO " + table_name + " VALUES(?, ?);", data)
        conn.commit()
    conn.close()

def calculate_spent(user_name):
    conn = sqlite3.connect('spending.db')
    cur = conn.cursor()
    sums = list()
    table_name = user_name + gen_table_suffix()
    table_exist = conn.execute(""" SELECT count(name) 
    FROM sqlite_master WHERE type='table' AND name='""" + table_name + """'""")
    if table_exist.fetchone()[0]==1 :
        for c in CATEGORIES:
            query = cur.execute("SELECT sum FROM " + table_name + " WHERE category = '" + c + "';")
            if query is not None:
                sums.append((c, sum([s[0] for s in query.fetchall()])))
            else:
                sums.append((c, 0))
    conn.close()
    return sums
