from fastapi import FastAPI
import uvicorn
from database import create_table, insert_to_table_company, check_if_already_exist
from pydantic import BaseModel

app = FastAPI()

# Models


class Company(BaseModel):
    co_name: str
    co_address: str
    co_VAT: int
    co_bankaccount: str


class Customer(BaseModel):
    cus_name: str
    cus_email: str
    cus_address: str
    cus_phone: str
    company_id: int


class Subscription(BaseModel):
    sub_price: float
    sub_currency: str
    company_id: int


# Query

sql_create_company_table = ''' CREATE TABLE IF NOT EXISTS Company(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    co_name TEXT NOT NULL,
    co_address TEXT NOT NULL,
    co_VAT INT NOT NULL,
    co_bankaccount TEXT NOT NULL) '''

sql_create_customer_table = ''' CREATE TABLE IF NOT EXISTS Customer(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cus_name TEXT NOT NULL,
    cus_email TEXT NOT NULL,
    cus_address TEXT NOT NULL,
    cus_phone TEXT NOT NULL,
    company_id INTEGER NOT NULL,
    FOREIGN KEY (company_id) REFERENCES company(id) 
    ) '''

sql_create_subscription_table = ''' CREATE TABLE IF NOT EXISTS subscription(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sub_price FLOAT NOT NULL,
    sub_currency TEXT NOT NULL,
    company_id INTEGER NOT NULL,
    FOREIGN KEY (company_id) REFERENCES company(id) 
    ) '''

# Functions


def generate_model_to_string(model):
    r = dict(model.__annotations__)
    str = ""
    for key, value in r.items():
        str += key + ", "
    return(str[:-2])


def generate_model_to_list(model):
    r = dict(model.__annotations__)
    lst = []
    for key, value in r.items():
        lst.append(key)
    return(lst)


def generate_data_to_tuple(data):
    dic = dict(data)
    # remove whitespace around the item
    for key, value in dic.items():
        key = key.strip()
    return(tuple([*dic.values()]))


# Router


@app.get("/")
def root():
    return {"message": "It works !"}


@app.post("/create-company-account")
def create_company_account(company: Company):
    # create table, if already exist skip
    if (create_table(sql_create_company_table)):
        table = "Company"
        model = generate_model_to_string(Company)
        data = generate_data_to_tuple(company)
        insert_to_table_company(table, model, data)
        return {"message": "Company account created"}
    return {"result": "NOK"}


@app.post("/create-customer-account")
def create_customer_account(customer: Customer):
    # create table, if already exist skip
    if (create_table(sql_create_customer_table)):
        table = "Customer"
        model_str = generate_model_to_string(Customer)
        model_lst = generate_model_to_list(Customer)
        data = generate_data_to_tuple(customer)
        res = check_if_already_exist(table, model_lst, data)
        if (res):
            insert_to_table_company(table, model_str, data)
            return {"message": "Customer account created"}
        return {"message": "Customer already exist"}
    return {"result": "NOK"}


@app.post("/create-subscripton")
def create_subscription(subscription: Subscription):
    subscription = dict(subscription)
    # round to 2 decimals
    subscription["sub_price"] = round(subscription["sub_price"], 2)
    # create table, if already exist skip
    if (create_table(sql_create_subscription_table)):
        table = "Subscription"
        model_str = generate_model_to_string(Subscription)
        model_lst = generate_model_to_list(Subscription)
        data = generate_data_to_tuple(subscription)
        res = check_if_already_exist(table, model_lst, data)
        if (res):
            insert_to_table_company(table, model_str, data)
            return {"message": "Customer account created"}
        return {"message": "Customer already exist"}
    return {"result": "NOK"}


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
