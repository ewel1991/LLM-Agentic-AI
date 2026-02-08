def calculate_calories(weight_kg: float, height_cm: float, age: int, gender: str, activity_level: float) -> float:
    """Calculates TDEE using Mifflin-St Jeor formula."""
    if gender.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    return bmr * activity_level
