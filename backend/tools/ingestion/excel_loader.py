"""
DataWise AI — Ingestion: Excel Loader
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd


def load_excel(
    file_path: str,
    sheet_name: Optional[Union[str, int]] = 0,
    nrows: Optional[int] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load an Excel (.xlsx, .xls) spreadsheet with metadata."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    excel_file = pd.ExcelFile(file_path)
    sheet_names: List[str] = excel_file.sheet_names
    chosen_sheet = sheet_name if sheet_name is not None else 0

    df = pd.read_excel(excel_file, sheet_name=chosen_sheet, nrows=nrows)

    metadata = {
        "file_path": str(path.resolve()),
        "file_name": path.name,
        "format": "excel",
        "available_sheets": sheet_names,
        "selected_sheet": chosen_sheet if isinstance(chosen_sheet, str) else sheet_names[chosen_sheet],
        "rows": len(df),
        "columns": len(df.columns),
        "memory_bytes": int(df.memory_usage(deep=True).sum()),
    }
    return df, metadata
