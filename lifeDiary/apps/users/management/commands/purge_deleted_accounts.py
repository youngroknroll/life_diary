from django.core.management.base import BaseCommand

from apps.users.account_deletion import purge_due_deleted_accounts


class Command(BaseCommand):
    help = "Purge accounts whose deletion grace period has expired."

    def handle(self, *args, **options):
        purged_count = purge_due_deleted_accounts()
        self.stdout.write(f"Purged {purged_count} account(s).")
