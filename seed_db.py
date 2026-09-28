#!/usr/bin/env python3
import json
import logging
import os
from google.cloud import firestore

# IMPORTANT: Hardcode project ID as a string for Firestore seeding
PROJECT_ID = "qwiklabs-gcp-02-5562d69b56d9"
COLLECTION_NAME = "recipes"

SEED_RECIPES = [
    {
        "id": "recipe-001",
        "title": "Classic Tuscan Garlic Butter Pasta",
        "cuisine": "Italian",
        "prep_time_minutes": 20,
        "servings": 4,
        "ingredients": [
            "8 oz fettuccine",
            "4 tbsp butter",
            "4 cloves garlic, minced",
            "1/2 cup heavy cream",
            "1/2 cup grated parmesan cheese",
            "1 cup fresh spinach",
            "Salt and black pepper to taste"
        ],
        "instructions": "Cook fettuccine according to package directions. Sauté garlic in butter for 1 minute until fragrant. Stir in heavy cream, parmesan, and spinach until sauce thickens. Toss pasta with garlic butter sauce.",
        "dietary_tags": ["Vegetarian"]
    },
    {
        "id": "recipe-002",
        "title": "Avocado & Chickpea Power Bowl",
        "cuisine": "Mediterranean",
        "prep_time_minutes": 15,
        "servings": 2,
        "ingredients": [
            "1 can chickpeas, drained and rinsed",
            "1 ripe avocado, diced",
            "1 cup cherry tomatoes, halved",
            "1 cup diced cucumber",
            "2 tbsp extra virgin olive oil",
            "1 tbsp lemon juice",
            "1/4 cup crumbled feta cheese"
        ],
        "instructions": "Combine chickpeas, avocado, tomatoes, and cucumber in a bowl. Whisk olive oil and lemon juice together, drizzle over salad, and toss gently. Top with crumbled feta cheese.",
        "dietary_tags": ["Vegetarian", "Gluten-Free"]
    },
    {
        "id": "recipe-003",
        "title": "Teriyaki Tofu Veggie Stir-Fry",
        "cuisine": "Asian",
        "prep_time_minutes": 25,
        "servings": 3,
        "ingredients": [
            "14 oz firm tofu, pressed and cubed",
            "2 cups broccoli florets",
            "1 red bell pepper, sliced",
            "1/3 cup teriyaki sauce",
            "1 tbsp sesame oil",
            "1 tbsp sesame seeds for garnish"
        ],
        "instructions": "Heat sesame oil in a skillet over medium-high heat. Pan-fry tofu cubes until golden brown on all sides. Add broccoli and bell pepper, sauté for 5 minutes. Pour in teriyaki sauce and simmer for 2 minutes until glazed. Garnish with sesame seeds.",
        "dietary_tags": ["Vegan", "Dairy-Free"]
    }
]

def seed_database():
    print(f"Seeding recipes into Firestore for project '{PROJECT_ID}'...")
    
    # 1. Seed to local backup JSON
    local_file = os.path.join(os.path.dirname(__file__), "app", "recipes_local.json")
    with open(local_file, "w") as f:
        json.dump(SEED_RECIPES, f, indent=2)
    print(f"✅ Local backup seed file written to {local_file}")

    # 2. Seed to Cloud Firestore
    try:
        db = firestore.Client(project=PROJECT_ID)
        for recipe in SEED_RECIPES:
            doc_ref = db.collection(COLLECTION_NAME).document(recipe["id"])
            doc_ref.set(recipe)
            print(f"  + Seeded Firestore doc: {recipe['id']} ({recipe['title']})")
        print(f"✅ Successfully seeded {len(SEED_RECIPES)} items to Cloud Firestore collection '{COLLECTION_NAME}'")
    except Exception as e:
        print(f"⚠️ Cloud Firestore seeding notice: {e}")
        print("   Local seed backup is active and available for offline local testing.")

if __name__ == "__main__":
    seed_database()
