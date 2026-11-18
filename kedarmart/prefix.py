"""Keep the optional standalone store mount separate from the host website."""
import re

from django.conf import settings


class StorePrefixMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        prefix = settings.FORCE_SCRIPT_NAME or ''
        if not prefix:
            return response
        location = response.get('Location', '')
        if location.startswith('/') and not location.startswith('//') and not (
                location == prefix or location.startswith(prefix + '/')):
            response['Location'] = prefix + location
        if not response.streaming and response.get('Content-Type', '').startswith('text/html'):
            def mount(match):
                path = match.group(2)
                if path == prefix or path.startswith(prefix + '/'):
                    return match.group(0)
                return match.group(1) + prefix + path
            body = response.content.decode(response.charset)
            body = re.sub(r'''(\b(?:href|src|action)=["'])(/(?!/)[^"']*)''', mount, body)
            response.content = body.encode(response.charset)
            if response.has_header('Content-Length'):
                response['Content-Length'] = len(response.content)
        return response
