from dataclasses import dataclass
from fastapi import File, Form, UploadFile
from app.core.logger import get_logger

logger = get_logger(__name__)

@dataclass
class FolhaPontoUploadRequest:
    file: UploadFile
    column_name: str
    column_month: str
    column_contact: str
    template_type: str = "FP"

    @classmethod
    def as_form(
        cls,
        file: UploadFile = File(...),
        column_name: str = Form(...),
        column_month: str = Form(...),
        column_contact: str = Form(...),
        template_type: str = Form("FP"),
    ):
        return cls(
            file=file,
            column_name=column_name,
            column_month=column_month,
            column_contact=column_contact,
            template_type=template_type,
        )
