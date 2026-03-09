import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_push_notification(user, title, body, url='/'):
    """
    Send a web push notification to all of a user's subscribed devices.
    Silently skips if VAPID keys are not configured.
    Automatically removes expired/invalid subscriptions.
    """
    if not getattr(settings, 'VAPID_PRIVATE_KEY', ''):
        return

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.warning("pywebpush not installed — push notifications unavailable")
        return

    from accounts.models import PushSubscription

    payload = json.dumps({
        'title': title,
        'body': body,
        'url': url,
        'icon': '/static/icons/icon-192.png',
    })

    for sub in user.push_subscriptions.all():
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    'sub': f'mailto:{settings.VAPID_ADMIN_EMAIL}',
                },
            )
        except Exception as e:
            # 404/410 = subscription expired or user unsubscribed — clean it up
            status = getattr(getattr(e, 'response', None), 'status_code', None)
            if status in (404, 410):
                sub.delete()
            else:
                logger.warning("Push notification failed for user %s: %s", user.pk, e)
