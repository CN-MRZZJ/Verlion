from datetime import date

POINT_RULE = {1: 9, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}


def scoring_strategy_for_event_type(event_type: str) -> str:
    mapping = {
        "track": "time",
        "field": "length",
        "fun": "count",
    }
    if event_type not in mapping:
        raise ValueError("event_type 必须是 track/field/fun")
    return mapping[event_type]


def age_on_date(birth_date: date, on_date: date) -> int:
    years = on_date.year - birth_date.year
    if (on_date.month, on_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def calc_age_group(gender: str, birth_date: date, meet_date: date) -> str:
    age = age_on_date(birth_date, meet_date)
    if gender == "male":
        if age >= 50:
            return "A"
        if age >= 38:
            return "B"
        return "C"
    if gender == "female":
        if age >= 46:
            return "A"
        if age >= 38:
            return "B"
        return "C"
    raise ValueError("gender 必须是 male 或 female")
