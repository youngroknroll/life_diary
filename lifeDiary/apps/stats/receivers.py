from django.dispatch import receiver

from apps.dashboard.signals import time_blocks_changed
from apps.users.signals import goals_changed, notes_changed
from .use_cases import rotate_stats_generation


@receiver(time_blocks_changed, dispatch_uid="stats.rotate_stats_generation")
def on_time_blocks_changed(sender, user_id, **kwargs):
    rotate_stats_generation(user_id)


@receiver(goals_changed, dispatch_uid="stats.rotate_stats_generation_on_goals")
def on_goals_changed(sender, user_id, **kwargs):
    rotate_stats_generation(user_id)


@receiver(notes_changed, dispatch_uid="stats.rotate_stats_generation_on_notes")
def on_notes_changed(sender, user_id, **kwargs):
    rotate_stats_generation(user_id)
