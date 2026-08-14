from django.dispatch import receiver

from apps.dashboard.signals import time_blocks_changed
from .use_cases import invalidate_stats_cache


@receiver(time_blocks_changed, dispatch_uid="stats.invalidate_stats_cache")
def on_time_blocks_changed(sender, user_id, target_date, **kwargs):
    invalidate_stats_cache(user_id, target_date)
