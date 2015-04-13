"""
Unit tests for the digests.py file
"""

from django.test import TestCase

from edx_notifications.namespaces import (
    NotificationNamespaceResolver,
    DefaultNotificationNamespaceResolver,
    register_namespace_resolver
)
from edx_notifications.data import (
    NotificationMessage,
    NotificationType,
)
from edx_notifications.scopes import (
    NotificationUserScopeResolver
)

from edx_notifications.digests import (
    send_unread_notifications_digest,
    create_default_notification_preferences
)
from edx_notifications.stores.store import notification_store
from edx_notifications.lib.publisher import (
    publish_notification_to_user,
)
from edx_notifications.lib.consumer import (
    set_user_notification_preference,
)
from edx_notifications import const


class TestUserResolver(NotificationUserScopeResolver):
    """
    UserResolver for test purposes
    """
    def resolve(self, scope_name, scope_context, instance_context):
        """
        Implementation of interface method
        """
        return [
            {
                'id': 1001,
                'email': 'dummy@dummy.com',
                'first_name': 'Joe',
                'last_name': 'Smith'
            }
        ]


class TestNamespaceResolver(NotificationNamespaceResolver):
    """
    Namespace resolver for demo purposes
    """
    def resolve(self, namespace, instance_context):
        """
        Implementation of interface method
        """
        return {
            'namespace': namespace,
            'display_name': 'A Test Namespace',
            'features': {
                'digests': True,
            },
            'default_user_resolver': TestUserResolver()
        }


class TestNamespaceResolverNoUsers(NotificationNamespaceResolver):
    """
    Namespace resolver for demo purposes
    """
    def resolve(self, namespace, instance_context):
        """
        Implementation of interface method
        """
        return {
            'namespace': namespace,
            'display_name': 'A Test Namespace',
            'features': {
                'digests': True,
            },
            'default_user_resolver': None
        }


class DigestTestCases(TestCase):
    """
    Test cases for digests.py
    """

    def setUp(self):
        """
        Initialize tests, by creating users and populating some
        unread notifications
        """
        create_default_notification_preferences()
        self.store = notification_store()
        self.test_user_id = 1001

        self.msg_type = self.store.save_notification_type(
            NotificationType(
                name='foo.bar',
                renderer='foo',
            )
        )

        # create two notifications
        msg = self.store.save_notification_message(
            NotificationMessage(
                msg_type=self.msg_type,
                namespace='foo',
                payload={'foo': 'bar'},
            )
        )
        publish_notification_to_user(self.test_user_id, msg)

        msg = self.store.save_notification_message(
            NotificationMessage(
                msg_type=self.msg_type,
                namespace='bar',
                payload={'foo': 'bar'},
            )
        )
        publish_notification_to_user(self.test_user_id, msg)

    def test_no_namespace_resolver(self):
        """
        Assert no digests were sent if we don't have
        a namespace resolver
        """

        register_namespace_resolver(None)

        self.assertEqual(send_unread_notifications_digest(), 0)

    def test_default_namespace_resolver(self):
        """
        Assert no digests were sent if we just use the DefaultNotificationNamespaceResolver
        """

        register_namespace_resolver(DefaultNotificationNamespaceResolver())

        self.assertEqual(send_unread_notifications_digest(), 0)

    def test_no_user_resolver(self):
        """
        Asserts no digests were sent if we don't have a user resolver as part of the namespace
        """

        register_namespace_resolver(TestNamespaceResolverNoUsers())

        self.assertEqual(send_unread_notifications_digest(), 0)

    def test_user_preference_undefined(self):
        """
        Make sure we don't send a digest if the digest preference name is not found
        """
        register_namespace_resolver(TestNamespaceResolver())

        self.assertEqual(send_unread_notifications_digest(), 0)

    def test_user_preference_false(self):
        """
        Make sure we don't send a digest to a user that does not want digests
        """
        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME, 'false')

        self.assertEqual(send_unread_notifications_digest(), 0)

    def test_happy_path(self):
        """
        If all is good and enabled, in this test case, we should get two digests sent, one for each namespace
        """

        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME, 'true')

        self.assertEqual(send_unread_notifications_digest(), 2)

    def test_weekly_preference_false(self):
        """
        If all is good and enabled, in this test case, we should get two digests sent, one for each namespace
        """

        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_WEEKLY_DIGEST_PREFERENCE_NAME, 'false')

        self.assertEqual(send_unread_notifications_digest(is_daily_digest=False), 0)

    def test_happy_path_weekly(self):
        """
        If all is good and enabled, in this test case, we should get two digests sent, one for each namespace
        """

        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_WEEKLY_DIGEST_PREFERENCE_NAME, 'true')

        self.assertEqual(send_unread_notifications_digest(is_daily_digest=False), 2)
