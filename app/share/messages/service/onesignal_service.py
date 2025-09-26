from onesignal import ApiClient, Configuration, ApiException
from onesignal.api.default_api import DefaultApi
from onesignal.model.string_map import StringMap
from onesignal.model.notification import Notification
from app.share.messages.domain.config import ConfigOneSignal
from app.share.messages.domain.model import NotificationBody
from app.share.messages.domain.repo import SenderServiceRepository


class OneSignalService(SenderServiceRepository):

    config = ConfigOneSignal()

    api_client: ApiClient = None

    def get_api_client(self):
        if self.api_client:
            return self.api_client

        # La configuración correcta según la documentación actual
        configuration = Configuration(
            # El header de Authorization debe ser "Basic REST_API_KEY"
            app_key=self.config.api_key,
        )
        self.api_client = ApiClient(configuration)
        return self.api_client

    def create_notification(self, notification: NotificationBody):
        return Notification(
            app_id=self.config.app_id,
            headings=StringMap(en=notification.title),
            contents=StringMap(en=notification.body),
            include_external_user_ids=notification.user_ids,  # Debe ser una lista
        )

    async def send_notification(self, notification: NotificationBody):

        with self.get_api_client() as api_client_context:
            default_api = DefaultApi(api_client_context)

            new_notification = self.create_notification(notification)

            try:

                thread = default_api.create_notification(
                    notification=new_notification)

                print(thread)
            except ApiException as e:
                print("Exception when calling DefaultApi->create_notification: %s\n" % e)
