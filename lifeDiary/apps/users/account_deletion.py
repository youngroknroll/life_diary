from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import AccountDeletionRequest, DeletedAccountRecord


GRACE_PERIOD_DAYS = 15


def mask_email(email):
    if not email:
        return ""
    local, separator, domain = email.partition("@")
    if not separator:
        return email
    if len(local) <= 1:
        masked_local = local
    elif len(local) == 2:
        masked_local = f"{local[0]}*"
    else:
        masked_local = f"{local[:2]}{'*' * (len(local) - 2)}"
    return f"{masked_local}@{domain}"


@transaction.atomic
def request_account_deletion(user, now=None):
    now = now or timezone.now()
    existing = AccountDeletionRequest.objects.filter(
        user=user,
        cancelled_at__isnull=True,
        purged_at__isnull=True,
    ).first()
    if existing:
        if user.is_active:
            user.is_active = False
            user.save(update_fields=["is_active"])
        return existing
    deletion_request = AccountDeletionRequest.objects.create(
        user=user,
        requested_at=now,
        scheduled_delete_at=now + timedelta(days=GRACE_PERIOD_DAYS),
    )
    user.is_active = False
    user.save(update_fields=["is_active"])
    return deletion_request


@transaction.atomic
def cancel_account_deletion(user, now=None):
    now = now or timezone.now()
    deletion_request = AccountDeletionRequest.objects.filter(
        user=user,
        cancelled_at__isnull=True,
        purged_at__isnull=True,
    ).first()
    if not deletion_request or deletion_request.scheduled_delete_at <= now:
        return False
    deletion_request.cancelled_at = now
    deletion_request.save(update_fields=["cancelled_at"])
    user.is_active = True
    user.save(update_fields=["is_active"])
    return True


def _create_deleted_account_record(deletion_request, purged_at):
    user = deletion_request.user
    return DeletedAccountRecord.objects.create(
        original_user_id=user.id,
        username=user.get_username(),
        masked_email=mask_email(user.email),
        date_joined=user.date_joined,
        deletion_requested_at=deletion_request.requested_at,
        purged_at=purged_at,
    )


@transaction.atomic
def purge_due_deleted_accounts(now=None):
    now = now or timezone.now()
    due_requests = list(
        AccountDeletionRequest.objects.select_related("user").filter(
            scheduled_delete_at__lte=now,
            cancelled_at__isnull=True,
            purged_at__isnull=True,
        )
    )
    purged_count = 0
    User = get_user_model()
    for deletion_request in due_requests:
        original_user_id = deletion_request.user_id
        _create_deleted_account_record(deletion_request, now)
        deletion_request.purged_at = now
        deletion_request.save(update_fields=["purged_at"])
        User.objects.filter(id=original_user_id).delete()
        purged_count += 1
    return purged_count
