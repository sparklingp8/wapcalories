import time
from django.http import HttpResponseForbidden
class NoRobotsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Common bot signatures
        self.bot_signatures = {
            'bot', 'spider', 'crawler', 'selenium', 'http', 'python',
            'curl', 'wget', 'go-http', 'postman', 'applebot', 'googlebot'
        }
        # Rate limiting dictionary
        self.request_history = {}

    def __call__(self, request):
        # Get IP and user agent
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.headers.get('User-Agent', '').lower()

        # Check if it's a bot
        is_bot = any(sig in user_agent for sig in self.bot_signatures)

        # Basic rate limiting (5 requests per minute per IP)
        current_time = time.time()
        if ip in self.request_history:
            requests = [t for t in self.request_history[ip]
                       if current_time - t < 60]
            if len(requests) >= 15:
                return HttpResponseForbidden("Too many requests")
            self.request_history[ip] = requests + [current_time]
        else:
            self.request_history[ip] = [current_time]

        response = self.get_response(request)

        if is_bot:
            response['X-Robots-Tag'] = 'noindex, nofollow'
            response['X-Frame-Options'] = 'DENY'
            response['X-Content-Type-Options'] = 'nosniff'

        return response