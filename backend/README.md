# DSBDA Project Backend

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Gemini API:
```bash
export GEMINI_API_KEY=your-gemini-api-key
export GEMINI_MODEL=gemini-2.5-flash
```

4. Run the backend:
```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `POST /api/datasets/upload` - Upload a CSV or XLSX file
- `GET /api/datasets` - List all datasets
- `GET /api/datasets/{dataset_id}` - Get dataset info
- `POST /api/chat` - Send a chat message and get LLM response
- `GET /api/datasets/{dataset_id}/data` - Get dataset data (with optional filters)
- `GET /api/datasets/{dataset_id}/summary` - Get dataset summary
