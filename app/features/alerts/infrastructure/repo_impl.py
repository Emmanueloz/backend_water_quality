from fastapi import HTTPException
from firebase_admin import db
from datetime import datetime
from app.features.alerts.domain.model import (
    Alert,
    AlertCreate,
    AlertData,
    AlertQueryParams,
    AlertCreate,
    AlertUpdate,
    InfoForSendEmail,
)
from app.features.alerts.domain.repo import AlertRepository
from app.share.parameters.domain.model import Parameter
from app.share.workspace.domain.model import WorkspaceRoles
from app.share.workspace.workspace_access import WorkspaceAccess


class AlertRepositoryImpl(AlertRepository):
    def __init__(self, access: WorkspaceAccess):
        self.access = access

    def is_meter_access(self, user: str, workspace_id: str, meter_id: str) -> bool:

        workspace_ref = self.access.get_ref(
            workspace_id,
            user,
            roles=[WorkspaceRoles.ADMINISTRATOR, WorkspaceRoles.MANAGER],
        )

        meter_ref = workspace_ref.ref.child("meters").child(meter_id)

        if meter_ref.get() is None:
            return False

        return True

    def create(self, owner: str, alert: AlertCreate) -> Alert:

        self._validete_guests(alert.workspace_id, alert.guests, owner)

        new_alert = AlertData(
            title=alert.title,
            type=alert.type,
            workspace_id=alert.workspace_id,
            meter_id=alert.meter_id,
            owner=owner,
            parameters=alert.parameters,
            guests=alert.guests
        )

        alert_ref = db.reference("/alerts").push(new_alert.model_dump())

        return Alert(
            id=alert_ref.key,
            title=alert.title,
            type=alert.type,
            workspace_id=alert.workspace_id,
            meter_id=alert.meter_id,
            owner=owner,
            parameters=alert.parameters,
            guests=alert.guests
        )

    def _get_if_owner(
        self,
        owner: str,
        alert_id: str,
        get_alert: bool = False,
        get_ref_alert: bool = False,
    ) -> db.Reference | Alert | tuple[db.Reference, Alert]:

        alert_ref = db.reference("/alerts").child(alert_id)
        alert = alert_ref.get()

        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")

        if alert.get("owner") != owner:
            raise HTTPException(
                status_code=403, detail="No has access to the alert")

        if get_alert:
            return Alert(
                id=alert_id,
                title=alert.get("title"),
                type=alert.get("type"),
                workspace_id=alert.get("workspace_id"),
                meter_id=alert.get("meter_id"),
                owner=alert.get("owner"),
                parameters=alert.get("parameters") or None,
                guests=alert.get("guests") or [],
            )

        if get_ref_alert:
            return alert_ref, Alert(
                id=alert_id,
                title=alert.get("title"),
                type=alert.get("type"),
                workspace_id=alert.get("workspace_id"),
                meter_id=alert.get("meter_id"),
                owner=alert.get("owner"),
                parameters=alert.get("parameters") or None,
                guests=alert.get("guests") or [],
            )

        return alert_ref

    def get(self, owner: str, alert_id: str) -> Alert:

        return self._get_if_owner(owner, alert_id, get_alert=True)

    def query(self, owner: str, params: AlertQueryParams) -> list[Alert]:

        alerts_query = (
            db.reference(
                "/alerts").order_by_child("owner").equal_to(owner).get() or {}
        )

        alerts: list[Alert] = []

        for alert_id, alert_data in alerts_query.items():

            if (
                params.workspace_id is not None
                and alert_data.get("workspace_id") != params.workspace_id
            ):
                continue

            if (
                params.meter_id is not None
                and alert_data.get("meter_id") != params.meter_id
            ):
                continue

            if params.type is not None and alert_data.get("type") != params.type:
                continue

            alert = Alert(
                id=alert_id,
                title=alert_data.get("title"),
                type=alert_data.get("type"),
                workspace_id=alert_data.get("workspace_id"),
                meter_id=alert_data.get("meter_id"),
                owner=alert_data.get("owner"),
                parameters=alert_data.get("parameters") or None,
                guests=alert_data.get("guests") or [],
            )

            alerts.append(alert)

        return alerts

    def update(self, owner: str, alert_id: str, alert: AlertUpdate) -> Alert:

        alert_ref, alert_data = self._get_if_owner(
            owner, alert_id, get_ref_alert=True)

        self._validete_guests(alert_data.workspace_id,
                              alert.guests or [], owner)

        if alert.parameters is not None:
            # obtenemos los parámetros actuales y los actualizamos con los nuevos
            if alert_data.parameters is not None:
                current_parameters = alert_data.parameters.model_dump() or {}
                current_parameters.update(alert.parameters)
                alert.parameters = Parameter(**current_parameters)
        else:
            alert.parameters = alert_data.parameters

        if alert.guests is not None:
            old_guests = alert_data.guests or []
            old_guests.extend(alert.guests)
            new_guests = list(set(old_guests))  # eliminamos duplicados
            alert.guests = new_guests

        alert_ref.update(alert.model_dump())

        return Alert(
            id=alert_id,
            title=alert.title,
            type=alert.type,
            workspace_id=alert_data.workspace_id,
            meter_id=alert_data.meter_id,
            owner=alert_data.owner,
            parameters=alert.parameters,
            guests=alert.guests
        )

    def _update_parameters(self, alert_id: str, parameters: dict) -> None:
        alert_ref = db.reference("/alerts").child(alert_id)
        alert_ref.update({"parameters": parameters})

    def delete(self, owner: str, alert_id: str) -> Alert:

        alert_ref, alert = self._get_if_owner(
            owner, alert_id, get_ref_alert=True)

        alert_ref.delete()

        return alert

    def _get_guest_ids(self, id_workspace: str, user: str) -> list[str]:

        workspace_ref = self.access.get_ref(
            id_workspace, user, roles=[
                WorkspaceRoles.ADMINISTRATOR, WorkspaceRoles.MANAGER]
        )

        guests_ref = workspace_ref.ref.child("guests")

        guests_data = guests_ref.get()

        if guests_data is None:
            return []
        return [guest_id for guest_id in guests_data.keys()]

    def _validete_guests(self, id_workspace: str, guests: list[str], user: str) -> None:
        guest_ids = self._get_guest_ids(id_workspace, user)

        invalid_guests = [guest for guest in guests if guest not in guest_ids]

        if len(invalid_guests) > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Los siguientes invitados no tienen acceso a la workspace: {', '.join(invalid_guests)}",
            )

    def _get_some_info_about_workspace(self, workspace_id: str, user: str, meter_id: str) -> InfoForSendEmail:
        workspace_ref = self.access.get_ref(
            workspace_id, user, roles=[
                WorkspaceRoles.ADMINISTRATOR, WorkspaceRoles.MANAGER]
        )
        workspace_name = workspace_ref.ref.child("name").get()
        meter_data = workspace_ref.ref.child("meters").child(meter_id).get()
        if meter_data is None:
            raise HTTPException(status_code=404, detail="Meter not found")
        meter_name = meter_data.get("name")

        # obtener los invitados de la workspace
        guests_data = workspace_ref.ref.child("guests").get()
        email_guests: list[str] = []
        if guests_data:
            for guest_id, guest in guests_data.items():
                if guest.get("rol") == WorkspaceRoles.VISITOR:
                    guest_detail = self.access.user_repo.get_by_uid(
                        guest_id, limit_data=True)
                    if guest_detail and guest_detail.email:
                        email_guests.append(guest_detail.email)

        return InfoForSendEmail(
            workspace_name=workspace_name,
            meter_name=meter_name,
            guests_emails=email_guests
        )

    def _get_alert_data(self, alert_id: str) -> Alert:
        alert_ref = db.reference("/alerts").child(alert_id)
        alert = alert_ref.get()

        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")

        return Alert(
            id=alert_id,
            title=alert.get("title"),
            type=alert.get("type"),
            workspace_id=alert.get("workspace_id"),
            meter_id=alert.get("meter_id"),
            owner=alert.get("owner"),
            parameters=alert.get("parameters") or None,
            guests=alert.get("guests") or [],
        )

    def get_info_for_send_email(self, alert_id: str) -> InfoForSendEmail:
        alert_data = self._get_alert_data(alert_id)
        info_for_send_email = self._get_some_info_about_workspace(
            alert_data.workspace_id, alert_data.owner, alert_data.meter_id
        )
        info_for_send_email.meter_parameters = alert_data.parameters
        return info_for_send_email
