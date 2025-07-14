from langchain_core.tools import tool


def estimate_body_fat(bmi, age, sex):
    # sex: 1 for male, 0 for female (Deurenberg et al. 1991)
    code = 1 if sex == 'male' else 0
    return 1.20 * bmi + 0.23 * age - 10.8 * code - 5.4


def calculate_ibw(sex, height_cm):
    # Devine formula (metric)
    return (50 + 0.91 * (height_cm - 152.4)) if sex == 'male' else (45.5 + 0.91 * (height_cm - 152.4))


def calculate_adjbw(actual_wt, ibw):
    # AdjBW = IBW + 0.25 * (ActualW - IBW)
    return ibw + 0.25 * (actual_wt - ibw)


def calculate_ffm(actual_wt, bf_pct):
    # FFM = ActualW * (1 - BF%/100)
    return actual_wt * (1 - bf_pct / 100)


activity_factors = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'very': 1.725,
    'extra': 1.9
}

# Macro ratios for remaining calories after protein
macro_ratios = {
    'balanced': {'carbs': 0.55, 'fat': 0.25},
    'keto':     {'carbs': 0.075, 'fat': 0.65}
}


def calculate_bmr(sex, wt, ht, age):
    # Mifflin–St Jeor equation
    return 10 * wt + 6.25 * ht - 5 * age + (5 if sex == 'male' else -161)


def calculate_tdee(bmr, activity):
    return bmr * activity_factors.get(activity, 1.2)


def calculate_macros(cals, prot_g, diet, goal):
    # Initial protein calories
    prot_cal = prot_g * 4
    # For muscle goals, ensure at least 25% of calories from protein
    if goal == 'muscle':
        min_protein_cal = cals * 0.25
        if prot_cal < min_protein_cal:
            prot_cal = min_protein_cal
            prot_g = prot_cal / 4
    # Prevent protein exceeding total calories
    if prot_cal > cals:
        prot_cal = cals * 0.9
        prot_g = prot_cal / 4

    # Distribute remaining calories between carbs and fat
    rem_cal = cals - prot_cal
    ratios = macro_ratios.get(diet, macro_ratios['balanced'])
    total_ratio = ratios['carbs'] + ratios['fat']
    carbs_cal = rem_cal * (ratios['carbs'] / total_ratio)
    fat_cal = rem_cal * (ratios['fat'] / total_ratio)

    # Compute grams
    macros = {
        'protein_g': round(prot_g, 1),
        'carbs_g':   round(carbs_cal / 4, 1),
        'fat_g':     round(fat_cal / 9, 1)
    }

    # Ensure sum matches exactly by allocating tiny remainder to protein
    total_cals = macros['protein_g'] * 4 + \
        macros['carbs_g'] * 4 + macros['fat_g'] * 9
    diff = round(cals - total_cals)
    if abs(diff) >= 1:
        macros['protein_g'] = round(macros['protein_g'] + diff / 4, 1)

    return macros


@tool
def calc_makros(age: int,
                sex: str,
                wt: float,
                ht: float,
                activity: str,
                goal: str,
                diet: str,
                bf_str: float | None,
                surplus: float,
                ppk: float
                ):
    """
    Calculate daily BMR, TDEE, calorie goal, and macronutrients.

    Args:
        age: Age in years
        sex: 'male' or 'female'
        wt: Weight in kg
        ht: Height in cm
        activity: One of sedentary, light, moderate, very, extra
        goal: 'maintain', 'lose', 'gain', or 'muscle'
        diet: 'balanced' or 'keto'
        bf_str: Body fat % or None to estimate
        surplus: % surplus for muscle gain
        ppk: Desired protein g per kg FFM
    """
    sex = sex.lower()
    assert sex in ('male', 'female'), "sex must be 'male' or 'female'"

    # Body fat
    if bf_str is not None:
        bf_pct = bf_str
    else:
        bmi = wt / (ht / 100) ** 2
        bf_pct = estimate_body_fat(bmi, age, 1 if sex == 'male' else 0)

    ibw = calculate_ibw(sex, ht)
    adjbw = calculate_adjbw(wt, ibw)
    ffm = calculate_ffm(wt, bf_pct)

    # Energy
    bmr = calculate_bmr(sex, wt, ht, age)
    tdee = calculate_tdee(bmr, activity)

    # Calorie goal
    if goal == 'lose':
        calories = tdee - 500
    elif goal == 'gain':
        calories = tdee + 500
    elif goal == 'muscle':
        calories = tdee * (1 + surplus / 100)
    else:
        calories = tdee

    # Protein target
    if goal == 'muscle':
        prot_g = ffm * (ppk if ppk else 2.2)
    elif goal == 'lose' and age >= 60:
        prot_g = wt * 1.2
    elif wt > 1.15 * ibw:
        prot_g = adjbw * 1.2
    else:
        prot_g = wt * 1.6

    # Macros calculation with goal-based protein floor
    macros = calculate_macros(calories, prot_g, diet, goal)

    return f"""

BMR: {bmr:.0f} kcal/day

TDEE: {tdee:.0f} kcal/day

Calorie target ({goal}): {calories:.0f} kcal/day
Macros (g/day):
    Protein: {macros['protein_g']:.1f}
    Carbs:   {macros['carbs_g']:.1f}
    Fat:     {macros['fat_g']:.1f}
    """
