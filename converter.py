from pydantic.utils import _EMPTY
import requests
import json
import time
from database import create_table, create_connection_to_db, read_from_table

sql_converter_table = "CREATE TABLE IF NOT EXISTS conversion (id INTEGER PRIMARY KEY AUTOINCREMENT, base_code TEXT NOT NULL, conversion_rates json, documentation TEXT NOT NULL, result TEXT NOT NULL, terms_of_use TEXT NOT NULL, time_last_update_unix INT NOT NULL, time_last_update_utc DATE NOT NULL, time_next_update_unix INT NOT NULL, time_next_update_utc DATE NOT NULL)"
table = "conversion"


def delete_table():
    conn = create_connection_to_db()
    cur = conn.cursor()
    cur.execute("DELETE from " + table)
    conn.commit()


def check_time():
    data = read_from_table(table, "time_next_update_unix", False)
    if (data == False):
        return(True)
    if (data[0] <= time.time()):
        return(True)
    return(False)


def update_convert_table():
    if (check_time()):
        # create table if doesn't exist
        create_table(sql_converter_table)

        # erease previous conversion datas
        delete_table()

        # get new conversion data
        response = requests.get(
            "https://v6.exchangerate-api.com/v6/e1ab50496b040f58ab530bc6/latest/EUR")
        currentCurrencies = response.json()

        # upload new records to db
        conn = create_connection_to_db()
        cur = conn.cursor()
        cur.execute("insert into conversion (base_code, conversion_rates, documentation, result, terms_of_use, time_last_update_unix, time_last_update_utc, time_next_update_unix, time_next_update_utc) values (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
                    currentCurrencies["base_code"], json.dumps(currentCurrencies["conversion_rates"]), currentCurrencies["documentation"], currentCurrencies["result"], currentCurrencies["terms_of_use"], currentCurrencies["time_last_update_unix"], currentCurrencies["time_last_update_utc"], currentCurrencies["time_next_update_unix"], currentCurrencies["time_next_update_utc"]])
        conn.commit()
        return True
    return False
