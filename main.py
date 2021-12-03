from typing_extensions import final
from fastapi import FastAPI
import uvicorn
from database import create_table, insert_to_table, check_if_already_exist, read_from_table, update_table
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


class AcceptQuote(BaseModel):
    accept: bool = True
    quote_id: int


class Invoice(BaseModel):
    inv_pending: bool = True
    quote_id: int


class PayInvoice(BaseModel):
    credit_card: int
    quote_id: int


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

sql_create_invoice_table = ''' CREATE TABLE IF NOT EXISTS Invoice(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inv_pending BOOL NOT NULL,
    quote_id INTEGER NOT NULL,
    FOREIGN KEY (quote_id) REFERENCES quote(id)  
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
    for key, value in dic.items():
        # remove whitespace around the item
        key = key.strip()
    return(tuple([*dic.values()]))


def calc_vat(price):
    vat = price / 100 * 21
    newPrice = price + vat
    return(newPrice)


def calc_conversion(price, currency):
    if (currency == "EUR"):
        return(price)
    # check if conversion is up to date, if not update it
    r = update_convert_table()
    print(r)
    # get daily conversion
    conversionRates = read_from_table("conversion", "conversion_rates", False)
    # convert to dict
    conversionRates = json.loads(conversionRates[0])
    # convert to EUR
    finalResult = 1 / conversionRates[currency] * price
    return(finalResult)


def check_credit_card(cardNumbers):
    # convert to string
    cardNumbers = str(cardNumbers)
    # save last digit to checking digit
    checkingDigit = int(cardNumbers[:1])
    # remove last digit
    cardNumbers = cardNumbers[:-1]
    # reverse the numbers
    cardNumbers = cardNumbers[::-1]
    # convert to list of int
    cardNumbers = list(map(int, cardNumbers))
    # even number * 2 > 9 -> number-=9
    for index, num in enumerate(cardNumbers):
        if (index % 2 == 0):
            num *= 2
            if (num > 9):
                num -= 9
                cardNumbers[index] = num
    # sum the list + add checking digit
    finalNumber = sum(cardNumbers) + checkingDigit
    if (finalNumber % 10 == 0):
        return(True)
    return (False)


# Router

@app.get("/")
def root():
    return {"message": "It works !"}


@app.post("/create-company-account")
def create_company_account(company: Company):
    # create table, if already exist skip
    if (create_table(sql_create_company_table)):
        table = "Company"
        # convert model to right format for sql request
        model = generate_model_to_string(Company)
        data = generate_data_to_tuple(company)
        # add data to db
        insert_to_table(table, model, data)
        return {"message": "Company account created"}
    return {"result": "NOK"}


@app.post("/create-customer-account")
def create_customer_account(customer: Customer):
    # create table, if already exist skip
    if (create_table(sql_create_customer_table)):
        table = "Customer"
        # convert model to right format for sql request
        model_str = generate_model_to_string(Customer)
        model_lst = generate_model_to_list(Customer)
        data = generate_data_to_tuple(customer)
        res = check_if_already_exist(table, model_lst, data)
        if (res):
            # add data to db
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
        # convert model to right format for sql request
        model_str = generate_model_to_string(Subscription)
        model_lst = generate_model_to_list(Subscription)
        data = generate_data_to_tuple(subscription)
        res = check_if_already_exist(table, model_lst, data)
        if (res):
            # add data to db
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
            # add data to db
            quote_id = insert_to_table(table, model_str, data)
            # add quote id
            quote["quote_id"] = quote_id
        # convert price in euro
        quote["quote_price_eur"] = calc_conversion(
            quote["quote_price"], quote["quote_currency"])
        # add vat to price
        quote["quote_price_vat_incl"] = calc_vat(quote["quote_price_eur"])
        # round to 2 decimals
        quote["quote_price_vat_incl"] = round(quote["quote_price_vat_incl"], 2)
        quote["quote_price_eur"] = round(quote["quote_price_eur"], 2)
        # convert to json string
        jsonStr = json.dumps(quote)
        return {jsonStr}
    return {"result": "NOK"}


@app.post("/accept-quote")
def accept_quote(acceptQuote: AcceptQuote):
    acceptQuote = dict(acceptQuote)
    if (acceptQuote["accept"]):
        update_table("Quote", list(str(acceptQuote["quote_id"])))
        # create invoice
        create_table(sql_create_invoice_table)
        model_str = generate_model_to_string(Invoice)
        data = (True, acceptQuote["quote_id"])
        insert_to_table("Invoice", model_str, data)

    else:
        return{"message": "Quote not accepted"}

    return {"result": "NOK"}


@app.get("/check-payment")
def check_payment(quote_id: int):
    result = read_from_table(
        "Invoice", "*", "WHERE quote_id = " + str(quote_id))
    if (len(result) == 1):
        result = list(result)
        if (result[1] == 1):
            result[1] = True
        else:
            result[1] = False
        return {"id": result[0], "inv_pending": result[1], "quote_id": result[2]}
    return {"message": "No invoice found with the quote id : " + quote_id}


@app.post("/pay-invoice")
def pay_invoice(payInvoice: PayInvoice):
    payInvoice = dict(payInvoice)
    # check credit card
    if (check_credit_card(payInvoice["credit_card"])):
        # check if quote id exist
        return(True)

    # result = read_from_table(
    #     "Invoice", "*", "WHERE quote_id = " + str(quote_id))

    return {"message": "Payment refused"}


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
