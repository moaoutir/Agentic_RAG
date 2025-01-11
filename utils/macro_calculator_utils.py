def bmr_calculation(weightInKgs, heightInCentimeters, age, maleOrFemale):
    if maleOrFemale == "m":
        bmr = int((10 * weightInKgs) + (6.25 * heightInCentimeters) - (5 * age) + 5)
    elif maleOrFemale == "f":
        bmr = int((10 * weightInKgs) + (6.25 * heightInCentimeters) - (5 * age) - 161)

    return bmr

def daily_calorie_needs(activityLevel, goal, bmr):

    activity_levels = {
        1: 1.2,     # Sedentary
        2: 1.375,   # Lightly active
        3: 1.46,    # Moderately active
        4: 1.725,   # Very active
        5: 1.9      # Super active
    }

    activity_level_index = activity_levels.get(activityLevel)

    dailyCaloriesNeeded = int(bmr * activity_level_index)

    goal_adjustments = {
        1: 0,               # Maintain weight
        2: -500,            # Extreme weight loss (0.5 kg/week)
        3: 500,             # Weight gain (0.5 kg/week)
    }

    calorie_adjustment = goal_adjustments.get(goal)
    adjusted_calories = dailyCaloriesNeeded + calorie_adjustment

    print("your daily calories needed: " + str(adjusted_calories) + " calories.")

    return adjusted_calories

def macro_calculator(calories):
    calories_from_protein = int(.4 * calories)
    calories_in_protein = int(calories_from_protein / 4)
    calories_from_carbs = int(.4 * calories)
    calories_in_carbs = int(calories_from_carbs / 4)
    calories_from_fat = int(.2 * calories)
    calories_in_fat = int(calories_from_fat / 9)

    return calories, calories_in_protein, calories_in_carbs, calories_in_fat


def macro_nutrition(weightInKgs, heightInCentimeters, age, activityLevel, goal, maleOrFemale):
    bmr = bmr_calculation(weightInKgs, heightInCentimeters, age, maleOrFemale)
    needed_calories = daily_calorie_needs(activityLevel, goal, bmr)
    return macro_calculator(needed_calories)
    