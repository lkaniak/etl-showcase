import inspect
import math
import re
from datetime import datetime, timedelta
from typing import Tuple

DATE_OPERATORS = {
    "eq": lambda x, **kw: x == kw["lower_bound"],
    "lt": lambda x, **kw: x < kw["lower_bound"],
    "lte": lambda x, **kw: x <= kw["lower_bound"],
    "gt": lambda x, **kw: x > kw["upper_bound"],
    "gte": lambda x, **kw: x >= kw["upper_bound"],
    "between": lambda x, **kw: kw["upper_bound"] <= x <= kw["lower_bound"],
}

DATE_PARAMS_PERIOD = {
    "today": lambda: datetime.now(),
    "yesterday": lambda: datetime.now() - timedelta(days=1),
    "last_x_days": lambda x: datetime.now() - timedelta(days=x),
}


def translate_date_period_param(param: str) -> str:
    if m := re.match(r"^last_(\d+)_days$", param):
        days = int(m.group(1))
        return DATE_PARAMS_PERIOD["last_x_days"](days).strftime("%Y-%m-%d")
    if param in DATE_PARAMS_PERIOD:
        return DATE_PARAMS_PERIOD[param]().strftime("%Y-%m-%d")
    return param


def get_next_day(initial_date: datetime) -> datetime:
    return initial_date + timedelta(days=1)


def apply_date_offset(date: datetime, past_days_to_sync: int) -> datetime:
    if not isinstance(date, datetime):
        raise TypeError("date must be a datetime object")
    return date - timedelta(days=past_days_to_sync)


def get_next_x_days(initial_date: datetime, x: int) -> datetime:
    if not isinstance(initial_date, datetime):
        raise TypeError("date must be a datetime object")
    return initial_date + timedelta(days=x)


def get_last_day_of_the_month(initial_date: datetime) -> datetime:
    if not isinstance(initial_date, datetime):
        raise TypeError("date must be a datetime object")
    next_month = initial_date.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def get_first_day_from_next_month(initial_date: datetime) -> datetime:
    if not isinstance(initial_date, datetime):
        raise TypeError("date must be a datetime object")
    next_month = initial_date.replace(day=28) + timedelta(days=4)
    return next_month.replace(day=1)


def get_next_initial_final_dates(
    stop_date: datetime,
    initial_date_func,
    final_date_func,
    initial_date_func_args=None,
    final_date_func_args=None,
) -> Tuple[datetime, datetime]:
    initial_date_func_args = initial_date_func_args or []
    final_date_func_args = final_date_func_args or []
    initial_date_ret = initial_date_func(*initial_date_func_args)
    final_date_ret = final_date_func(initial_date_ret, *final_date_func_args)
    if final_date_ret >= stop_date:
        final_date_ret = stop_date
    return initial_date_ret, final_date_ret


def get_oldest_sync_date(sync_dates: dict, entities: list[str]):
    dates = {entity: sync_dates[entity] for entity in entities}
    return min(dates.items(), key=lambda x: x[1] or "")


def calculate_timeout_based_on_periods(
    initial_date: datetime, stop_date: datetime, period: int, min_timeout: int = 30 * 60
) -> int:
    days_in_period = (stop_date - initial_date).days
    if days_in_period == 0:
        multiply = 1
    elif days_in_period % period != 0:
        multiply = math.ceil(days_in_period / period)
    else:
        multiply = days_in_period // period
    return int(multiply * min_timeout)
