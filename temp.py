random_advanced_setting = {
    "date": "SAT 31 MAY",
    "court": "Court Philippe-Chatrier",
    "session": "day",
    "categories": [
        {
            "category 3": 1
        },
        {
            "category 2": 1
        },
        {
            "category 1": 1
        },
        {
            "category gold": 1
        },
        {
            "box": 1
        }
    ]
}

found_category = 'category 3'
desired_category_amount = {}

result_amount = desired_category_amount 

for category_item in random_advanced_setting.get('categories'):
    for category, value in category_item.items():
        if category == found_category: desired_category_amount = category_item

print(desired_category_amount)
desired_category_to_amount = None
print(desired_category_to_amount.get('someObj'))