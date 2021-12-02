from sqlite3 import Error
import sqlite3

databaseName = 'SaaS.db'


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_connection_to_db():
    # create a database connection
    conn = create_connection(databaseName)
    if conn is not None:
        return(conn)
    else:
        print("Error! cannot create the database connection.")


def create_table(create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    conn = create_connection_to_db()
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        return True
    except Error as e:
        print(e)


def insert_to_table_company(table, model, data):
    """
    Create a new task
    :param table: table
    :param model: model structure
    :param data: data to fill in the db
    :return:
    """
    dataparam = ""
    for item in data:
        dataparam += '?,'

    sql = ''' INSERT INTO ''' + table + '''(''' + model + ''')
              VALUES(''' + dataparam[:-1] + ''') '''
    conn = create_connection_to_db()
    cur = conn.cursor()
    cur.execute(sql, data)
    conn.commit()
    return cur.lastrowid


def check_if_already_exist(table, model, data):
    sql = "SELECT * FROM " + table
    sql_where = " WHERE "
    lenofmodel = len(model)
    for index, item in enumerate(model):
        if index + 1 == lenofmodel:
            sql_where += item + ' = ?'
        else:
            sql_where += item + ' = ? AND '
    conn = create_connection_to_db()
    cur = conn.cursor()
    cur.execute(sql + sql_where, data)
    data = cur.fetchall()
    if (len(data) > 0):
        return (False)
    return(True)
