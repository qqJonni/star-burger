from django.http import HttpResponseForbidden
from django.utils.http import url_has_allowed_host_and_scheme

from star_burger import settings


class URLProtectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем URL запроса
        if not url_has_allowed_host_and_scheme(request.build_absolute_uri(), allowed_hosts=settings.ALLOWED_HOSTS):
            return HttpResponseForbidden("Forbidden - Invalid Host or Scheme")

        response = self.get_response(request)
        return response
