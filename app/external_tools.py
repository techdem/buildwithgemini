import json
import os
import urllib.request
import urllib.parse

def search_online_recipes(query: str) -> str:
    """Searches the public TheMealDB API for online global recipes matching a search term."""
    api_key = os.environ.get("THEMEALDB_API_KEY", "1")
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            
            meals = data.get("meals")
            if not meals:
                return json.dumps({
                    "status": "NO_RESULTS",
                    "query": query,
                    "message": f"No online recipes found matching '{query}'."
                })

            formatted_results = []
            for meal in meals[:3]:  # Return top 3 matches
                # Extract non-empty ingredients
                ingredients = []
                for i in range(1, 21):
                    ing = meal.get(f"strIngredient{i}")
                    measure = meal.get(f"strMeasure{i}")
                    if ing and ing.strip():
                        item_str = f"{measure.strip()} {ing.strip()}" if measure and measure.strip() else ing.strip()
                        ingredients.append(item_str)

                formatted_results.append({
                    "id": meal.get("idMeal"),
                    "title": meal.get("strMeal"),
                    "category": meal.get("strCategory"),
                    "area": meal.get("strArea"),
                    "instructions": meal.get("strInstructions", "")[:300] + "...",
                    "image_url": meal.get("strMealThumb"),
                    "ingredients": ingredients
                })

            return json.dumps({
                "status": "SUCCESS",
                "query": query,
                "count": len(formatted_results),
                "online_recipes": formatted_results
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "ERROR",
            "query": query,
            "message": f"Failed to fetch online recipes from TheMealDB: {str(e)}"
        })
