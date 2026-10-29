import re
from datetime import date

import accounts


class Blocked(Exception):
    pass


def check_user(user):
    user = str(user).strip().lower()
    if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", user):
        raise Blocked(f"'{user}' is not a valid username")
    if user not in accounts.ACCOUNTS:
        raise Blocked(f"user '{user}' does not exist")
    if not accounts.is_regular(user):
        raise Blocked(f"'{user}' is a system account and cannot be changed")
    return user


def check_days(days, lowest):
    try:
        number = float(days)
        whole = not isinstance(days, bool) and number == int(number)
    except (TypeError, ValueError, OverflowError):
        whole = False
    if not whole:
        raise Blocked(f"days must be a whole number, got {days!r}")
    days = int(number)
    if not lowest <= days <= 99999:
        raise Blocked(f"days must be between {lowest} and 99999")
    return days


def check_date(value):
    value = str(value).strip().lower()
    if value in ("never", "-1"):
        return "-1"
    try:
        date.fromisoformat(value)
    except ValueError:
        raise Blocked("date must look like 2026-12-31, or be 'never'")
    return value


def force_password_change(user):
    user = check_user(user)
    return ["chage", "-d", "0", user], f"Force {user} to choose a new password at next login"


def set_max_days(user, days):
    user, days = check_user(user), check_days(days, -1)
    if days == 0:
        raise Blocked("0 would expire the password immediately; use force_password_change instead")
    return ["chage", "-M", str(days), user], f"Make {user}'s password expire every {days} days"


def set_min_days(user, days):
    user, days = check_user(user), check_days(days, 0)
    return ["chage", "-m", str(days), user], f"Stop {user} changing their password again for {days} days"


def set_warn_days(user, days):
    user, days = check_user(user), check_days(days, 0)
    return ["chage", "-W", str(days), user], f"Warn {user} {days} days before their password expires"


def set_inactive_days(user, days):
    user, days = check_user(user), check_days(days, -1)
    return ["chage", "-I", str(days), user], f"Lock {user} {days} days after their password expires"


def set_account_expiry(user, date):
    user, value = check_user(user), check_date(date)
    return ["chage", "-E", value, user], f"Disable {user}'s account on {'no date (never)' if value == '-1' else value}"


def lock_account(user):
    user = check_user(user)
    return ["passwd", "-l", user], f"Lock {user}'s password"


def unlock_account(user):
    user = check_user(user)
    return ["passwd", "-u", user], f"Unlock {user}'s password"


def get_password_policy(user):
    user = str(user).strip().lower()
    if user not in accounts.ACCOUNTS:
        raise Blocked(f"user '{user}' does not exist")
    return ["chage", "-l", user], f"Read {user}'s password settings"


def list_accounts():
    return ["read", "/etc/shadow"], "Read every account's password settings"


TOOLS = {
    "force_password_change": (force_password_change, "Force a user to choose a new password at their next login."),
    "set_max_days": (set_max_days, "Set how many days a password stays valid. -1 means it never expires."),
    "set_min_days": (set_min_days, "Set how many days must pass before a user may change their password again."),
    "set_warn_days": (set_warn_days, "Set how many days before expiry the user is warned."),
    "set_inactive_days": (set_inactive_days, "Set how many days after expiry the account is locked. -1 turns this off."),
    "set_account_expiry": (set_account_expiry, "Disable the whole account on a date (YYYY-MM-DD), or 'never' to remove the date."),
    "lock_account": (lock_account, "Lock a user's password so they cannot log in with it."),
    "unlock_account": (unlock_account, "Unlock a user's locked password."),
    "get_password_policy": (get_password_policy, "Read one user's password and account settings."),
    "list_accounts": (list_accounts, "Read the password and account settings of every account."),
}
NEEDS_CONFIRMATION = {"lock_account", "set_account_expiry"}
READ_ONLY = {"get_password_policy", "list_accounts"}

PARAMETERS = {
    "user": {"type": "string", "description": "Linux username, for example bob"},
    "days": {"type": "integer", "description": "Number of days"},
    "date": {"type": "string", "description": "YYYY-MM-DD, or 'never'"},
}


def schemas():
    result = []
    for name, (function, description) in TOOLS.items():
        params = function.__code__.co_varnames[:function.__code__.co_argcount]
        result.append({"type": "function", "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": {p: PARAMETERS[p] for p in params}, "required": list(params)},
        }})
    return result
