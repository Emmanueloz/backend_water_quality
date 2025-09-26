from enum import Enum

from pydantic import BaseModel

from app.share.parameters.domain.model import Parameter


class AlertType(str, Enum):
    DANGEROUS = "dangerous"
    POOR = "poor"
    MODERATE = "moderate"
    GOOD = "good"
    EXCELLENT = "excellent"


class NotificationStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"


class NotificationStatusData(BaseModel):
    status: NotificationStatus


class ParameterDataForAlert(BaseModel):
    alert_id: str
    parameter: str
    value: float


class ResultValidationAlert(BaseModel):
    alerts_ids: list[str] = []
    has_parameters: bool = False
    parameters_data: list[ParameterDataForAlert] = []


class PriorityParameters(list[str], Enum):
    parameters: list[str] = ["ph", "turbidity"]


class RecordParameter(BaseModel):
    parameter: str
    value: float


class AlertData(BaseModel):
    id: str
    title: str
    meter_id: str
    type: AlertType
    user_uid: str
    parameters: Parameter | None = None
    records_of_parameters: list[RecordParameter] = []


class NotificationControl(BaseModel):
    alert_id: str
    validation_count: int
    last_sent: float = None


class NotificationBody(BaseModel):
    id: str = None
    read: bool = False
    title: str
    body: str
    user_ids: list[str]
    timestamp: float | None = None
    status: NotificationStatus | None = None
    alert_id: str | None = None
    record_parameters: list[RecordParameter] = []
    aproved_by: str | None = None


class NotificationBodyDatetime(BaseModel):
    id: str = None
    read: bool = False
    title: str
    body: str
    user_id: str
    datetime: str | float = None
    status: NotificationStatus | None = None


class QueryNotificationParams(BaseModel):
    is_read: bool | None = None
    convert_timestamp: bool = False
