from contact.models import RequestLog


class RequestLogRepository:
    def create(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        client_ip: str | None,
        duration_ms: int,
        user_agent: str = '',
    ) -> RequestLog:
        return RequestLog.objects.create(
            method=method,
            path=path,
            status_code=status_code,
            client_ip=client_ip,
            duration_ms=duration_ms,
            user_agent=user_agent[:512],
        )
