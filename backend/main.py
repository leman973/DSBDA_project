"""
DSBDA Backend - Data Analysis Assistant API
Uses Gemini API for natural language data analysis
"""

import os
import json
import uuid
import asyncio
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
import pandas as pd
import httpx
import logging
import pdfplumber
import json
import models
from database import engine, get_db
from auth_router import router as auth_router, get_current_user
from dotenv import load_dotenv
from schemas import UserRegister, DatasetInfo as DatasetSchema, ChatRequest, ChatResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment from project and backend .env files when present.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

# Initialize FastAPI
app = FastAPI(
    title="DSBDA Data Analysis API",
    description="Backend for natural language data analysis with LLM",
    version="1.0.0"
)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Configure CORS - Read from environment variable
# Include both localhost and 127.0.0.1 defaults for local dev.
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:80,http://127.0.0.1:80"
).split(",")
logger.info(f"Configuring CORS for origins: {CORS_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(auth_router)

# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB max file size
MAX_ROWS_IN_MEMORY = 100000  # Limit rows for in-memory processing

# Global state (in-memory cache, database is source of truth)
datasets_cache: Dict[str, Dict[str, Any]] = {}

# ============= Data Models =============

class ChatRequest(BaseModel):
    message: str
    dataset_id: str
    history: Optional[List[Dict[str, str]]] = []

    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 5000:
            raise ValueError('Message too long (max 5000 characters)')
        return v.strip()

class ChatResponse(BaseModel):
    response: str
    chart_spec: Optional[Dict[str, Any]] = None
    data: Optional[List[Dict[str, Any]]] = None

class DatasetInfo(BaseModel):
    id: str
    name: str
    rows: int
    columns: int
    columns_info: List[Dict[str, str]]
    created_at: str


def _extract_readable_response(raw_response: str) -> str:
    """Return plain, human-readable text from raw model output."""
    if not raw_response:
        return "I could not generate a response. Please try again."

    text = raw_response.strip()

    def pick_text_field(obj: dict) -> str:
        for key in ("response", "answer", "summary", "text", "message"):
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            extracted = pick_text_field(parsed)
            if extracted:
                return extracted
    except json.JSONDecodeError:
        pass

    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        candidate = text[start:end]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                extracted = pick_text_field(parsed)
                if extracted:
                    return extracted
        except json.JSONDecodeError:
            pass

    # Recover plain text when model returns broken/incomplete JSON text.
    if text.lstrip().startswith("{"):
        match = re.search(r'"response"\s*:\s*"([^"]*)', text, flags=re.DOTALL)
        if match:
            cleaned = match.group(1).replace("\\n", "\n").strip()
            if cleaned:
                return cleaned

        # Last-resort cleanup: remove braces/keys so user never sees raw JSON.
        cleaned = re.sub(r'[\{\}\[\]"]', " ", text)
        cleaned = re.sub(r'\b(response|chart_spec|data)\b\s*:\s*', "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', " ", cleaned).strip()
        if cleaned:
            return cleaned

    return text

# ============= Helper Functions =============

def get_gemini_api_key() -> str:
    """Get Gemini API key from environment."""
    return os.getenv("GEMINI_API_KEY", "").strip()


def get_gemini_model() -> str:
    """Get Gemini model name from environment or use default."""
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_gemini_base_url() -> str:
    return os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")


async def call_gemini(prompt: str, system_prompt: str = "", expect_json: bool = False) -> str:
    """Call Gemini API with configured model."""
    api_key = get_gemini_api_key()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured on the backend."
        )

    model = get_gemini_model()
    url = f"{get_gemini_base_url()}/models/{model}:generateContent"
    generation_config = {
        "temperature": 0.2,
        "maxOutputTokens": 768
    }
    if expect_json:
        generation_config["response_mime_type"] = "application/json"

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt or "You are a helpful data analysis assistant."}]
        },
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": generation_config
    }

    try:
        max_attempts = 3
        async with httpx.AsyncClient(timeout=45.0) as client:
            for attempt in range(1, max_attempts + 1):
                response = await client.post(
                    url,
                    params={"key": api_key},
                    json=payload
                )

                if response.status_code in (401, 403):
                    raise HTTPException(status_code=502, detail="Gemini API authentication failed. Check GEMINI_API_KEY.")
                if response.status_code == 429:
                    if attempt < max_attempts:
                        await asyncio.sleep(0.8 * attempt)
                        continue
                    raise HTTPException(status_code=429, detail="Gemini API rate limit exceeded. Please retry shortly.")
                if response.status_code >= 500:
                    if attempt < max_attempts:
                        await asyncio.sleep(0.8 * attempt)
                        continue
                    raise HTTPException(status_code=503, detail="Gemini API is temporarily unavailable. Please retry.")

                response.raise_for_status()
                result = response.json()
                candidates = result.get("candidates", [])
                if not candidates:
                    raise HTTPException(status_code=502, detail="Gemini returned no response candidates.")

                parts = candidates[0].get("content", {}).get("parts", [])
                text_parts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("text")]
                output = "\n".join(text_parts).strip()
                if not output:
                    raise HTTPException(status_code=502, detail="Gemini response did not include text content.")
                return output

        raise HTTPException(status_code=503, detail="Gemini API is temporarily unavailable. Please retry.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to Gemini timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling Gemini API: {str(e)}")

def load_dataframe(dataset_id: str) -> pd.DataFrame:
    """Load dataset as pandas DataFrame"""
    if dataset_id not in datasets_cache:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset = datasets_cache[dataset_id]
    file_path = dataset["file_path"]
    
    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)
    elif file_path.endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path)
    elif file_path.endswith(".pdf"):
        # Extract tables from PDF using pdfplumber
        with pdfplumber.open(file_path) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        all_tables.append(table)
            if not all_tables:
                raise HTTPException(status_code=400, detail="No tables found in PDF.")
            # Use the first table found
            df = pd.DataFrame(all_tables[0][1:], columns=all_tables[0][0])
            return df
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")

def load_dataframe_from_path(file_path: str) -> pd.DataFrame:
    """Load dataset as pandas DataFrame directly from a file path."""
    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)
    elif file_path.endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path)
    elif file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        all_tables.append(table)
            if not all_tables:
                raise HTTPException(status_code=400, detail="No tables found in PDF.")
            return pd.DataFrame(all_tables[0][1:], columns=all_tables[0][0])
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")


def is_chart_intent(message: str) -> bool:
    """Heuristic detection of chart/visualization intent."""
    text = (message or "").lower()
    chart_keywords = [
        "chart", "plot", "graph", "visual", "visualization", "vega", "vega-lite",
        "bar chart", "line chart", "scatter", "histogram", "pie chart", "donut",
        "box plot", "heatmap", "show trend", "draw"
    ]
    return any(keyword in text for keyword in chart_keywords)


def extract_json_object(text: str) -> Optional[dict]:
    """Best-effort JSON extraction from raw model text."""
    if not text:
        return None
    raw = text.strip()

    # Direct JSON
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # JSON inside markdown/code wrapper
    if "{" in raw and "}" in raw:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        candidate = raw[start:end]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None
    return None


def normalize_chart_payload(raw_text: str) -> dict:
    """Normalize model output into {response, chart_spec, data}."""
    parsed = extract_json_object(raw_text)
    if not parsed:
        return {
            "response": _extract_readable_response(raw_text),
            "chart_spec": None,
            "data": None,
        }

    response_text = parsed.get("response")
    chart_spec = parsed.get("chart_spec")
    data = parsed.get("data")

    # Some models put entire JSON in the `response` string; parse again.
    if (not isinstance(chart_spec, dict) or not isinstance(data, list)) and isinstance(response_text, str):
        nested = extract_json_object(response_text)
        if isinstance(nested, dict):
            response_text = nested.get("response", response_text)
            if isinstance(nested.get("chart_spec"), dict):
                chart_spec = nested.get("chart_spec")
            if isinstance(nested.get("data"), list):
                data = nested.get("data")

    # If chart data was embedded in chart_spec only, mirror it to `data`.
    if isinstance(chart_spec, dict) and not isinstance(data, list):
        values = chart_spec.get("data", {}).get("values") if isinstance(chart_spec.get("data"), dict) else None
        if isinstance(values, list):
            data = values

    return {
        "response": _extract_readable_response(response_text if isinstance(response_text, str) else raw_text),
        "chart_spec": chart_spec if isinstance(chart_spec, dict) else None,
        "data": data if isinstance(data, list) else None,
    }


def build_fallback_chart_payload(df: pd.DataFrame) -> tuple[Optional[dict], Optional[list]]:
    """Create a simple valid Vega-Lite chart when model chart JSON is missing."""
    if df is None or df.empty:
        return None, None

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = [c for c in df.columns if c not in numeric_cols]

    # Prefer line chart for numeric trend by index if only numeric data available.
    if numeric_cols and not cat_cols:
        y_col = numeric_cols[0]
        values = [{"index": int(i), y_col: float(v) if pd.notna(v) else None} for i, v in enumerate(df[y_col].head(50))]
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": f"{y_col} trend",
            "data": {"values": values},
            "mark": {"type": "line", "point": True},
            "encoding": {
                "x": {"field": "index", "type": "quantitative", "title": "Index"},
                "y": {"field": y_col, "type": "quantitative", "title": y_col},
                "tooltip": [{"field": "index"}, {"field": y_col}]
            }
        }
        return spec, values

    # Otherwise build bar chart using first categorical + first numeric.
    if numeric_cols and cat_cols:
        x_col = cat_cols[0]
        y_col = numeric_cols[0]
        grouped = df[[x_col, y_col]].dropna().groupby(x_col, as_index=False)[y_col].mean().head(20)
        values = grouped.to_dict(orient="records")
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": f"Average {y_col} by {x_col}",
            "data": {"values": values},
            "mark": "bar",
            "encoding": {
                "x": {"field": x_col, "type": "nominal", "title": x_col},
                "y": {"field": y_col, "type": "quantitative", "title": f"Average {y_col}"},
                "tooltip": [{"field": x_col}, {"field": y_col}]
            }
        }
        return spec, values

    return None, None

def get_columns_info(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Get information about DataFrame columns"""
    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        col_info = {"name": col, "type": dtype}
        
        # Add sample values for categorical columns
        if df[col].dtype == "object" or df[col].nunique() < 20:
            col_info["unique_values"] = df[col].unique().tolist()[:10]
        
        columns.append(col_info)
    
    return columns

def generate_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a summary of the dataset"""
    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": get_columns_info(df),
        "numeric_summary": {},
        "categorical_summary": {}
    }
    
    # Numeric columns summary
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        summary["numeric_summary"][col] = {
            "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
            "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
            "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
            "median": float(df[col].median()) if not pd.isna(df[col].median()) else None,
            "null_count": int(df[col].isna().sum())
        }
    
    # Categorical columns summary
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in cat_cols:
        summary["categorical_summary"][col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": df[col].value_counts().head(5).to_dict(),
            "null_count": int(df[col].isna().sum())
        }
    
    return summary

# ============= API Endpoints =============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DSBDA Data Analysis API",
        "version": "1.0.0",
        "llm_provider": "gemini",
        "gemini_model": get_gemini_model()
    }

@app.post("/api/datasets/upload", response_model=DatasetSchema)
async def upload_dataset(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a CSV, XLSX, or PDF file (requires authentication)"""
    # Validate file type
    allowed_extensions = [".csv", ".xlsx", ".xls", ".pdf"]
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {allowed_extensions}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique ID
    dataset_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{dataset_id}{file_ext}"
    
    # Save file
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Load and validate data
    try:
        # During upload, dataset is not cached yet, so read directly from saved path.
        df = load_dataframe_from_path(str(file_path))
        
        # Check row limit
        if len(df) > MAX_ROWS_IN_MEMORY:
            # Clean up file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=400,
                detail=f"Dataset too large. Maximum rows: {MAX_ROWS_IN_MEMORY}"
            )
            
    except pd.errors.EmptyDataError:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=400, detail="File is empty")
    except pd.errors.ParserError as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")
    except Exception as e:
        # Clean up file
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Store dataset in database
    columns_info = get_columns_info(df)
    dataset = models.Dataset(
        id=dataset_id,
        name=file.filename,
        file_path=str(file_path),
        original_filename=file.filename,
        rows=len(df),
        columns=len(df.columns),
        columns_info=json.dumps(columns_info),
        owner_id=current_user.id
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    # Cache dataset info for quick access
    datasets_cache[dataset_id] = {
        "id": dataset.id,
        "name": dataset.name,
        "file_path": dataset.file_path,
        "rows": dataset.rows,
        "columns": dataset.columns,
        "columns_info": columns_info,
        "created_at": dataset.created_at.isoformat(),
        "owner_id": dataset.owner_id
    }
    
    return DatasetSchema(**{
        "id": dataset.id,
        "name": dataset.name,
        "rows": dataset.rows,
        "columns": dataset.columns,
        "columns_info": columns_info,
        "created_at": dataset.created_at,
        "owner_id": dataset.owner_id
    })

@app.get("/api/datasets", response_model=List[DatasetSchema])
async def list_datasets(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all datasets owned by the current user"""
    user_datasets = db.query(models.Dataset).filter(
        models.Dataset.owner_id == current_user.id
    ).all()
    
    result = []
    for ds in user_datasets:
        columns_info = json.loads(ds.columns_info) if ds.columns_info else []
        result.append(DatasetSchema(
            id=ds.id,
            name=ds.name,
            rows=ds.rows,
            columns=ds.columns,
            columns_info=columns_info,
            created_at=ds.created_at,
            owner_id=ds.owner_id
        ))
    
    return result

@app.get("/api/datasets/{dataset_id}", response_model=DatasetSchema)
async def get_dataset(
    dataset_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dataset information (requires ownership)"""
    dataset = db.query(models.Dataset).filter(
        models.Dataset.id == dataset_id,
        models.Dataset.owner_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    columns_info = json.loads(dataset.columns_info) if dataset.columns_info else []
    return DatasetSchema(
        id=dataset.id,
        name=dataset.name,
        rows=dataset.rows,
        columns=dataset.columns,
        columns_info=columns_info,
        created_at=dataset.created_at,
        owner_id=dataset.owner_id
    )

@app.get("/api/datasets/{dataset_id}/data")
async def get_dataset_data(
    dataset_id: str, 
    limit: int = 100, 
    offset: int = 0,
    filters: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dataset data with optional pagination and filters (requires ownership)"""
    dataset = db.query(models.Dataset).filter(
        models.Dataset.id == dataset_id,
        models.Dataset.owner_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Validate pagination
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")
    
    try:
        # Load from database-backed file path to work across backend restarts.
        df = load_dataframe_from_path(dataset.file_path)
        
        # Apply filters if provided
        if filters:
            try:
                filter_dict = json.loads(filters)
                for col, value in filter_dict.items():
                    if col in df.columns:
                        df = df[df[col] == value]
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid filter format")
        
        # Apply pagination
        total = len(df)
        df_page = df.iloc[offset:offset + limit]
        
        return {
            "data": df_page.to_dict(orient="records"),
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting dataset data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/datasets/{dataset_id}/summary")
async def get_dataset_summary(
    dataset_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dataset summary with statistics (requires ownership)"""
    dataset = db.query(models.Dataset).filter(
        models.Dataset.id == dataset_id,
        models.Dataset.owner_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Load from database-backed file path to work across backend restarts.
        df = load_dataframe_from_path(dataset.file_path)
        return generate_dataset_summary(df)
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a chat message and get LLM response with data analysis (requires ownership)"""
    
    # Validate dataset exists and user owns it
    dataset = db.query(models.Dataset).filter(
        models.Dataset.id == request.dataset_id,
        models.Dataset.owner_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Load from database-backed file path to work across backend restarts.
        df = load_dataframe_from_path(dataset.file_path)
        dataset_info_cached = datasets_cache.get(request.dataset_id, {})
        
        # Get column information
        columns_info = json.loads(dataset.columns_info) if dataset.columns_info else []
        columns_str = ", ".join([f"{c['name']} ({c['type']})" for c in columns_info])
        
        # Keep context compact for faster responses.
        sample_data = df.head(8).to_csv(index=False)
        chart_mode = is_chart_intent(request.message)
        if chart_mode:
            system_prompt = """You are a data analysis assistant.
Return VALID JSON only with exactly these keys:
{
  "response": "human-readable insight text",
  "chart_spec": <valid Vega-Lite v5 spec object>,
  "data": <array of objects used by chart_spec data.values if needed>
}
Rules:
- response must be clear and concise.
- chart_spec must be valid Vega-Lite JSON.
- Choose suitable chart type based on the user request and data.
- Do not return markdown, code fences, or any extra keys."""
        else:
            system_prompt = """You are a data analysis assistant.
Respond in plain, human-readable text (not JSON).
Keep answers concise, with bullet points and concrete numbers where relevant."""

        # Generate summary statistics for context
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        context = f"""Dataset: {dataset.name}
Columns: {columns_str}

Numeric columns: {numeric_cols}
Categorical columns: {cat_cols}

Sample data (first 8 rows):
{sample_data}

User question: {request.message}"""

        # Call Gemini
        llm_response = await call_gemini(context, system_prompt, expect_json=chart_mode)

        if chart_mode:
            normalized = normalize_chart_payload(llm_response)
            if not isinstance(normalized["chart_spec"], dict):
                fallback_spec, fallback_data = build_fallback_chart_payload(df)
                normalized["chart_spec"] = fallback_spec
                normalized["data"] = fallback_data
            return ChatResponse(
                response=normalized["response"],
                chart_spec=normalized["chart_spec"],
                data=normalized["data"],
            )

        return ChatResponse(response=_extract_readable_response(llm_response))
    
    except HTTPException as e:
        # Keep chat resilient during transient model/provider issues.
        if e.status_code in (429, 503, 504):
            return ChatResponse(
                response="The AI service is temporarily busy. Please retry in a few seconds."
            )
        raise
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dataset (requires ownership)"""
    dataset = db.query(models.Dataset).filter(
        models.Dataset.id == dataset_id,
        models.Dataset.owner_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    file_path = Path(dataset.file_path)
    
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    db.delete(dataset)
    db.commit()
    
    # Remove from cache
    if dataset_id in datasets_cache:
        del datasets_cache[dataset_id]
    
    return {"message": "Dataset deleted successfully"}

@app.get("/api/health")
async def health_check(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Health check endpoint (requires authentication)"""
    gemini_status = "unknown"
    api_key_configured = bool(get_gemini_api_key())

    if api_key_configured:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(
                    f"{get_gemini_base_url()}/models",
                    params={"key": get_gemini_api_key()}
                )
                gemini_status = "connected" if response.status_code == 200 else "error"
        except Exception:
            gemini_status = "disconnected"
    else:
        gemini_status = "not_configured"
    
    # Count user's datasets
    datasets_count = db.query(models.Dataset).filter(
        models.Dataset.owner_id == current_user.id
    ).count()
    
    return {
        "status": "healthy",
        "llm_provider": "gemini",
        "gemini": gemini_status,
        "gemini_model": get_gemini_model(),
        "gemini_api_key_configured": api_key_configured,
        "datasets_count": datasets_count,
        "user": current_user.username
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
