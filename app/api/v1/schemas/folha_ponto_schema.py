from fastapi import Form
from pydantic import BaseModel
from app.core.logger import get_logger

logger = get_logger(__name__)


class FolhaPontoRequest(BaseModel):
    column_name: str
    column_month: str
    column_contact: str
    template_type: str = "FP"

    @classmethod
    def as_form(
        cls,
        column_name: str = Form(...),
        column_month: str = Form(...),
        column_contact: str = Form(...),
        template_type: str = Form("FP"),
    ):
        return cls(
            column_name=column_name,
            column_month=column_month,
            column_contact=column_contact,
            template_type=template_type,
        )
