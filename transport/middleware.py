from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token_str):
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    User = get_user_model()
    try:
        token = AccessToken(token_str)
        return User.objects.get(id=token['user_id'])
    except (InvalidToken, TokenError, Exception):
        return AnonymousUser()


class JWTAuthMiddlewareStack(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        qs = parse_qs(scope.get('query_string', b'').decode())
        tokens = qs.get('token', [])
        if tokens:
            scope['user'] = await get_user_from_token(tokens[0])
        else:
            scope['user'] = AnonymousUser()
        return await super().__call__(scope, receive, send)
