advanced_settings = [
    {
        "date": "SAT 31 MAY",
        "court": "Philippe-Chatrier Day",
        "categories": [
            {
                "cat3": 1
            },
            {
                "cat2": 1
            },
            {
                "cat1": 50
            },
            {
                "gold": -1
            },
            {
                "box": None
            }
        ]
    },
    {
        "date": "SAT 31 MAY",
        "court": "Philippe-Chatrier Night",
        "categories": [
            {
                "cat3": 0
            },
            {
                "cat2": 1
            },
            {
                "cat1": None
            },
            {
                "gold": None
            },
            {
                "box": 0
            }
        ]
    },
    {
        "date": "SAT 31 MAY",
        "court": "Suzanne-Lenglen Day",
        "categories": [
            {
                "cat3": None
            },
            {
                "cat2": 1
            },
            {
                "cat1": 1
            },
            {
                "gold": 1
            },
            {
                "box": 1
            }
        ]
    },

    
]

import random

random_advanced_setting = random.choice(advanced_settings)
desired_categories = []
for category_item in random_advanced_setting.get('categories'):
    for category, value in category_item.items():
        desired_categories.append(category) if value and value >= 0 else None

found_category = 'cat3'

desired_category_amount = ''
for category_item in random_advanced_setting.get('categories'):
    for category, value in category_item.items():
        if category == found_category: desired_category_amount = category_item

print(desired_category_amount)