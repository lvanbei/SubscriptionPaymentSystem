from fastapi import FastAPI, Request
import uvicorn
from pydantic import BaseModel
import json
import sqlite3
import requests
app = FastAPI()
databaseName = 'SaaS.db'


# Models
class Company(BaseModel):
    CO_NAME: str
    CO_ADDRESS: str
    CO_VAT: int
    CO_BANKACCOUNT: str


class Customer(BaseModel):
    CUS_NAME: str
    CUS_EMAIL: str
    CUS_ADDRESS: str
    CUS_PHONE: str
    COMPANY_ID: int


class Subscription(BaseModel):
    SUB_PRICE: float
    SUB_CURRENCY: str
    COMPANY_ID: int


class Quote(BaseModel):
    QUOTE_QUANTITY: int
    QUOTE_PRICE: float
    QUOTE_CURRENCY: str
    QUOTE_ACTIVE: bool = False
    CUSTOMER_ID: int
    SUBSCRIPTION_ID: int


class AcceptQuote(BaseModel):
    ACCEPT: bool = True
    QUOTE_ID: int


class Invoice(BaseModel):
    INV_PENDING: bool = True
    QUOTE_ID: int


class PayInvoice(BaseModel):
    CREDIT_CARD: int
    QUOTE_ID: int


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


def calc_vat(price):
    vat = price / 100 * 21
    newPrice = price + vat
    # convert to two decimals
    newPrice = round(2, newPrice)
    return(newPrice)


def calc_conversion(price, currency):
    if (currency == "EUR"):
        return(price)
    response = requests.get(
        "https://v6.exchangerate-api.com/v6/e1ab50496b040f58ab530bc6/latest/EUR")
    currentCurrencies = response.json()
    conversionRate = currentCurrencies["conversion_rates"][currency]
    finalResult = 1 / conversionRate * price
    # convert to two decimals
    finalResult = round(2, finalResult)
    return(finalResult)


def check_credit_card(cardNumbers):
    # convert to string
    cardNumbers = str(cardNumbers)
    if (len(cardNumbers) != 16):
        return(False)
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
    # create company
    values_dict = dict(company)
    conn = sqlite3.connect(databaseName)
    cur = conn.cursor()
    cur.execute(sql_create_company_table)
    sql = "INSERT INTO company(CO_NAME,CO_ADDRESS,CO_VAT,CO_BANKACCOUNT) VALUES(?,?,?,?)"
    data = [values_dict["CO_NAME"], values_dict["CO_ADDRESS"],
            values_dict["CO_VAT"], values_dict["CO_BANKACCOUNT"]]
    cur.execute(sql, data)
    conn.commit()
    conn.close()
    return {"message": "Company account created"}


@app.post("/create-customer-account")
def create_customer_account(customer: Customer):
    # create customer
    values_dict = dict(customer)
    conn = sqlite3.connect(databaseName)
    cur = conn.cursor()
    cur.execute(sql_create_customer_table)
    sql = "INSERT INTO customer (CUS_NAME,CUS_EMAIL,CUS_ADDRESS,CUS_PHONE,COMPANY_ID) VALUES(?,?,?,?,?)"
    data = [values_dict["CUS_NAME"], values_dict["CUS_EMAIL"],
            values_dict["CUS_ADDRESS"], values_dict["CUS_PHONE"], values_dict["COMPANY_ID"]]
    cur.execute(sql, data)
    conn.commit()
    conn.close()
    return {"message": "Customer account created"}


@app.post("/create-subscripton")
def create_subscription(subscription: Subscription):
    # create subscription
    values_dict = dict(subscription)
    conn = sqlite3.connect(databaseName)
    cur = conn.cursor()
    cur.execute(sql_create_subscription_table)
    sql = "INSERT INTO subscription (SUB_PRICE,SUB_CURRENCY,COMPANY_ID) VALUES(?,?,?)"
    data = [values_dict["SUB_PRICE"], values_dict["SUB_CURRENCY"],
            values_dict["COMPANY_ID"]]
    cur.execute(sql, data)
    conn.commit()
    conn.close()
    return {"message": "Subscription created"}


@app.post("/create-quote")
def create_quote(quote: Quote):
    # add new quote
    values_dict = dict(quote)
    conn = sqlite3.connect(databaseName)
    cur = conn.cursor()
    cur.execute(sql_create_quote_table)
    sql = "INSERT INTO quote (QUOTE_QUANTITY,QUOTE_PRICE,QUOTE_CURRENCY,QUOTE_ACTIVE,CUSTOMER_ID,SUBSCRIPTION_ID) VALUES(?,?,?,?,?,?)"
    data = [values_dict["QUOTE_QUANTITY"], values_dict["QUOTE_PRICE"], values_dict["QUOTE_CURRENCY"],
            values_dict["QUOTE_ACTIVE"], values_dict["CUSTOMER_ID"], values_dict["SUBSCRIPTION_ID"]]
    cur.execute(sql, data)
    conn.commit()
    conn.close()
    quote_id = cur.lastrowid
    # return quote id + price in EUR + price with VAT
    values_dict["QUOTE_ID"] = quote_id
    if (values_dict["QUOTE_CURRENCY"] != "EUR"):
        values_dict["QUOTE_PRICE_EUR"] = calc_conversion(
            values_dict["QUOTE_PRICE"], values_dict["QUOTE_CURRENCY"])

    values_dict["QUOTE_PRICE_VAT_INCL"] = calc_vat(
        values_dict["QUOTE_PRICE_EUR"])
    return (values_dict)


@app.post("/accept-quote")
def accept_quote(acceptQuote: AcceptQuote):
    values_dict = dict(acceptQuote)
    if (values_dict["ACCEPT"] == True):
        # update quote
        conn = sqlite3.connect(databaseName)
        cur = conn.cursor()
        sql = "UPDATE Quote SET quote_active = ? WHERE id = ?"
        data = [values_dict["ACCEPT"], values_dict["QUOTE_ID"]]
        cur.execute(sql, data)
        conn.commit()
        # create invoice
        cur.execute(sql_create_invoice_table)
        sql = "INSERT INTO Invoice (INV_PENDING,QUOTE_ID) VALUES(?,?)"
        data = [True, values_dict["QUOTE_ID"]]
        cur.execute(sql, data)
        conn.commit()
        conn.close()
        return {"message": "Payment " + str(values_dict["QUOTE_ID"]) + " has been updated to : True"}
    else:
        return {"result": "NOK"}


@app.get("/check-payment")
def check_payment(quote_id: int):
    values_dict = dict({"QUOTE_ID": quote_id})
    conn = sqlite3.connect(databaseName)
    cur = conn.cursor()
    sql = "SELECT * FROM Invoice WHERE QUOTE_ID = ?"
    data = [values_dict["QUOTE_ID"]]
    cur.execute(sql, data)
    result = cur.fetchall()
    conn.close()
    if (len(result) == 1):
        result_dict = list(result[0])
        if (result_dict[1] == 1):
            return {"message": "payment is pending"}
        elif (result_dict[1] == 0):
            return {"message": "payment is payed"}
    else:
        return {"message": "No invoice found with the quote id : " + str(values_dict["QUOTE_ID"])}


@app.post("/pay-invoice")
def pay_invoice(payInvoice: PayInvoice):
    values_dict = dict(payInvoice)
    # check credit card
    if (check_credit_card(values_dict["CREDIT_CARD"]) == True):
        conn = sqlite3.connect(databaseName)
        cur = conn.cursor()
        sql = "UPDATE Invoice SET INV_PENDING = FALSE WHERE id = ?"
        data = [values_dict["QUOTE_ID"]]
        cur.execute(sql, data)
        conn.close()
        return{"message": "Payment accepted"}
    else:
        return {"message": "Payment refused wrong credit card : " + str(payInvoice["credit_card"])}


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
