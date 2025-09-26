from string import Template
from datetime import datetime

from app.share.messages.domain.model import RecordParameter


class HtmlTemplate:

    def get_reset_password(self, username, code: int):

        year = datetime.now().year

        template = Template(
            """
                            <html>
                              <head>
                                <meta charset="UTF-8" />
                                <title>Recuperar contraseña</title>
                              </head>
                              <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 10px; overflow: hidden;">
                                  <tr>
                                    <td style="background-color: #5accc4; padding: 20px; text-align: center; color: white;">
                                      <h2>Recuperar contraseña</h2>
                                    </td>
                                  </tr>
                                  <tr>
                                    <td style="padding: 30px;">
                                      <p style="font-size: 16px;">Hola <strong> ${username} </strong>,</p>
                                      <p style="font-size: 15px;">
                                        Recibimos una solicitud para restablecer tu contraseña en la plataforma de calidad de agua.
                                      </p>
                                      <p style="font-size: 15px;">
                                        Usa el siguiente código para continuar con el proceso:
                                      </p>
                                      <div style="margin: 20px auto; text-align: center;">
                                        <span style="display: inline-block; background-color: #e9f5f3; color: #004e49; font-size: 24px; padding: 10px 20px; border-radius: 8px; letter-spacing: 4px;">
                                          ${code}
                                        </span>
                                      </div>
                                      <p style="font-size: 14px; color: #555;">Este código es válido por 10 minutos.</p>
                                      <p style="font-size: 14px; color: #555;">Si no solicitaste este cambio, puedes ignorar este mensaje.</p>
                                    </td>
                                  </tr>
                                  <tr>
                                    <td style="background-color: #eeeeee; text-align: center; padding: 15px; font-size: 12px; color: #999;">
                                      © ${year} aqua-minds.org. Todos los derechos reservados.
                                    </td>
                                  </tr>
                                </table>
                              </body>
                            </html>"""
        )
        template = template.substitute(username=username, code=code, year=year)
        return template

    def get_guest_workspace(self, username, owner, id_workspace):
        url_workspace = f"https://aqua-minds.org/#/workspaces/{id_workspace}"

        template = Template(
            """
                            <html>
                              <head>
                                <meta charset="UTF-8" />
                                <title>Invitación a espacio de trabajo</title>
                              </head>
                              <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 10px; overflow: hidden;">
                                  <tr>
                                    <td style="background-color: #5accc4; padding: 20px; text-align: center; color: white;">
                                      <h2>Invitación a espacio de trabajo</h2>
                                    </td>
                                  </tr>
                                  <tr>
                                    <td style="padding: 30px;">
                                      <p style="font-size: 16px;">Hola <strong>${username}</strong>,</p>
                                      <p style="font-size: 15px;">
                                        Has sido invitado por <strong>${owner}</strong> a unirte a un espacio de trabajo en la plataforma de calidad de agua.
                                      </p>
                                      <p style="font-size: 15px;">
                                        Puedes acceder al espacio haciendo clic en el siguiente botón:
                                      </p>
                                      <div style="margin: 20px auto; text-align: center;">
                                        <a href="${url}" target="_blank" style="display: inline-block; background-color: #145c57; color: white; font-size: 16px; padding: 12px 24px; border-radius: 6px; text-decoration: none;">
                                          Unirme al espacio
                                        </a>
                                      </div>
                                    </td>
                                  </tr>
                                  <tr>
                                    <td style="background-color: #eeeeee; text-align: center; padding: 15px; font-size: 12px; color: #999;">© ${year} aqua-minds.org. Todos los derechos reservados.
                                    </td>
                                  </tr>
                                </table>
                              </body>
                            </html>"""
        )

        template = template.substitute(
            username=username, owner=owner, url=url_workspace, year=datetime.now().year
        )

        return template

    def get_analysis_notification(
        self,
        id_analysis: str,
        action: str,
        start_date: str,
        end_date: str,
        analysis_type: str,
    ) -> str:
        url_analysis = f"https://aqua-minds.org/#/analysis/{id_analysis}"
        template = Template(
            """
                        <html>
                          <head>
                            <meta charset="UTF-8" />
                            <title>Notificación de análisis</title>
                          </head>
                          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 10px; overflow: hidden;">
                              <tr>
                                <td style="background-color: #5accc4; padding: 20px; text-align: center; color: white;">
                                  <h2>Notificación de análisis</h2>
                                </td>
                              </tr>
                              <tr>
                                <td style="padding: 30px;">
                                  <p style="font-size: 16px;">Hola</p>
                                  <p style="font-size: 15px;">
                                    Tu análisis de tipo <strong>${analysis_type}</strong> ha sido <strong>${action}</strong>.
                                  </p>
                                  <p style="font-size: 15px;">
                                    <strong>Rango de fechas:</strong> ${start_date} a ${end_date}
                                  </p>
                                  
                                  <div style="margin: 20px auto; text-align: center;">
                                    <a href="${url}" target="_blank" style="display: inline-block; background-color: #145c57; color: white; font-size: 16px; padding: 12px 24px; border-radius: 6px; text-decoration: none;">
                                      Ver análisis
                                    </a>
                                  </div>
                                </td>
                              </tr>
                              <tr>
                                <td style="background-color: #eeeeee; text-align: center; padding: 15px; font-size: 12px; color: #999;">© ${year} aqua-minds.org. Todos los derechos reservados.
                                </td>
                              </tr>
                            </table>
                          </body>
                        </html>"""
        )
        template = template.substitute(
            action=action,
            analysis_type=analysis_type,
            start_date=start_date,
            end_date=end_date,
            url=url_analysis,
            year=datetime.now().year,
        )
        return template

    def get_critical_alert_notification_email(
        self,
        workspace: str,
        meter: str,
        detected_values: list[RecordParameter],
        approver_name: str,
    ) -> str:
        """
        Correo base que se enviará a Managers/Visitors cuando un admin/owner apruebe la alerta
        (el contenido es preescrito; sólo cambian workspace, medidor y valores detectados).
        """
        year = datetime.now().year
        template = Template("""
        <html>
          <head>
            <meta charset="UTF-8" />
            <title>Notificación: Alerta crítica aprobada</title>
          </head>
          <body style="font-family: Arial, sans-serif; background:#f4f6f8; padding:20px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width:640px; margin:auto; background:white; border-radius:8px;">
              <tr>
                <td style="background:#145c57; padding:16px; color:white; text-align:center;">
                  <h2 style="margin:0">Alerta crítica aprobada</h2>
                </td>
              </tr>

              <tr>
                <td style="padding:20px;">
                  <p style="font-size:15px;">Hola,</p>
                  <p style="font-size:14px; margin:6px 0;">
                    Se ha aprobado una alerta crítica en el espacio <strong>${workspace}</strong> por <strong>${approver_name}</strong>.
                  </p>

                  <p style="font-size:14px; margin:8px 0;"><strong>Medidor:</strong> ${meter}</p>

                  <p style="font-size:14px; margin:8px 0;"><strong>Valores detectados:</strong></p>
                  <table cellpadding="8" cellspacing="0" width="100%" style="border:1px solid #e9e9e9; border-collapse:collapse;">
                    <thead style="background:#f7f7f7;">
                      <tr><th align="left">Parámetro</th><th align="left">Valor</th></tr>
                    </thead>
                    <tbody>
                      ${detected_rows}
                    </tbody>
                  </table>
                </td>
              </tr>

              <tr>
                <td style="background:#fafafa; text-align:center; padding:12px; font-size:12px; color:#999;">
                  © ${year} aqua-minds.org
                </td>
              </tr>
            </table>
          </body>
        </html>
        """)

        rows = []
        for record in detected_values:
            rows.append(
                f"<tr><td style='border-top:1px solid #eee;'>{record.parameter}</td><td style='border-top:1px solid #eee;'>{record.value}</td></tr>")
        detected_rows = "\n".join(rows)
        template = template.substitute(
            workspace=workspace,
            meter=meter,
            detected_rows=detected_rows,
            approver_name=approver_name,
            year=year
        )

        return template
