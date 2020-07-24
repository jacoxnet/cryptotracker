# *CX cryptotracker*

*CX cryptotracker* is a web application that helps the user keep track of the purchase, sale, present value, and profit/loss, of the user's cryptocurrency holdings. It also helps the user do research on cryptocurrencies by retrieving price and other relevant information through web APIs.

This project was prepared to satisfy the "final project" requirement for CS50x, the online version of Harvard's Computer Science 50 class.

In addition to registration and login, there are four basic functional screens in the web app, each reachable by clicking on Navigation Bar elements.

- The home screen lists the user's current cryptocurrency holdings
- *Request Quote* allows the user to request the current price and other available information on a cryptocurrency.
- *Enter Transaction* allows the user to enter purchase and sale transactions in cryptocurrencies.
- *Transaction History* displays all purchase and sale transactions entered in the system.

These four screens are described in more detail below.

## Technologies

The foundation of the web app is the code distributed for the finance app in the web track of the CS50x course. Thus, it is implemented using Flask, python3, JavaScript,  requests, and related technologies. It also continues to use CS50's SQL function for interfacing with a sqlite3 database. 

[CoinMarketCap.com](https://coinmarketcap.com) was chosen as the web site offering the most appropriate API for obtaining real-time information on cryptocurrencies. The web app provided an API key for this purpose under a "Basic" plan that operates on a credit system that limits the rate and quantity of API requests. It also provided a "sandbox" API environment for testing. The limits imposed are sufficient for development purposes.

The web app makes use of JavaScript/JQuery and Ajax requests to respond to input and to update elements of pages without reloading the entire page.

## How to Use

### Database

The web app depends on two preexisting tables in a sqlite3 database called **cryptos.txt**.  The fields for the tables are:

```sql
CREATE TABLE IF NOT EXISTS "users" (
        "id"        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "username"  TEXT NOT NULL UNIQUE,
        "fullname"  TEXT,
        "hash"      INTEGER NOT NULL);
```
```sql
CREATE TABLE IF NOT EXISTS "transactions" (
        "id"        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "symbol"    TEXT NOT NULL,
        "price"     NUMERIC NOT NULL,
        "costs"     NUMERIC NOT NULL,
        "quantity"  NUMERIC NOT NULL,
        "timestamp" datetime NOT NULL,
        "user_id"   INTEGER NOT NULL,
        FOREIGN KEY("user_id") REFERENCES "users"("id"));
```

### Starting the App

After creating the database, and making sure as well that all requirements listed in **requirements.txt** have been installed, start the app under flask's development server in the project's home directory. 

```shell
$ flask run
```

### Files

- application.py  (main repository of python code)
- helpers.py      (python functions called from application.py)
- cryptos.db      (sqlite3 database)
- README.md
- requirements.txt
- templates directory
  - apology.html
  - displayholdings.html
  - enter/html
  - history.html
  - layout.html
  - login.html
  - quoterequest.html
  - register.html
- static directory
  - generic.png (app pic)
  - generic pic license.txt (licensing text for pic)
  - icon.ico (icon version of pic)
  - styles.css

## Instructions for Using Web Pages

### Homepage

This page lists the current cryptocurrency holdings in a table with seven columns:

- **Symbol** The currency's icon and exchange symbol (e.g., BTC)
- **Currency Name** Official text name of currency (*e.g.* Bitcoin)
- **Quantity** Amount of currency (floating point number)
- **Current Price** In USD per coin.
- **Cost Per Coin** Calculated average cost per coin, including transaction fees
- **Profit/Loss** Change in value from purchase date(s) to current value
- **Current Value** Real-time quotation from [CoinMarketCap.com](https://coinmarketcap.com)

Two "Total" figures are also provided -- Profit/Loss and Current Value.

### Request Quote

This page allows the user to request information about any listed cryptocurrency. The user can either click on one of the listed icons for the cryptocurrencies the user's already bought or sold, or type in a new symbol. Using Ajax and JQuery to alter the displayed page without reload, the site then displays financial and textual information about the requested cryptocurrency.

### Enter Transaction

This page allows the user to enter the details of a cryptocurrency transaction. The user first selects a radio button to choose a "Purchase Transaction" or a "Sale Transaction." Using JQuery, the form alters itself to accommodate the choice,

- free text input for a "purchase"
- a drop-down selection box listing owned cryptocurrencies and amount for a "sale"

The form uses JQuery and Ajax to validate the cryptocurrency choice, fills in the "name" field automatically, and then allows input of the remaining information.

### Transaction History

This page displays the ID, symbol, transaction description, price, and date of each transaction. The transaction descriptions specify either "bought" or "sold" along with the amount of currency.

## Further Development

1. The app calls the API too frequently. It would be better to save the results of API calls to a new SQL table and then check that table first. Prices in the SQL table could "expire" after a set time period to prevent display of old information.
