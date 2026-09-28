import json
import logging
import os
from google.cloud import firestore

# IMPORTANT: Hardcode project ID as a string to prevent Agent Platform project-number breaking bug
PROJECT_ID = "qwiklabs-gcp-02-5562d69b56d9"
COLLECTION_NAME = "recipes"

logger = logging.getLogger(__name__)

# Fallback local in-memory/file storage if GCP Firestore is not provisioned in environment
_LOCAL_RECIPES_FILE = os.path.join(os.path.dirname(__file__), "recipes_local.json")

COMMON_SUBSTITUTIONS = {
    "buttermilk": "1 cup milk + 1 tbsp lemon juice or white vinegar (let sit for 5 minutes)",
    "heavy cream": "3/4 cup milk + 1/3 cup melted unsalted butter",
    "egg": "1/4 cup unsweetened applesauce OR 1 tbsp ground flaxseed + 3 tbsp water",
    "sour cream": "Equal amount of plain Greek yogurt",
    "breadcrumbs": "Equal amount of crushed rolled oats or crushed crackers",
    "butter": "Equal amount of coconut oil or vegetable oil (for baking)",
    "garlic": "1/8 tsp garlic powder per garlic clove",
    "soy sauce": "Equal amount of coconut aminos or tamari",
    "cornstarch": "2 tbsp all-purpose flour for every 1 tbsp cornstarch",
    "lemon juice": "Equal amount of lime juice or white wine vinegar"
}

def _load_local_recipes() -> list[dict]:
    if os.path.exists(_LOCAL_RECIPES_FILE):
        try:
            with open(_LOCAL_RECIPES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save_local_recipes(recipes: list[dict]):
    with open(_LOCAL_RECIPES_FILE, "w") as f:
        json.dump(recipes, f, indent=2)

def get_db():
    try:
        return firestore.Client(project=PROJECT_ID)
    except Exception as e:
        logger.warning(f"Failed to create Firestore client for project {PROJECT_ID}: {e}")
        return None

def search_recipes(cuisine: str = "", max_prep_time: int = 0) -> str:
    """Search recipes in the database by cuisine type or maximum preparation time."""
    db = get_db()
    results = []
    
    if db is not None:
        try:
            query = db.collection(COLLECTION_NAME)
            if cuisine:
                query = query.where("cuisine", "==", cuisine)
            
            docs = query.stream()
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                if max_prep_time > 0 and data.get("prep_time_minutes", 0) > max_prep_time:
                    continue
                results.append(data)
        except Exception as e:
            logger.warning(f"Firestore query error: {e}. Falling back to local dataset.")
            db = None

    if db is None:
        local_data = _load_local_recipes()
        for item in local_data:
            if cuisine and item.get("cuisine", "").lower() != cuisine.lower():
                continue
            if max_prep_time > 0 and item.get("prep_time_minutes", 0) > max_prep_time:
                continue
            results.append(item)

    if not results:
        return json.dumps({"status": "NO_MATCHES", "message": f"No recipes found matching cuisine='{cuisine}' and max_prep_time={max_prep_time}."})

    return json.dumps({"status": "SUCCESS", "count": len(results), "recipes": results}, indent=2)

def add_recipe(title: str, cuisine: str, prep_time_minutes: int, ingredients: list[str], instructions: str, dietary_tags: list[str]) -> str:
    """Add a new recipe to the Firestore database."""
    recipe_id = f"recipe-{title.lower().replace(' ', '-')[:20]}"
    recipe_data = {
        "id": recipe_id,
        "title": title,
        "cuisine": cuisine,
        "prep_time_minutes": prep_time_minutes,
        "ingredients": ingredients,
        "instructions": instructions,
        "dietary_tags": dietary_tags,
    }

    db = get_db()
    firestore_success = False

    if db is not None:
        try:
            db.collection(COLLECTION_NAME).document(recipe_id).set(recipe_data)
            firestore_success = True
        except Exception as e:
            logger.warning(f"Firestore set error: {e}. Saving to local backup.")

    # Always persist locally to preserve state across test runs
    local_data = _load_local_recipes()
    local_data = [r for r in local_data if r.get("id") != recipe_id]
    local_data.append(recipe_data)
    _save_local_recipes(local_data)

    return json.dumps({
        "status": "SUCCESS",
        "recipe_id": recipe_id,
        "firestore_saved": firestore_success,
        "recipe": recipe_data
    })

def check_pantry_substitutions(missing_ingredient: str) -> str:
    """Finds culinary substitutes for a missing recipe ingredient."""
    key = missing_ingredient.strip().lower()
    for ingredient, substitute in COMMON_SUBSTITUTIONS.items():
        if ingredient in key or key in ingredient:
            return json.dumps({
                "status": "FOUND",
                "missing_ingredient": missing_ingredient,
                "recommended_substitute": substitute
            })
    return json.dumps({
        "status": "NOT_FOUND",
        "missing_ingredient": missing_ingredient,
        "message": f"No direct substitute found for '{missing_ingredient}'. Try a similar dairy, oil, or starch substitute."
    })
