"""
Defines abstract class for the Notification Store data tier
"""

import abc

from importlib import import_module

from django.conf import settings


# Cached instance of a store provider
_STORE_PROVIDER = None


def notification_store():
    """
    Returns the singleton instance of the StoreProvider that has been
    configured for this runtime. The class path should be
    set in NOTIFICATION_STORE_PROVIDER in the settings file
    """
    global _STORE_PROVIDER  # pylint: disable=global-statement

    if not _STORE_PROVIDER:
        if not hasattr(settings, "NOTIFICATION_STORE_PROVIDER"):
            raise Exception("Settings not configured with NOTIFICATION_STORE_PROVIDER!")

        config = settings.NOTIFICATION_STORE_PROVIDER

        if 'class' not in config or 'options' not in config:
            msg = (
                "Misconfigured NOTIFICATION_STORE_PROVIDER settings, "
                "must have both 'class' and 'options' keys."
            )
            raise Exception(msg)

        module_path, _, name = config['class'].rpartition('.')
        class_ = getattr(import_module(module_path), name)

        _STORE_PROVIDER = class_(**config['options'])

    return _STORE_PROVIDER


class BaseNotificationStoreProvider(object):
    """
    The base abstract class for all notifications data providers, such as MySQL/Django-ORM backed.

    IMPORTANT: NotificationStoreProvider is assumed to be a singleton, therefore there must be
    no state stored in the instance of the provider class.
    """

    # don't allow instantiation of this class, it must be subclassed
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_notification_message_by_id(self, msg_id):
        """
        Returns the notitication message (of NotificationMessage type) by primary key

        ARGS:
            - msg_id: the primary key of the NotificationMessage

        RETURNS: type NotificationMessage
        """

    @abc.abstractmethod
    def save_notification_message(self, msg):
        """
        Save (create or update) a notification message (of NotificationMessage type)

        ARGS:
            - msg: an instance of NotificationMessage. If the 'id' field is
                   set by the caller, then it is assumed to be an update
                   operation

        RETURNS: type NotificationMessage
        """

    @abc.abstractmethod
    def get_notification_type(self, name):
        """
        This returns a NotificationType object.
        """

    @abc.abstractmethod
    def save_notification_type(self, msg_type):
        """
        Saves a new notification type, note that we do not support updates
        """

    @abc.abstractmethod
    def get_num_notifications_for_user(self, user_id, read=True, unread=True):
        """
        Returns an integer count of notifications. It is presumed
        that store provider implementations can make this an optimized
        query

        ARGS:
            - user_id: The id of the user
            - read: Whether to return read notifications (default True)
            - unread: Whether to return unread notifications (default True)

        RETURNS: type list   i.e. []
        """

    @abc.abstractmethod
    def get_notifications_for_user(self, user_id, read=True, unread=True):
        """
        Returns a (unsorted) collection (list) of notifications for the user.

        NOTE: We will have to add paging (with sorting/filtering) in the future

        ARGS:
            - user_id: The id of the user
            - read: Whether to return read notifications (default True)
            - unread: Whether to return unread notifications (default True)

        RETURNS: type list   i.e. []
        """