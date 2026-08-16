from django.core.management.base import BaseCommand, CommandError

from apps.users.account_deletion import (
    count_overdue_deletion_requests,
    purge_due_deleted_accounts,
)


class Command(BaseCommand):
    help = "Purge accounts whose deletion grace period has expired."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Report overdue uncancelled requests without purging; "
            "exit nonzero when any remain.",
        )

    def handle(self, *args, **options):
        if options["check"]:
            overdue = count_overdue_deletion_requests()
            if overdue:
                raise CommandError(f"Overdue deletion requests: {overdue}")
            self.stdout.write("Overdue deletion requests: 0")
            return
        purged_count = purge_due_deleted_accounts()
        self.stdout.write(f"Purged {purged_count} account(s).")
