from datetime import datetime
import time
from firebase_admin import db
from app.share.messages.domain.model import NotificationBody, NotificationBodyDatetime, NotificationControl, QueryNotificationParams, RecordParameter
from app.share.messages.domain.repo import NotificationManagerRepository


class NotificationManagerRepositoryImpl(NotificationManagerRepository):
    """
    Implementation of the NotificationManagerRepository interface.
    This class is responsible for managing notifications.
    """

    def create(self, notification: NotificationBody) -> NotificationBody:
        ref = db.reference("/notifications_history/")

        result = ref.push(notification.model_dump())

        notification.id = result.key

        return notification

    def mark_as_read(self, notification_id: str) -> NotificationBody:

        notification_ref = db.reference(
            f"/notifications_history/{notification_id}/")

        notification_data = notification_ref.get()

        if notification_data is None:
            raise ValueError(
                f"Notification with ID {notification_id} not found.")

        notification_ref.update({"read": True})

        notification = NotificationBody(**notification_data)
        notification.id = notification_id
        notification.read = True
        return notification

    def get_history(self, user_uid: str, params: QueryNotificationParams) -> list[NotificationBody | NotificationBodyDatetime]:

        notifications_ref = db.reference(
            f"/notifications_history/").order_by_child("user_id").equal_to(user_uid)

        notifications_data = notifications_ref.get()
        if notifications_data is None:
            return []

        notifications = []

        for notification_id, notification_data in notifications_data.items():

            notification = None

            if params.convert_timestamp:
                notification = NotificationBodyDatetime(
                    id=notification_id,
                    read=notification_data.get("read"),
                    title=notification_data.get("title"),
                    body=notification_data.get("body"),
                    user_id=notification_data.get("user_id"),
                    datetime=notification_data.get("timestamp"),
                    status=notification_data.get("status") or None
                )
            else:
                notification = NotificationBody(**notification_data)

            notification.id = notification_id

            if params.is_read is not None and notification.read != params.is_read:
                continue

            if params.convert_timestamp:
                notification.datetime = self._convert_timestamp_to_datetime(
                    notification.datetime)

            notifications.append(notification)

        return notifications

    def _convert_timestamp_to_datetime(self, timestamp: float) -> str:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def create_control(self, alert: NotificationControl) -> NotificationControl:
        print("Creating control for alert:", alert.alert_id)
        db.reference(
            f"/notifications_control/{alert.alert_id}/").set(alert.model_dump())
        return alert

    def get_control(self, alert_id: str) -> NotificationControl:
        print("Getting control for alert:", alert_id)

        notification_ref = db.reference(
            f"/notifications_control/{alert_id}/")

        notification_data = notification_ref.get()
        print("Notification data:", notification_data)
        if notification_data is None:
            print("Control not found, creating new one")
            return self.create_control(NotificationControl(
                alert_id=alert_id,
                validation_count=0,
            ))

        notification = NotificationControl(**notification_data)

        return notification

    def update_control_validation(self, alert_id: str):
        ref = db.reference(
            f'/notifications_control/{alert_id}/validation_count')
        current_count = ref.get() or 0
        ref.set(current_count + 1)

    def reset_control_validation(self, alert_id: str):
        # Logic to reset control validation for an alert
        ref = db.reference(
            f'/notifications_control/{alert_id}/validation_count')

        if ref.get() is None:
            return

        ref.set(0)

    def update_control_last_sent(self, alert_id: str, last_sent: float):
        # Logic to update the last sent timestamp for an alert
        ref = db.reference(
            f'/notifications_control/{alert_id}/last_sent')

        ref.set(last_sent)

    def update_notification_status(self, notification_id: str, status: str, aproved_by: str):
        notification_ref = db.reference(
            f"/notifications_history/{notification_id}/")

        notification_data = notification_ref.get()

        if notification_data is None:
            raise ValueError(
                f"Notification with ID {notification_id} not found.")

        notification_ref.update({"status": status, "aproved_by": aproved_by})

    def get_by_id(self, notification_id: str) -> NotificationBody:
        notification_ref = db.reference(
            f"/notifications_history/{notification_id}/")

        notification_data = notification_ref.get()

        if notification_data is None:
            raise ValueError(
                f"Notification with ID {notification_id} not found.")

        pre_record_parameters = notification_data.get(
            "record_parameters") or None
        record_parameters = []
        if pre_record_parameters is not None:
            for record in pre_record_parameters:
                record_parameters.append(
                    RecordParameter(parameter=record.get(
                        "parameter"), value=record.get("value"))
                )

        notification = NotificationBody(
            id=notification_id,
            read=notification_data.get("read"),
            title=notification_data.get("title"),
            body=notification_data.get("body"),
            user_ids=notification_data.get("user_ids"),
            timestamp=notification_data.get("timestamp"),
            status=notification_data.get("status"),
            alert_id=notification_data.get("alert_id"),
            record_parameters=record_parameters
        )
        return notification
