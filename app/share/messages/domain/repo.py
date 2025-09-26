from abc import ABC, abstractmethod

from app.share.messages.domain.model import NotificationBody, NotificationBodyDatetime, NotificationControl, QueryNotificationParams
from app.share.socketio.domain.model import RecordBody


class SenderAlertsRepository(ABC):
    """
    Abstract class for managing alerts queries and operations.
    """

    @abstractmethod
    def send_alerts(self, workspace_id: str, meter_id: str, record: RecordBody) -> None:
        """
        Mark alerts as seen for a specific meter.
        :param meter_id: The ID of the meter.
        """
        pass


class SenderServiceRepository(ABC):
    @abstractmethod
    def send_notification(self, notification: NotificationBody) -> dict:
        pass


class NotificationManagerRepository(ABC):
    """
    Abstract class for managing notifications.
    """

    @abstractmethod
    def create(self, notification: NotificationBody) -> NotificationBody:
        pass

    @abstractmethod
    def mark_as_read(self, notification_id: str) -> NotificationBody:
        pass

    @abstractmethod
    def get_history(self, user_uid: str, params: QueryNotificationParams) -> list[NotificationBody | NotificationBodyDatetime]:
        pass

    @abstractmethod
    def create_control(self, alert: NotificationControl) -> NotificationControl:
        pass

    @abstractmethod
    def get_control(self, alert_id: str) -> NotificationControl:
        pass

    @abstractmethod
    def update_control_validation(self, alert_id: str):
        pass

    @abstractmethod
    def reset_control_validation(self, alert_id: str):
        pass

    @abstractmethod
    def update_control_last_sent(self, alert_id: str, last_sent: float):
        pass

    @abstractmethod
    def update_notification_status(self, notification_id: str, status: str, aproved_by: str):
        pass

    @abstractmethod
    def get_by_id(self, notification_id: str) -> NotificationBody:
        pass
