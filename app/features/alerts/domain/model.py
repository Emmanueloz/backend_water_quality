from pydantic import BaseModel
from app.share.messages.domain.model import AlertType, RecordParameter
from app.share.parameters.domain.model import Parameter


class AlertData(BaseModel):
    title: str
    type: AlertType
    workspace_id: str
    meter_id: str
    owner: str
    parameters: Parameter | None
    guests: list[str]


class Alert(AlertData):
    id: str


class AlertCreate(BaseModel):
    title: str
    type: AlertType
    workspace_id: str
    meter_id: str
    parameters: Parameter
    guests: list[str]


class AlertUpdate(BaseModel):
    title: str
    type: AlertType
    parameters: Parameter | None = None
    guests: list[str] | None = None


class AlertQueryParams(BaseModel):
    workspace_id: str | None = None
    meter_id: str | None = None
    type: AlertType | None = None


class InfoForSendEmail(BaseModel):
    workspace_name: str
    meter_name: str
    guests_emails: list[str]
    meter_parameters: list[RecordParameter] = []
