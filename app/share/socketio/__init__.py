from fastapi import HTTPException
from socketio import AsyncServer, ASGIApp
from fastapi import BackgroundTasks
from app.share.messages.infra.notification_manager import (
    NotificationManagerRepositoryImpl,
)
from app.share.messages.infra.sender_alerts import SenderAlertsRepositoryImpl
from app.share.jwt.domain.payload import MeterPayload, UserPayload
from app.share.jwt.infrastructure.access_token import AccessToken
from app.share.messages.service.onesignal_service import OneSignalService
from app.share.socketio.domain.enum.meter_connection_state import MeterConnectionState
from app.share.socketio.domain.model import RecordBody
from app.share.socketio.infra.meter_status_repo_impl import MeterStateRepositoryImpl
from app.share.socketio.infra.record_repo_impl import RecordRepositoryImpl
from app.share.socketio.infra.session_repo_impl import (
    SessionMeterSocketIORepositoryImpl,
)

from app.share.socketio.util.query_string_to_dict import query_string_to_dict
from app.share.users.infra.users_repo_impl import UserRepositoryImpl
from app.share.workspace.domain.model import WorkspaceRoles
from app.share.workspace.workspace_access import WorkspaceAccess

sio = AsyncServer(cors_allowed_origins="*", async_mode="asgi")
socket_app = ASGIApp(sio)

access_token_connection = AccessToken[MeterPayload]()
access_token_user = AccessToken[UserPayload]()

workspace_access = WorkspaceAccess(user_repo=UserRepositoryImpl())

record_repo = RecordRepositoryImpl()

meter_state_repo = MeterStateRepositoryImpl()

background_tasks = BackgroundTasks()

onesignal = OneSignalService()
notification_manager = NotificationManagerRepositoryImpl()
sender = SenderAlertsRepositoryImpl(
    sender_service=onesignal, notification_manager=notification_manager
)


@sio.on("connect", namespace="/receive/")
async def receive_connection(sid, environ):
    try:
        print(f"📡 Nuevo conexión en receive: {sid}")

        query_dict = query_string_to_dict(environ.get("QUERY_STRING") or "")

        token = environ.get(
            "HTTP_ACCESS_TOKEN") or query_dict.get("access_token")

        if not token:
            raise Exception("Access token is required")

        decoded_token = access_token_connection.validate(token)

        payload = MeterPayload(**decoded_token)

        meter_state_repo.set_state(
            payload.id_workspace, payload.id_meter, MeterConnectionState.CONNECTED
        )

        # Guardar información del medidor
        SessionMeterSocketIORepositoryImpl.add(sid, payload)
    except Exception as e:
        print(e)
        print(f"📡 Desconexión: {sid}")
        await sio.disconnect(sid, namespace="/receive/")


@sio.on("message", namespace="/receive/")
async def receive_message(sid, data: dict):

    # Obtener información del medidor
    payload = SessionMeterSocketIORepositoryImpl.get(sid)
    print(f"Payload del medidor: {payload}")

    room_name = f"{payload.id_workspace}-{payload.id_meter}"

    try:
        record_body = RecordBody(**data)

        meter_state_repo.set_state(
            payload.id_workspace, payload.id_meter, MeterConnectionState.SENDING_DATA
        )

        response = record_repo.add(payload, record_body)
        # print(response.model_dump())
        """
        background_tasks.add_task(
            sender.send_alerts, payload.id_meter, record_body)
        """
        await sender.send_alerts(workspace_id=payload.id_workspace, meter_id=payload.id_meter, records=record_body)
        await sio.emit(
            "message",
            response.model_dump(mode="json"),
            namespace="/subscribe/",
            room=room_name,
        )
        print(f"📤 Mensaje enviado a sala {room_name} en namespace /subscribe/")

    except Exception as e:
        print(e.__class__.__name__)
        print(e)
        await sio.emit(
            "error",
            f"Error: {e.__class__.__name__}",
            namespace="/subscribe/",
            room=room_name,
        )


@sio.on("disconnect", namespace="/receive/")
async def receive_disconnection(sid):
    print(f"📡 Desconexión de receive: {sid}")
    payload = SessionMeterSocketIORepositoryImpl.get(sid)

    if payload is not None:
        meter_state_repo.set_state(
            id_workspace=payload.id_workspace,
            id_meter=payload.id_meter,
            state=MeterConnectionState.DISCONNECTED,
        )

    SessionMeterSocketIORepositoryImpl.delete(sid)
    await sio.emit("disconnect", sid, namespace="/receive/")


@sio.on("connect", namespace="/subscribe/")
async def subscribe_connection(sid, environ):

    try:
        print(f"📡 Nuevo conexión en subscribe: {sid}")
        query_dict = query_string_to_dict(environ.get("QUERY_STRING") or "")

        token = environ.get(
            "HTTP_ACCESS_TOKEN") or query_dict.get("access_token")

        if not token:
            raise Exception("Access token is required")

        decoded_token = access_token_user.validate(token)
        user_payload = UserPayload(**decoded_token)

        id_workspace = query_dict.get("id_workspace")
        id_meter = query_dict.get("id_meter")

        if id_workspace is None or id_meter is None:
            await sio.disconnect(sid, namespace="/subscribe/")
            return

        work_ref = workspace_access.get_ref(
            workspace_id=id_workspace,
            user=user_payload.uid,
            roles=[
                WorkspaceRoles.VISITOR,
                WorkspaceRoles.MANAGER,
                WorkspaceRoles.ADMINISTRATOR,
            ],
            is_public=True,
        )

        if work_ref.ref.get(shallow=True) is None:
            await sio.disconnect(sid, namespace="/subscribe/")
            return

        room_name = f"{id_workspace}-{id_meter}"

        # Crear la sala con el email del usuario
        await sio.enter_room(sid, room_name, namespace="/subscribe/")
        print(
            f"🔗 Cliente {sid} unido a la sala {room_name} en namespace /subscribe/")

    except Exception as e:
        print(e.__class__.__name__)
        print(e)
        await sio.disconnect(sid, namespace="/subscribe/")
        return


@sio.on("disconnect", namespace="/subscribe/")
async def subscribe_disconnection(sid):
    print(f"📡 Desconexión de subscribe: {sid}")
