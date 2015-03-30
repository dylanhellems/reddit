import sqlite3


def populate_db():
    sql = sqlite3.connect('sql.db')
    print('Loaded SQL Database')
    cur = sql.cursor()

    cur.execute('DROP TABLE IF EXISTS words')
    print ('Dropped old table: words')
    cur.execute('CREATE TABLE IF NOT EXISTS words(ID TEXT)')
    print('Loaded Completed table: words')

    file = open("words.txt", "r")
    for line in file:
        cur.execute('INSERT INTO words VALUES(?)', [line.strip()])
    file.close()
    print('Populated table: words')

    sql.commit()
    print('Commited\n')


def fetch_word():
    sql = sqlite3.connect('sql.db')
    print('Loaded SQL Database')
    cur = sql.cursor()
    cur.execute('SELECT COUNT(*) FROM words')
    if cur.fetchone()[0] <= 0:
        populate_db()
    cur.execute('SELECT * FROM words ORDER BY RANDOM() LIMIT 1')
    word = cur.fetchone()[0]
    print('Word fetched')
    cur.execute('DELETE FROM words WHERE ID=?', [word])
    return word

