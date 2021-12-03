from fastapi import FastAPI
import uvicorn
from database import create_table, insert_to_table, check_if_already_exist
from pydantic import BaseModel
import json
from converter import update_convert_table

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


class Quote(BaseModel):
    quote_quantity: int
    quote_price: float
    quote_currency: str
    quote_active: bool = False
    customer_id: int
    subscription_id: int


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

sql_create_subscription_table = ''' CREATE TABLE IF NOT EXISTS Subscription(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sub_price FLOAT NOT NULL,
    sub_currency TEXT NOT NULL,
    company_id INTEGER NOT NULL,
    FOREIGN KEY (company_id) REFERENCES company(id) 
    ) '''

sql_create_quote_table = ''' CREATE TABLE IF NOT EXISTS Quote(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_quantity INT NOT NULL,
    quote_price FLOAT NOT NULL,
    quote_currency TEXT NOT NULL,
    quote_active BOOL NOT NULL,
    customer_id INTEGER NOT NULL,
    subscription_id INTEGER NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customer(id),
    FOREIGN KEY (subscription_id) REFERENCES subscription(id)  
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


def calc_vat(price):
    vat = price / 100 * 21
    newPrice = price + vat
    return(newPrice)


def calc_conversion(price, currency):
    if (currency == "EUR"):
        return(price)
    update_convert_table()
    # response = requests.get(
    #     "https://v6.exchangerate-api.com/v6/e1ab50496b040f58ab530bc6/latest/" + currency)
    # currentCurrencies = dict(response.json())
    # conversionRates = currentCurrencies["conversion_rates"]["EUR"]
    # newPrice = conversionRates * price
    # return(newPrice)


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
        insert_to_table(table, model, data)
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
            insert_to_table(table, model_str, data)
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
            insert_to_table(table, model_str, data)
            return {"message": "Subscripytion created"}
        return {"message": "Subscripytion already exist"}
    return {"result": "NOK"}


@app.post("/create-quote")
def create_quote(quote: Quote):
    quote = dict(quote)
    # round to 2 decimals
    quote["quote_price"] = round(quote["quote_price"], 2)
    # create table, if already exist skip
    if (create_table(sql_create_quote_table)):
        table = "Quote"
        model_str = generate_model_to_string(Quote)
        model_lst = generate_model_to_list(Quote)
        data = generate_data_to_tuple(quote)
        res = check_if_already_exist(table, model_lst, data)
        if (res):
            insert_to_table(table, model_str, data)
            # convert price in euro
        quote["quote_price_eur"] = calc_conversion(
            quote["quote_price"], quote["quote_currency"])
        # add price with vat
        quote["quote_price_vat_incl"] = calc_vat(quote["quote_price_eur"])
        # round to 2 dec.
        quote["quote_price_vat_incl"] = round(quote["quote_price_vat_incl"], 2)
        quote["quote_price_eur"] = round(quote["quote_price_eur"], 2)
        jsonStr = json.dumps(quote)
        return {jsonStr}
    return {"result": "NOK"}


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
