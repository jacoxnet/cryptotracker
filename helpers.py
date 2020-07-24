import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session, flash
from functools import wraps
import re



def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code



def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up cryptocurrency quote for symbol
    from api of coinmarketcap.com.
    """

    # return quickly if symbol empty
    if not symbol:
        return None

    quoteurl = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    infourl = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/info"

    parameters = {"symbol": symbol}

    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": ""
    }

    # Contact API

    try:
        response = requests.get(quoteurl, params=parameters, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        response2 = requests.get(infourl, params=parameters, headers=headers)
        response2.raise_for_status()
    except requests.RequestException:
        return None

    # Parse responses
    try:
        quote = response.json()
        info = response2.json()
        returnitem =  {
            "name": quote["data"][symbol]["name"],
            "price": quote["data"][symbol]["quote"]["USD"]["price"],
            "logo": info["data"][symbol]["logo"],
            "cap": quote["data"][symbol]["quote"]["USD"]["market_cap"],
            "vol": quote["data"][symbol]["quote"]["USD"]["volume_24h"],
            "desc": info["data"][symbol]["description"]
        }

        ### debugging
        print("lookup: ", end="")
        print(returnitem)
        return returnitem
    except (KeyError, TypeError, ValueError):
        return None


def complexpassword(password):
    """Check if password complex enough"""

    if len(password) < 8:
        return False
    elif not re.search('[a-z]|[A-Z]', password):
        return False
    elif not re.search('[0-9]', password):
        return False
    return True


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
