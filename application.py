import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd, complexpassword

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///cryptos.db")

# Hashing method used in werkzeug.security.generate_password_hash
HASHING_METHOD = "sha256"

# minimum date
mindate = datetime(2008, 10, 31, 0, 0) # 10-31-08 (Bitcoin paper date!)

@app.route("/")
@login_required
def index():
    """Show summary of cryptocurrency holdings"""

    user_id = session.get("user_id")
    rows = db.execute("SELECT symbol, SUM(quantity) AS squantity FROM transactions WHERE user_id=? GROUP BY symbol", user_id)
    if not rows:
        return apology("error retrieving from database", 400)
    
    # these accumulate current value of all at market
    # and total costs
    totalvalue = 0.0
    totalprofit = 0.0

    # rows is variable to be passed to html page for display
    #       includes: SQL keys symbol, (calculated key) squantity
    #       plus: name, curprice, curvalue [from lookup]
    #       plus profit (calculated from (curval - allcosts)
    #       plus percoin (average cost per coin)
    #
    for row in rows:
        # lookup current price and company name of each symbol
        response = lookup(row["symbol"])
        rows2 = db.execute("SELECT sum((price * quantity) + costs) AS allcosts, sum((price * quantity) + costs) / sum(quantity) AS percoin FROM transactions WHERE quantity > 0 AND user_id=? AND symbol=?", user_id, row["symbol"])
        if not response or not rows2:
            return apology("error looking up symbol or retrieving costs", 400)

        row["name"] = response["name"]
        row["curprice"] = response["price"]
        row["curvalue"] = row["squantity"] * float(response["price"])
        row["profit"] = row["squantity"] * (float(response["price"] - rows2[0]["percoin"]))
        row["percoin"] = rows2[0]["percoin"] 
        row["profit"] = row["curvalue"] - (row["squantity"] * rows2[0]["percoin"])
        row["logo"] = response["logo"]
        totalprofit += row["profit"]
        totalvalue += row["curvalue"]

    return render_template("displayholdings.html", rows=rows, totalvalue=totalvalue, totalprofit=totalprofit)


@app.route("/enter", methods=["GET", "POST"])
@login_required
def enter():
    """Enter cryptocurrency transaction"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # are we selling or buying?
        radio = request.form.get("buysellradio")
        if request.form.get("buysellradio") == "sellradio":
            selling = True
            symbol = request.form.get("ssymbol")
        else:
            selling = False
            symbol = request.form.get("symbol")

        # get and validate remaining data
        if not symbol:
            apology("Invalid symbol", 400)
        symbol = symbol.upper()

        # lookup symbol and validate input
        name = lookup(symbol)["name"]
        if not name:
            apology("Invalid symbol", 400)
        price = request.form.get("price")
        quantity = request.form.get("quantity")
        costs = request.form.get("costs")
        if not costs:
            costs = 0
        if not price or float(price) <= 0:
            apology("Invalid entry for price", 400)
        if not quantity or float(quantity) <= 0:
            apology("Invalid entry for quantity", 400)
        if float(costs) < 0:
            apology("Invalid entry for costs", 400)
        date = request.form.get("date")
        date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")
        if not date or date < mindate or date > datetime.now():
            apology("Invalid date", 400)
        user_id = session.get("user_id")
        # if selling, validate enough coins. Also make quantity negative
        if selling:
            # get number of coins currently held
            rows = db.execute("SELECT SUM(quantity) AS squantity FROM transactions WHERE user_id=? AND symbol=?", user_id, symbol)
            if not rows:
                return apology("error reading from database", 400)
            if rows[0]["squantity"] == None:
                return apology("no coins found to sell", 400)
            if float(quantity) > rows[0]["squantity"]:
                return apology("insufficient coins available to sell", 400)
            quantity = -(float(quantity))
        
        # write validated data to database
        response = db.execute("INSERT INTO transactions (symbol, price, costs, quantity, timestamp, user_id) VALUES(?, ?, ?, ?, ?, ?)", symbol, price, costs, quantity, date.strftime("%s"), user_id)
        if not response:
            apology("Error writing transaction to database", 400)

        flash("Transaction recorded")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        user_id = session.get("user_id")

        # get list of currencies currently held
        currencies = db.execute("SELECT symbol, SUM(quantity) AS squantity FROM transactions WHERE user_id=? GROUP BY symbol", user_id)
        if not currencies:
            return apology("error retrieving coin quantity from database")
        return render_template("enter.html", currencies=currencies)


@app.route('/process', methods = ['POST'])
def process():

    symbol = request.form.get("symbol")

    # if the symbol is blank, return a space as error text
    # so that the fields are cleared
    if not symbol:
        return jsonify({'error': ' '})

    symbol = symbol.upper()
    result = lookup(symbol)
    if not result:
        return jsonify({'error': 'Invalid symbol'})
    else:
        return jsonify({'name': result["name"],
                        'logo': result["logo"],
                        'price': usd(result["price"]),
                        'cap': usd(result["cap"]),
                        'vol': usd(result["vol"]),
                        'desc': result["desc"] })


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    rows = db.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp", session.get("user_id"))
    for i in range(0, len(rows)):
        rows[i]["displaydate"] = datetime.fromtimestamp(rows[i]["timestamp"]).strftime("%m/%d/%Y")
        quantity = float(rows[i]["quantity"])
        rows[i]["trans"] = ("Bought " + str(quantity)) if quantity > 0 else "Sold " + str(-quantity)
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            flash("Please provide a username")
            return render_template("login.html")
            # return apology("must provide username", 403)
        elif not password:
            flash("Please provide a password")
            return render_template("login.html")
            # return apology("must provide password", 403)

        # make usernames case insensitive
        username = username.lower()

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid login")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get cryptocurrency quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("must enter a symbol", 403)

        # lookup symbol (case-insensitive)
        symbol = symbol.upper()
        response = lookup(symbol)
        if response == None:
            return apology("symbol not found", 403)
        else:
            return render_template("displayquote.html", name=response["name"], symbol=response["symbol"], price=response["price"])

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        user_id = session.get("user_id")

        # get list of currencies currently held
        currencies = db.execute("SELECT symbol FROM transactions WHERE user_id=? GROUP BY symbol",
                            user_id)
        for currency in currencies:
            response = lookup(currency["symbol"])
            if response == None:
                return apology("error retrieving currency information", 403)
            currency["logo"] = response["logo"]
            currency["name"] = response["name"]

        return render_template("quoterequest.html", currencies=currencies)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        fullname = request.form.get("fullname")
        username = request.form.get("username")
        password = request.form.get("password")
        passagain = request.form.get("passagain")

        if username == "":
            flash("Must provide username")
            return render_template("register.html")

        # Ensure password was submitted
        elif password == "":
            flash("Must provide a password")
            return render_template("register.html")

        # Ensure passagain was the same as password
        elif password != passagain:
            flash("Password fields didn't match")
            return render_template("register.html")

        elif not complexpassword(password):
            flash("Password must be 8 chars and include letters and numbers")
            return render_template("register.html")
            
        username = username.lower()

        # if no fullname, username is fullname
        if not fullname:
            fullname = username

        # Check whether username in use by querying database
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        if len(rows) > 0:
            return apology("username already in use", "/register")

        # Calc password hash
        hash = generate_password_hash(password, HASHING_METHOD)

        # insert new user into database
        id = db.execute("INSERT INTO users (fullname, username, hash) VALUES(?, ?, ?)",
                        fullname, username, hash)

        if id == None:
            return apology("error adding user", "/register")

        # Remember which user has logged in
        session["user_id"] = id

        # Redirect user to home page
        flash("Registration successful")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, "/")


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

