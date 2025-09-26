from app.share.socketio.domain.model import RecordBody
from app.share.messages.domain.model import AlertData, PriorityParameters, ResultValidationAlert, ParameterDataForAlert
from app.share.meter_records.domain.enums import SensorType


class RecordValidation:

    @classmethod
    def validate(cls, record: RecordBody, alerts: list[AlertData]) -> ResultValidationAlert:
        parameters_and_ranges = [
            alert.parameters for alert in alerts if alert.parameters]
        result_validation_alert = ResultValidationAlert()
        if not parameters_and_ranges:
            return result_validation_alert

        print(f"Found {len(parameters_and_ranges)} alerts with parameters")

        values: dict[SensorType, float] = {
            SensorType.TEMPERATURE: record.temperature,
            SensorType.TDS: record.tds,
            SensorType.CONDUCTIVITY: record.conductivity,
            SensorType.PH: record.ph,
            SensorType.TURBIDITY: record.turbidity,
        }

        result_validation_alert.has_parameters = True

        for alert in alerts:
            if not alert.parameters:
                continue
            valid_params_count = 0
            for param, range_param in alert.parameters.model_dump().items():
                sensor_value = values.get(param)
                if not (range_param.get('min') <= sensor_value <= range_param.get('max')):
                    continue
                if param in PriorityParameters.parameters:
                    result_validation_alert.alerts_ids.append(alert.id)
                    result_validation_alert.parameters_data.append(
                        ParameterDataForAlert(
                            alert_id=alert.id,
                            parameter=param,
                            value=sensor_value
                        )
                    )
                    continue
                valid_params_count += 1
                result_validation_alert.parameters_data.append(
                    ParameterDataForAlert(
                        alert_id=alert.id,
                        parameter=param,
                        value=sensor_value
                    )
                )
            if valid_params_count >= 3:
                result_validation_alert.alerts_ids.append(alert.id)
        # Eliminar ids duplicados
        result_validation_alert.alerts_ids = list(
            set(result_validation_alert.alerts_ids))
        return result_validation_alert
