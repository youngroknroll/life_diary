from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.tags.domain_services import TagPolicyService


class TagPolicyServiceTests(SimpleTestCase):
    def test_can_manage_default_tag_only_for_superuser(self):
        service = TagPolicyService()
        admin = SimpleNamespace(is_superuser=True)
        user = SimpleNamespace(is_superuser=False)
        default_tag = SimpleNamespace(is_default=True, user=None)

        self.assertTrue(service.can_manage(admin, default_tag))
        self.assertFalse(service.can_manage(user, default_tag))

    def test_can_manage_user_owned_tag(self):
        service = TagPolicyService()
        owner = SimpleNamespace(is_superuser=False, username="owner")
        other = SimpleNamespace(is_superuser=False, username="other")
        tag = SimpleNamespace(is_default=False, user=owner)

        self.assertTrue(service.can_manage(owner, tag))
        self.assertFalse(service.can_manage(other, tag))
