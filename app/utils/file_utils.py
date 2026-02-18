from io import BytesIO
from pathlib import Path
from typing import Union

import pandas as pd
from fastapi import HTTPException, UploadFile
from app.core.logger import get_logger

logger = get_logger(__name__)


async def xlsx_to_dataframe(file: Union[UploadFile, bytes, str, Path]) -> pd.DataFrame:
    if isinstance(file, UploadFile):
        filename = (file.filename or "").lower()
        if not filename.endswith(".xlsx"):
            raise HTTPException(status_code=400, detail="Arquivo deve ser .xlsx")
        content = await file.read()
        return pd.read_excel(BytesIO(content), engine="openpyxl")

    if isinstance(file, bytes):
        return pd.read_excel(BytesIO(file), engine="openpyxl")

    path = Path(file)
    if path.suffix.lower() != ".xlsx":
        raise HTTPException(status_code=400, detail="Arquivo deve ser .xlsx")
    return pd.read_excel(path, engine="openpyxl")
