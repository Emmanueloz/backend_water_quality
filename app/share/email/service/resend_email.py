import resend
from resend.exceptions import ApplicationError
from app.share.email.domain.config import EmailConfig
from app.share.email.domain.errors import EmailSeedError
from app.share.email.domain.repo import EmailRepository


class ResendEmailService(EmailRepository):
    config: EmailConfig = EmailConfig()

    def _validate_email(self, emails: str | list[str]) -> list[str]:
        if isinstance(emails, str):
            emails = [emails]

        # Filtrar None o strings vacíos, eliminar duplicados
        clean_emails = list(
            {
                email.strip()
                for email in emails
                if email and isinstance(email, str) and email.strip()
            }
        )

        return clean_emails

    def send(self, to: str | list[str], subject, body, raise_error=False):
        try:
            resend.api_key = self.config.api_key

            params: resend.Emails.SendParams = {
                "from": "no-reply <no-reply@aqua-minds.org>",
                "to": self._validate_email(emails=to),
                "subject": subject,
                "html": body,
            }
            resend.Emails.send(params)
        except ApplicationError as e:
            print(e.__class__.__name__)
            print(e)

            if raise_error:
                raise EmailSeedError(e.message, e.code)
        except Exception as e:
            print(e.__class__.__name__)
            print(e)
