from fastapi import APIRouter, Depends, HTTPException
from app.features.alerts.domain.model import AlertCreate, AlertUpdate, AlertQueryParams, InfoForSendEmail
from app.features.alerts.domain.response import ResponseAlert, ResponseAlerts
from app.features.alerts.presentation.depends import (
    get_alerts_repo,
    get_notifications_history_repo,
)
from app.share.email.domain.errors import EmailSeedError
from app.share.email.domain.repo import EmailRepository
from app.share.email.infra.html_template import HtmlTemplate
from app.share.email.presentation.depends import get_html_template, get_sender
from app.share.messages.domain.model import AlertType, QueryNotificationParams, NotificationStatusData, NotificationStatus
from app.share.jwt.infrastructure.verify_access_token import verify_access_token
from app.share.messages.domain.repo import NotificationManagerRepository
from app.features.alerts.domain.repo import AlertRepository
from app.share.users.domain.model.user import UserData


alerts_router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
)


@alerts_router.get("/")
async def get_alerts(
    workspace_id: str = None,
    meter_id: str = None,
    type: AlertType = None,
    user=Depends(verify_access_token),
    alert_repo: AlertRepository = Depends(get_alerts_repo),
) -> ResponseAlerts:

    params = AlertQueryParams(
        workspace_id=workspace_id, meter_id=meter_id, type=type)

    alerts = alert_repo.query(owner=user.uid, params=params)

    return ResponseAlerts(message="Alerts retrieved successfully", alerts=alerts)


@alerts_router.get("/notifications/")
async def get_alerts_notifications(
    type: AlertType = None,
    is_read: bool = None,
    convert_timestamp: bool = False,
    user=Depends(verify_access_token),
    notifications_history_repo: NotificationManagerRepository = Depends(
        get_notifications_history_repo
    ),
):

    params = QueryNotificationParams(
        type=type, is_read=is_read, convert_timestamp=convert_timestamp
    )
    notifications = notifications_history_repo.get_history(
        user_uid=user.uid, params=params
    )

    return {
        "message": "Notifications retrieved successfully",
        "notifications": notifications,
    }


@alerts_router.put("/notifications/{notification_id}/")
async def mark_as_read(
    notification_id: str,
    user=Depends(verify_access_token),
    notifications_history_repo: NotificationManagerRepository = Depends(
        get_notifications_history_repo
    ),
):

    notification = notifications_history_repo.mark_as_read(notification_id)

    return {"message": "Notification marked as read", "notification": notification}


@alerts_router.put("/notifications/status/{notification_id}/")
async def update_notification_status(
    notification_id: str,
    status_body: NotificationStatusData,
    user=Depends(verify_access_token),
    notifications_history_repo: NotificationManagerRepository = Depends(
        get_notifications_history_repo
    ),
    alert_repo: AlertRepository = Depends(get_alerts_repo),
    html_template: HtmlTemplate = Depends(get_html_template),
    sender: EmailRepository = Depends(get_sender),
):
    if status_body.status == NotificationStatus.PENDING:
        raise HTTPException(status_code=400, detail="El estado no es válido")

    notification = notifications_history_repo.get_by_id(notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.alert_id is None:
        raise HTTPException(
            status_code=400, detail="Notification has no alert_id")
    if notification.status == NotificationStatus.ACCEPTED or notification.status == NotificationStatus.REJECTED:
        raise HTTPException(
            status_code=404, detail="La notificacion ya esta actualizada")
    info_for_send_email: InfoForSendEmail = alert_repo.get_info_for_send_email(
        alert_id=notification.alert_id)
    info_for_send_email.meter_parameters = notification.record_parameters
    if info_for_send_email.guests_emails and status_body.status == NotificationStatus.ACCEPTED:
        body = html_template.get_critical_alert_notification_email(
            approver_name=user.username or "Usuario", detected_values=info_for_send_email.meter_parameters, meter=info_for_send_email.meter_name,
            workspace=info_for_send_email.workspace_name)
        try:
            sender.send(
                to=info_for_send_email.guests_emails,
                subject=f"Notificación de alerta crítica en medidor {info_for_send_email.meter_name}",
                body=body)
        except EmailSeedError as ese:
            raise HTTPException(
                status_code=ese.status_code, detail=ese.message)

    notifications_history_repo.update_notification_status(
        notification_id, status_body.status, aproved_by=user.email)

    return {"message": "Notification status updated"}


@alerts_router.get("/{id}/")
async def get_alert(
    id: str,
    user=Depends(verify_access_token),
    alert_repo: AlertRepository = Depends(get_alerts_repo),
) -> ResponseAlert:

    alert = alert_repo.get(owner=user.uid, alert_id=id)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    return ResponseAlert(message="Alert retrieved successfully", alert=alert)


@alerts_router.post("/")
async def create_alert(
    alert_body: AlertCreate,
    user: UserData = Depends(verify_access_token),
    alert_repo: AlertRepository = Depends(get_alerts_repo),
) -> ResponseAlert:

    is_access = alert_repo.is_meter_access(
        user.uid, alert_body.workspace_id, alert_body.meter_id
    )

    if not is_access:
        raise HTTPException(
            status_code=403, detail="Access needed to the meter or workspace"
        )

    alert = alert_repo.create(owner=user.uid, alert=alert_body)

    return ResponseAlert(message="Alert created successfully", alert=alert)


@alerts_router.put("/{id}/")
async def update_alert(
    id: str,
    alert_body: AlertUpdate,
    user=Depends(verify_access_token),
    alert_repo: AlertRepository = Depends(get_alerts_repo),
) -> ResponseAlert:
    alert = alert_repo.update(owner=user.uid, alert_id=id, alert=alert_body)

    return ResponseAlert(message="Alert updated successfully", alert=alert)


@alerts_router.delete("/{id}/")
async def delete_alert(
    id: str,
    user=Depends(verify_access_token),
    alert_repo: AlertRepository = Depends(get_alerts_repo),
) -> ResponseAlert:

    alert = alert_repo.delete(owner=user.uid, alert_id=id)

    return ResponseAlert(message="Alert deleted successfully", alert=alert)
