from datetime import date, timedelta

NEVER = 99999
EPOCH = date(1970, 1, 1)


def today():
    return (date.today() - EPOCH).days


def to_date(day):
    return (EPOCH + timedelta(days=day)).isoformat()


def fresh():
    t = today()
    return {
        "bob":    {"uid": 1001, "last_change": t - 10,  "min": 0, "max": NEVER, "warn": 7,  "inactive": -1, "expire": -1,     "locked": False},
        "alice":  {"uid": 1002, "last_change": t - 25,  "min": 0, "max": 30,    "warn": 7,  "inactive": -1, "expire": -1,     "locked": False},
        "carol":  {"uid": 1003, "last_change": t - 100, "min": 1, "max": 90,    "warn": 14, "inactive": 7,  "expire": -1,     "locked": True},
        "dave":   {"uid": 1004, "last_change": 0,       "min": 0, "max": 60,    "warn": 7,  "inactive": -1, "expire": t + 45, "locked": False},
        "root":   {"uid": 0,    "last_change": t - 200, "min": 0, "max": NEVER, "warn": 7,  "inactive": -1, "expire": -1,     "locked": False},
        "daemon": {"uid": 1,    "last_change": t - 400, "min": 0, "max": NEVER, "warn": 7,  "inactive": -1, "expire": -1,     "locked": True},
    }


ACCOUNTS = fresh()


def reset():
    ACCOUNTS.clear()
    ACCOUNTS.update(fresh())


def is_regular(user):
    return 1000 <= ACCOUNTS[user]["uid"] <= 60000


def days_left(a):
    if a["last_change"] == 0:
        return 0
    if a["max"] < 0 or a["max"] >= NEVER:
        return None
    return a["last_change"] + a["max"] - today()


def describe(user):
    a = ACCOUNTS[user]
    left = days_left(a)
    return {
        "user": user,
        "uid": a["uid"],
        "system_account": not is_regular(user),
        "locked": a["locked"],
        "must_change_password": a["last_change"] == 0,
        "last_change": "must change" if a["last_change"] == 0 else to_date(a["last_change"]),
        "max_days": "never" if a["max"] >= NEVER else a["max"],
        "min_days": a["min"],
        "warn_days": a["warn"],
        "inactive_days": "off" if a["inactive"] < 0 else a["inactive"],
        "account_expires": "never" if a["expire"] < 0 else to_date(a["expire"]),
        "password_days_left": "never expires" if left is None else left,
    }


def show(field, value):
    if field == "locked":
        return "locked" if value else "unlocked"
    if field == "last_change":
        return "must change" if value == 0 else to_date(value)
    if field == "expire":
        return "never" if value < 0 else to_date(value)
    if field == "max":
        return "never" if value >= NEVER else value
    if field == "inactive":
        return "off" if value < 0 else value
    return value


def apply(argv):
    program, flag, user = argv[0], argv[1], argv[-1]
    a = ACCOUNTS[user]
    before = dict(a)
    if program == "passwd":
        a["locked"] = flag == "-l"
    else:
        value = argv[2]
        field = {"-d": "last_change", "-M": "max", "-m": "min", "-W": "warn", "-I": "inactive", "-E": "expire"}[flag]
        if field == "expire" and value != "-1":
            value = (date.fromisoformat(value) - EPOCH).days
        a[field] = int(value)
        if field == "max" and a["max"] < 0:
            a["max"] = NEVER
    return {key: [show(key, before[key]), show(key, a[key])] for key in a if before[key] != a[key]}
