from abc import ABC, abstractmethod

from app.features.alerts.domain.model import (
    Alert,
    AlertCreate,
    AlertUpdate,
    AlertQueryParams,
    InfoForSendEmail,
)


class AlertRepository(ABC):
    @abstractmethod
    def is_meter_access(self, user: str, workspace_id: str, meter_id: str) -> bool:
        pass

    @abstractmethod
    def create(self, owner: str, alert: AlertCreate) -> Alert:
        pass

    @abstractmethod
    def get(self, owner: str, alert_id: str) -> Alert:
        pass

    @abstractmethod
    def query(self, owner: str, params: AlertQueryParams) -> list[Alert]:
        pass

    @abstractmethod
    def update(self, owner: str, alert_id: str, alert: AlertUpdate) -> Alert:
        pass

    @abstractmethod
    def delete(self, owner: str, alert_id: str) -> Alert:
        pass

    @abstractmethod
    def get_info_for_send_email(self, alert_id: str) -> InfoForSendEmail:
        pass
