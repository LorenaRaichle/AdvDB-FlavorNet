from pathlib import Path

SQL_DIR = Path(__file__).parent.parent.parent / "sql" / "queries"

def load_query(filename: str) -> str:
    path = SQL_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read()