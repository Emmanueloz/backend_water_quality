from firebase_admin import db
import time
from datetime import datetime, timezone
from app.share.messages.domain.model import AlertData, NotificationControl,  NotificationBody, NotificationStatus, RecordParameter
from app.share.messages.domain.repo import NotificationManagerRepository, SenderAlertsRepository, SenderServiceRepository
from app.share.messages.domain.validate import RecordValidation
from app.share.socketio.domain.model import RecordBody
from app.share.workspace.domain.model import WorkspaceRoles


class SenderAlertsRepositoryImpl(SenderAlertsRepository):
    def __init__(self, sender_service: SenderServiceRepository, notification_manager: NotificationManagerRepository):
        self.sender_service = sender_service
        self.notification_manager = notification_manager

    def _list_alerts_by_meter(self, meter_id: str) -> list[AlertData]:
        # Fetch alerts for the given meter_id from Firebase Realtime Database
        ref = db.reference().child("alerts").order_by_child("meter_id").equal_to(meter_id)

        alerts_data = ref.get()

        alerts = []

        for alert_id, alert in alerts_data.items():

            alerts.append(AlertData(
                id=alert_id,
                meter_id=alert.get('meter_id'),
                title=alert.get('title'),
                type=alert.get('type'),
                user_uid=alert.get('owner'),
                parameters=alert.get('parameters') or None,
            ))

        return alerts

    def _get_owner_of_workspace(self, workspace_id: str) -> str:
        ref = db.reference().child("workspaces").child(workspace_id).child("owner")
        owner_data = ref.get()
        return owner_data

    def _get_managers_of_workspace(self, workspace_id: str) -> list[str]:
        ref = db.reference().child("workspaces").child(workspace_id).child("guests")
        guests_data = ref.get()
        if not guests_data:
            return []
        managers = []
        for guest_id, guest in guests_data.items():
            if guest.get("rol") == WorkspaceRoles.MANAGER:
                managers.append(guest_id)
        return managers

    def _validate_records(self, meter_id, records: RecordBody) -> list[AlertData]:
        alerts = self._list_alerts_by_meter(meter_id)

        if not alerts:
            print("Not found alerts for meter")
            return []

        result_validation_alert = RecordValidation.validate(
            record=records, alerts=alerts)

        if not result_validation_alert.has_parameters:
            print("Not found parameters in alerts")
            return []

        if not result_validation_alert.alerts_ids:
            alerts_ids = [alert.id for alert in alerts]

            for alert_id in alerts_ids:
                self.notification_manager.reset_control_validation(
                    alert_id=alert_id)

            print("Not found alert type")
            return []

        alerts_not_validated = [
            alert for alert in alerts if alert.id not in result_validation_alert.alerts_ids]

        for alert in alerts_not_validated:
            self.notification_manager.reset_control_validation(
                alert_id=alert.id)

        alerts_validated = []

        for alert in alerts:
            if alert.id in result_validation_alert.alerts_ids:
                # Add the records of parameters that triggered the alert
                alert.records_of_parameters = [
                    RecordParameter(parameter=param_data.parameter, value=param_data.value) for param_data in result_validation_alert.parameters_data if param_data.alert_id == alert.id
                ]
                alerts_validated.append(alert)

        return alerts_validated

    def _was_sent_today(self, last_sent: float | None) -> bool:
        if not last_sent:
            return False
        # Convert the timestamp to a datetime object
        last_date = datetime.fromtimestamp(last_sent, tz=timezone.utc).date()

        return last_date == datetime.now(timezone.utc).date()

    async def send_alerts(self, workspace_id: str,  meter_id: str, records: RecordBody):
        alert_valid = self._validate_records(meter_id, records=records)

        if not alert_valid:
            print("Not found alerts for validation")
            return

        print(alert_valid)
        # Get the list of managers and owner of the workspace
        owner = self._get_owner_of_workspace(workspace_id=workspace_id)
        managers = self._get_managers_of_workspace(workspace_id=workspace_id)
        recipients = managers + [owner]
        recipients = self._remove_duplicate_user_ids(recipients)

        for alert in alert_valid:
            # Check if the alert is already validated

            notification_control = self.notification_manager.get_control(
                alert_id=alert.id)

            if notification_control.last_sent is not None and self._was_sent_today(notification_control.last_sent):
                continue

            if notification_control.validation_count < 100:
                self.notification_manager.update_control_validation(
                    alert_id=alert.id)
                continue
            # Send notification
            notification = NotificationBody(
                title=alert.title,
                body=f"Alert Type {alert.type.value.capitalize()} for meter {alert.meter_id}",
                user_ids=recipients,
                timestamp=time.time(),
                status=NotificationStatus.PENDING,
                alert_id=alert.id,
                record_parameters=alert.records_of_parameters
            )

            await self.sender_service.send_notification(notification)

            # Update the notification count in Firebase
            self.notification_manager.update_control_last_sent(
                alert_id=alert.id, last_sent=notification.timestamp)
            self.notification_manager.reset_control_validation(
                alert_id=alert.id)

            self.notification_manager.update_control_last_sent(
                alert_id=alert.id, last_sent=notification.timestamp)

            self.notification_manager.create(notification)

            print(
                f"Notification sent to {alert.user_uid} for alert {alert.id}")

    def _remove_duplicate_user_ids(self, user_ids: list[str]) -> list[str]:
        return list(set(user_ids))
