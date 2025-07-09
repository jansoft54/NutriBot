from langchain_core.tools import tool


def estimate_body_fat(bmi, age, sex):
    # sex: 1 for male, 0 for female (Deurenberg et al. 1991)
    return 1.20*bmi + 0.23*age - 10.8*sex - 5.4


def calculate_ibw(sex, height_cm):
    # Devine formula (metric)
    return (50 + 0.91*(height_cm - 152.4)) if sex == 'male' \
        else (45.5 + 0.91*(height_cm - 152.4))


def calculate_adjbw(actual_wt, ibw):
    # AdjBW = IBW + 0.25*(ActualW - IBW)
    return ibw + 0.25*(actual_wt - ibw)


def calculate_ffm(actual_wt, bf_pct):
    # FFM = ActualW * (1 - BF%/100)
    return actual_wt * (1 - bf_pct/100)


activity_factors = {
    'sedentary': 1.2, 'light': 1.375,
    'moderate': 1.55, 'very': 1.725, 'extra': 1.9
}

macro_ratios = {
    'balanced': {'carbs': 0.55, 'fat': 0.25},
    'keto':     {'carbs': 0.075, 'fat': 0.65}
}


def calculate_bmr(sex, wt, ht, age):
    # Mifflin–St Jeor
    return 10*wt + 6.25*ht - 5*age + (5 if sex == 'male' else -161)


def calculate_tdee(bmr, activity):
    return bmr * activity_factors.get(activity, 1.2)


def calculate_macros(cals, prot_g, diet):
    ratios = macro_ratios.get(diet, macro_ratios['balanced'])
    rem = cals - prot_g * 4
    return {
        'protein_g': prot_g,
        'carbs_g':   rem * ratios['carbs'] / 4,
        'fat_g':     rem * ratios['fat'] / 9
    }


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
        Output required Macro nutriens for specified goal

        Args:
            age: Age (yrs) (int)
            sex: (male/female) (string)
            wt: Weight (kg) (float)
            ht: Height (cm) (float)
            activity: Activity choose from (sedentary/light/moderate/very/extra) (string)
            goal: Nutrionial goal choose from (maintain/lose/gain/muscle) (string)
            diet: Diet style choose from (balanced/keto) (string)
            bf_str: Body fat %, Pass None to estiate (float | None)
            surplus: Calory surplus in % (float) Only If muscle gain is specified
            ppk: Protein per kilogram. Choose this depending on the persons requirements. Needs to be higher for muscle gain

    """

    if bf_str:
        bf_pct = float(bf_str)
    else:
        bmi = wt / (ht/100)**2
        sex_code = 1 if sex == 'male' else 0
        bf_pct = estimate_body_fat(bmi, age, sex_code)

    ibw = calculate_ibw(sex, ht)
    adjbw = calculate_adjbw(wt, ibw)
    ffm = calculate_ffm(wt, bf_pct)

    bmr = calculate_bmr(sex, wt, ht, age)
    tdee = calculate_tdee(bmr, activity)

    # Calorie target
    if goal == 'lose':
        calories = tdee - 500
    elif goal == 'gain':
        calories = tdee + 500
    elif goal == 'muscle':
        calories = tdee * (1 + surplus/100)
    else:
        calories = tdee

    # Protein target
    # Obesity dosing
    if wt > 1.15 * ibw:
        prot_g = adjbw * 1.2
    # Older adults in deficit or general lose goal
    elif goal == 'lose' and age >= 60:
        prot_g = wt * 1.2
    # Muscle-focused: allow 1.6–2.2 g/kg FFM
    elif goal == 'muscle':
        prot_g = ffm * (float(ppk) if ppk else 2.5)
    else:
        prot_g = wt * 1.6

    macros = calculate_macros(calories, prot_g, diet)
    return f"""
\nBMR: {bmr:.0f} kcal/day
\nTDEE: {tdee:.0f} kcal/day
\nCalorie target ({goal}): {calories:.0f} kcal/day
Macros (g/day):
    Protein: {macros['protein_g']:.1f}
    Carbs:   {macros['carbs_g']:.1f}
    Fat:     {macros['fat_g']:.1f}
    """
