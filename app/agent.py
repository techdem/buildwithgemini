# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.memory import VertexAiMemoryBankService
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog

from app.database import search_recipes, add_recipe, check_pantry_substitutions
from app.external_tools import search_online_recipes
from app.maps_tools import geocode_address, search_nearby_places
from app.image_tools import generate_recipe_image
from app.executor import get_code_executor
from app.a2ui_utils import a2ui_callback

PROJECT_ID = "qwiklabs-gcp-02-5562d69b56d9"
LOCATION = "us-west1"
AGENT_ENGINE_ID = "1644134921385541632"


async def generate_memories_callback(callback_context: CallbackContext):
    """Sends turn events to Vertex AI Memory Bank after each turn to extract durable user facts, allergies, and dietary preferences."""
    await callback_context.add_session_to_memory()
    return None


memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=AGENT_ENGINE_ID,
)


def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=AGENT_ENGINE_ID,
    )


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description="You are Smart Recipe Agent, an intelligent culinary assistant.",
    workflow_description="Analyze the culinary request and return structured A2UI visual cards when appropriate, or use tools to perform tasks.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects. "
        "\nCRITICAL ALLERGY & MEMORY RULES:\n"
        "- ALWAYS pay close attention to any user allergies or dietary restrictions (e.g., peanuts, tree nuts, gluten, dairy, shellfish, eggs, soy) mentioned in current or previous conversations.\n"
        "- ALL user allergies MUST be remembered across sessions using your Memory Bank integration.\n"
        "- When searching, suggesting, or creating recipes, ALWAYS cross-check ingredients against the user's remembered allergies and explicitly warn or suggest safe allergen-free substitutes.\n\n"
        "TOOL USAGE:\n"
        "- Use `PreloadMemoryTool` (automatically preloaded) to retrieve remembered user facts and allergies at the start of every turn.\n"
        "- Use `search_recipes` to look up local database recipes by cuisine or prep time.\n"
        "- Use `add_recipe` to store new recipes into the database.\n"
        "- Use `check_pantry_substitutions` whenever a user is missing an ingredient or asks for a substitution (especially for allergy-safe alternatives).\n"
        "- Use `search_online_recipes` to search external global recipe databases for meals, dishes, and recipe instructions.\n"
        "- Use `geocode_address` to convert an address or city into latitude and longitude coordinates.\n"
        "- Use `search_nearby_places` to search for nearby supermarkets, grocery stores, or markets near given coordinates.\n"
        "- Use `generate_recipe_image` whenever a user wants a photo, image, or visual preview of a dish or recipe.\n"
        "- Use Python code execution whenever you need to compute unit conversions, nutrition math, or scaling calculations."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        search_recipes,
        add_recipe,
        check_pantry_substitutions,
        search_online_recipes,
        geocode_address,
        search_nearby_places,
        generate_recipe_image,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    code_executor=get_code_executor(),
)

app = App(
    root_agent=root_agent,
    name="app",
)
