"""
Personal Trainer RAG Backend
A FastAPI backend that provides personalized workout recommendations using RAG
Now using ExerciseDB API v2 for exercises with videos
"""

import os
import json
import httpx
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Personal Trainer RAG API",
    description="AI-powered workout recommendation system",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === CONSTANTS ===
# ExerciseDB API v2 via RapidAPI
EXERCISEDB_API_HOST = "exercise-db-with-videos-and-images-by-ascendapi.p.rapidapi.com"
EXERCISEDB_API_BASE = f"https://{EXERCISEDB_API_HOST}"

# CDN base URLs for ExerciseDB media (these are free and unlimited!)
EXERCISE_VIDEO_CDN = "https://exercisedb.b-cdn.net/exercises-videos"
EXERCISE_IMAGE_CDN = "https://exercisedb.b-cdn.net/exercises-thumbnails"

# All muscle groups for parsing (updated for ExerciseDB format)
ALL_MUSCLES = [
    "chest", "shoulders", "biceps", "triceps", "forearms",
    "lats", "back", "lower back", "traps",
    "abdominals", "abs", "obliques", "core",
    "quadriceps", "quads", "hamstrings", "glutes", "calves", "adductors", "abductors", "legs"
]

# Muscle mapping to ExerciseDB bodyParts
MUSCLE_TO_BODYPART = {
    "chest": "Chest",
    "shoulders": "Shoulders",
    "biceps": "Upper Arms",
    "triceps": "Upper Arms",
    "forearms": "Lower Arms",
    "lats": "Back",
    "back": "Back",
    "lower back": "Back",
    "traps": "Back",
    "abdominals": "Waist",
    "abs": "Waist",
    "obliques": "Waist",
    "core": "Waist",
    "quadriceps": "Upper Legs",
    "quads": "Upper Legs",
    "hamstrings": "Upper Legs",
    "glutes": "Upper Legs",
    "calves": "Lower Legs",
    "adductors": "Upper Legs",
    "abductors": "Upper Legs",
    "legs": "Upper Legs"
}

EQUIPMENT_TYPES = ["dumbbell", "barbell", "body weight", "cable", "machine", "kettlebell", "band", "medicine ball", "exercise ball"]

# System prompt for Claude
SYSTEM_PROMPT = """You are an elite personal trainer and fitness expert with decades of experience helping clients achieve their fitness goals. Your role is to create personalized, effective workout plans.

When given a set of exercises and a user's workout request, you will:

1. Analyze the user's needs (muscles targeted, equipment available, skill level, time constraints, any injuries/limitations mentioned)
2. Select the most appropriate exercises from the provided list
3. Create a structured workout plan with proper exercise order (compound movements first, isolation later)
4. Provide specific sets and reps recommendations based on the user's goals
5. Explain WHY each exercise is included and how it benefits the user

Your response must be a valid JSON object with this exact structure:
{
  "summary": "A 2-3 sentence overview of the workout plan and its benefits",
  "workout_focus": "Primary focus area (e.g., 'Upper Body Push', 'Leg Day', 'Full Body')",
  "estimated_time": "Estimated workout duration (e.g., '45 minutes')",
  "difficulty": "Overall difficulty level",
  "exercises": [
    {
      "id": "exact exercise id from the provided list",
      "sets": 3,
      "reps": "10-12",
      "rest_seconds": 60,
      "trainer_notes": "Brief coaching tip for this exercise"
    }
  ],
  "warmup_recommendation": "Brief warmup suggestion",
  "cooldown_recommendation": "Brief cooldown suggestion"
}

IMPORTANT:
- Select EXACTLY 3 exercises for a focused, effective workout
- Only use exercise IDs that are provided in the context
- Provide realistic sets/reps based on the user's stated experience level
- Consider exercise order for optimal muscle activation
- Be encouraging and professional in your trainer notes"""

# Cache for exercises
exercises_cache = None


# === PYDANTIC MODELS ===
class WorkoutRequest(BaseModel):
    query: str
    difficulty: Optional[str] = None
    equipment: Optional[list[str]] = None


class ExercisePlan(BaseModel):
    id: str
    sets: int
    reps: str
    rest_seconds: int
    trainer_notes: str


class WorkoutPlan(BaseModel):
    summary: str
    workout_focus: str
    estimated_time: str
    difficulty: str
    exercises: list[ExercisePlan]
    warmup_recommendation: str
    cooldown_recommendation: str


class WorkoutResponse(BaseModel):
    plan: dict
    exercises: list[dict]


# === HELPER FUNCTIONS ===

def get_rapidapi_headers() -> dict:
    """Get headers for RapidAPI requests"""
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="RAPIDAPI_KEY not configured. Please set it in the .env file."
        )
    return {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": EXERCISEDB_API_HOST
    }


async def fetch_exercises() -> list[dict]:
    """Fetch and cache exercises from ExerciseDB API"""
    global exercises_cache
    
    if exercises_cache is not None:
        return exercises_cache
    
    try:
        async with httpx.AsyncClient() as client:
            # Fetch all exercises from ExerciseDB API
            response = await client.get(
                f"{EXERCISEDB_API_BASE}/api/v1/exercises",
                headers=get_rapidapi_headers(),
                params={"limit": 200},  # Hobby plan limit
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle the response structure
            if isinstance(data, dict) and "data" in data:
                exercises_cache = data["data"]
            elif isinstance(data, list):
                exercises_cache = data
            else:
                exercises_cache = []
            
            # Enrich exercises with full CDN URLs (only if relative path)
            for ex in exercises_cache:
                if ex.get("imageUrl"):
                    img_url = ex["imageUrl"]
                    # Only prepend CDN if it's a relative URL
                    if not img_url.startswith("http"):
                        ex["imageUrl"] = f"{EXERCISE_IMAGE_CDN}/{img_url}"
                if ex.get("videoUrl"):
                    vid_url = ex["videoUrl"]
                    # Only prepend CDN if it's a relative URL
                    if not vid_url.startswith("http"):
                        ex["videoUrl"] = f"{EXERCISE_VIDEO_CDN}/{vid_url}"
            
            return exercises_cache
            
    except httpx.HTTPStatusError as e:
        print(f"ExerciseDB API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch exercises: {str(e)}")
    except Exception as e:
        print(f"Error fetching exercises: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch exercises: {str(e)}")


def parse_user_query(query: str, difficulty: Optional[str] = None, equipment: Optional[list[str]] = None) -> dict:
    """Parse user query to extract workout parameters"""
    query_lower = query.lower()
    
    # Extract muscles
    muscles = [muscle for muscle in ALL_MUSCLES if muscle in query_lower]
    
    # Handle muscle group aliases
    if "arms" in query_lower:
        if "biceps" not in muscles:
            muscles.append("biceps")
        if "triceps" not in muscles:
            muscles.append("triceps")
    
    if "upper body" in query_lower:
        muscles.extend(["chest", "shoulders", "biceps", "triceps", "back"])
    
    if "lower body" in query_lower:
        muscles.extend(["quadriceps", "hamstrings", "glutes", "calves"])
    
    if "full body" in query_lower or "total body" in query_lower:
        muscles.extend(["chest", "quadriceps", "back", "shoulders", "abs"])
    
    # Deduplicate
    muscles = list(set(muscles))
    
    # Map to ExerciseDB bodyParts
    body_parts = list(set([MUSCLE_TO_BODYPART.get(m, "Chest") for m in muscles])) if muscles else []
    
    # Extract or use provided difficulty
    parsed_difficulty = difficulty
    if not parsed_difficulty:
        if any(word in query_lower for word in ["beginner", "easy", "new", "starting"]):
            parsed_difficulty = "beginner"
        elif any(word in query_lower for word in ["intermediate", "moderate"]):
            parsed_difficulty = "intermediate"
        elif any(word in query_lower for word in ["advanced", "expert", "hard", "intense"]):
            parsed_difficulty = "expert"
    
    # Extract or use provided equipment
    parsed_equipment = equipment or []
    
    if not parsed_equipment:
        for eq in EQUIPMENT_TYPES:
            if eq in query_lower:
                parsed_equipment.append(eq)
        
        # Handle aliases
        if "bodyweight" in query_lower or "no equipment" in query_lower or "home" in query_lower:
            parsed_equipment.append("body weight")
        if "dumbbells" in query_lower and "dumbbell" not in parsed_equipment:
            parsed_equipment.append("dumbbell")
        if "resistance band" in query_lower and "band" not in parsed_equipment:
            parsed_equipment.append("band")
    
    parsed_equipment = list(set(parsed_equipment))
    
    return {
        "muscles": muscles,
        "body_parts": body_parts,
        "difficulty": parsed_difficulty,
        "equipment": parsed_equipment
    }


def filter_exercises(exercises: list[dict], params: dict) -> list[dict]:
    """Filter exercises based on parsed parameters"""
    filtered = exercises.copy()
    
    # Filter by body parts (ExerciseDB uses bodyParts array)
    if params["body_parts"]:
        filtered = [
            ex for ex in filtered
            if any(
                bp.upper() in [p.upper() for p in ex.get("bodyParts", [])]
                for bp in params["body_parts"]
            )
        ]
    
    # Filter by equipment
    if params["equipment"]:
        equipment_filtered = [
            ex for ex in filtered
            if any(
                eq.lower() in [e.lower() for e in ex.get("equipments", [])]
                for eq in params["equipment"]
            )
        ]
        # Only apply if we still have enough results
        if len(equipment_filtered) >= 3:
            filtered = equipment_filtered
    
    # If we have too few results, expand search
    if len(filtered) < 3:
        filtered = exercises[:30]
    
    # Limit to 30 for context management
    return filtered[:30]


async def generate_workout_plan(query: str, exercises: list[dict]) -> dict:
    """Use Claude API to generate a personalized workout plan"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="ANTHROPIC_API_KEY not configured. Please set it in the .env file."
        )
    
    # Prepare exercise context (adapted for ExerciseDB format)
    exercise_context = [
        {
            "id": ex.get("exerciseId"),
            "name": ex.get("name"),
            "equipment": ex.get("equipments", []),
            "bodyParts": ex.get("bodyParts", []),
            "targetMuscles": ex.get("targetMuscles", []),
            "secondaryMuscles": ex.get("secondaryMuscles", []),
            "exerciseType": ex.get("exerciseType")
        }
        for ex in exercises
    ]
    
    # Call Claude API
    client = anthropic.Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""User's workout request: "{query}"

Available exercises (choose from these ONLY):
{json.dumps(exercise_context, indent=2)}

Create a personalized workout plan based on the user's request. Return ONLY valid JSON."""
            }
        ]
    )
    
    content = message.content[0].text
    
    # Parse JSON from response
    json_str = content
    
    # Handle markdown code blocks
    if "```" in content:
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            json_str = json_match.group(1).strip()
    
    try:
        plan = json.loads(json_str)
        return plan
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")


# === API ENDPOINTS ===

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Personal Trainer RAG API", "version": "2.0 - ExerciseDB"}


@app.get("/api/exercises")
async def get_exercises():
    """Get all exercises from ExerciseDB"""
    try:
        exercises = await fetch_exercises()
        return {"count": len(exercises), "exercises": exercises}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exercises/{exercise_id}")
async def get_exercise(exercise_id: str):
    """Get a specific exercise by ID"""
    exercises = await fetch_exercises()
    
    for ex in exercises:
        if ex.get("exerciseId") == exercise_id:
            return ex
    
    raise HTTPException(status_code=404, detail="Exercise not found")


@app.post("/api/workout")
async def generate_workout(request: WorkoutRequest):
    """Generate a personalized workout plan using RAG"""
    try:
        # Fetch all exercises
        all_exercises = await fetch_exercises()
        
        # Build enhanced query with filters
        enhanced_query = request.query
        if request.difficulty:
            enhanced_query += f" {request.difficulty}"
        if request.equipment:
            enhanced_query += f" with {', '.join(request.equipment)}"
        
        # Parse query and filter exercises
        params = parse_user_query(enhanced_query, request.difficulty, request.equipment)
        relevant_exercises = filter_exercises(all_exercises, params)
        
        if not relevant_exercises:
            raise HTTPException(
                status_code=400,
                detail="No exercises found matching your criteria. Try a different query."
            )
        
        # Generate workout plan with Claude
        plan = await generate_workout_plan(enhanced_query, relevant_exercises)
        
        # Map exercise IDs to full exercise objects
        exercise_map = {ex.get("exerciseId"): ex for ex in all_exercises}
        
        full_exercises = []
        for plan_ex in plan.get("exercises", []):
            ex_id = plan_ex.get("id")
            if ex_id and ex_id in exercise_map:
                full_ex = exercise_map[ex_id].copy()
                full_ex["sets"] = plan_ex.get("sets", 3)
                full_ex["reps"] = plan_ex.get("reps", "10-12")
                full_ex["restSeconds"] = plan_ex.get("rest_seconds", 60)
                full_ex["trainerNotes"] = plan_ex.get("trainer_notes", "")
                
                # Normalize to frontend expected format
                full_ex["id"] = full_ex.get("exerciseId")
                full_ex["primaryMuscles"] = full_ex.get("targetMuscles", [])
                full_ex["equipment"] = ", ".join(full_ex.get("equipments", []))
                full_ex["level"] = "intermediate"  # ExerciseDB doesn't have difficulty levels
                
                # Generate YouTube search URL for exercise video
                import urllib.parse
                exercise_name = full_ex.get("name", "exercise")
                youtube_query = urllib.parse.quote(f"{exercise_name} exercise tutorial")
                full_ex["youtubeSearchUrl"] = f"https://www.youtube.com/results?search_query={youtube_query}"
                
                full_exercises.append(full_ex)
        
        return {
            "plan": plan,
            "exercises": full_exercises
        }
        
    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"AI API Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/filters")
async def get_filters():
    """Get available filter options"""
    exercises = await fetch_exercises()
    
    # Extract unique values
    equipment = set()
    body_parts = set()
    muscles = set()
    
    for ex in exercises:
        for eq in ex.get("equipments", []):
            equipment.add(eq)
        for bp in ex.get("bodyParts", []):
            body_parts.add(bp)
        for m in ex.get("targetMuscles", []):
            muscles.add(m)
        for m in ex.get("secondaryMuscles", []):
            muscles.add(m)
    
    return {
        "equipment": sorted(list(equipment)),
        "bodyParts": sorted(list(body_parts)),
        "muscles": sorted(list(muscles))
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
