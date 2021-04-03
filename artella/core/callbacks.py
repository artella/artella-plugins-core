#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core callback functionality
"""

from __future__ import print_function, division, absolute_import

import inspect
import logging
import traceback

from artella import dcc
from artella.core.dcc import callback
from artella.core import dcc as dcc_core

# Cache used to store Artella callbacks
ARTELLA_CALLBACKS_CACHE = dict()

logger = logging.getLogger('artella')


def initialize_callbacks():

    global ARTELLA_CALLBACKS_CACHE
    if ARTELLA_CALLBACKS_CACHE:
        return

    shutdown_type = None
    if hasattr(callback.Callbacks(), 'ShutdownCallback'):
        shutdown_type = getattr(callback.Callbacks(), 'ShutdownCallback')

    for callback_name in dcc_core.callbacks():
        callback_type = getattr(dcc_core.DccCallbacks, callback_name)[1]['type']
        if callback_type == 'simple':
            callback_type = SimpleCallbackWrapper
        elif callback_type == 'filter':
            callback_type = FilterCallbackWrapper
        else:
            callback_type = SimpleCallbackWrapper

        callback_class = getattr(callback.Callbacks(), '{}Callback'.format(callback_name), None)
        if not callback_class:
            logger.warning(
                'Dcc {} does not provides a Callback implementation for {}Callback. Skipping ...'.format(
                    dcc.name(), callback_name))
            continue

        # This should not be necessary. We added just to be sure that no callbacks are registered in scenes
        # because that could break user DCC session.
        new_callback = ARTELLA_CALLBACKS_CACHE.get(callback_name, None)
        if new_callback:
            new_callback.cleanup()

        ARTELLA_CALLBACKS_CACHE[callback_name] = callback_type(callback_class, shutdown_type)

        logger.debug('Creating Callback: {} | {}'.format(callback_name, callback_class))


def register(callback_type, fn):
    """
    Register a new callback if given callback_type exists in current DCC
    :param str callback_type: type of callback
    :param fn: Python function that will be called when callback is emitted
    """

    global ARTELLA_CALLBACKS_CACHE
    if not ARTELLA_CALLBACKS_CACHE:
        return

    if isinstance(callback_type, (list, tuple)):
        callback_type = callback_type[0]

    if inspect.isclass(callback_type):
        callback_type = callback_type.__name__

    if callback_type.endswith('Callback'):
        callback_type = callback_type.replace('Callback', '')

    if callback_type in list(ARTELLA_CALLBACKS_CACHE.keys()):
        ARTELLA_CALLBACKS_CACHE[callback_type].register(fn)


def unregister(callback_type, fn):
    """
    Unregisters given function from given callback type
    :param str callback_type: type of callback
    :param fn: Python function we want to unregister from callback
    """

    if isinstance(callback_type, (list, tuple)):
        callback_type = callback_type[0]

    if callback_type in list(ARTELLA_CALLBACKS_CACHE.keys()):
        ARTELLA_CALLBACKS_CACHE[callback_type].unregister(fn)


def uninitialize_callbacks():

    global ARTELLA_CALLBACKS_CACHE
    if not ARTELLA_CALLBACKS_CACHE:
        return

    for callback_name, callback_obj in ARTELLA_CALLBACKS_CACHE.items():
        callback_obj.cleanup()

    ARTELLA_CALLBACKS_CACHE.clear()


class CallbackWrapper(object):
    """
    Class that wraps DCC callbacks
    """

    def __init__(self, notifier, shutdown_notifier):
        super(CallbackWrapper, self).__init__()

        self._notifier = notifier
        self._enabled_stack = list()
        self._registry = list()
        self._shutdown_notifier = None
        self._shutdown_token = None
        if shutdown_notifier and notifier != shutdown_notifier:
            self._shutdown_notifier = shutdown_notifier
            self._shutdown_token = self._shutdown_notifier.register(self._shutdown)

    def __del__(self):
        if self._notifier:
            self._shutdown([])

    @property
    def valid(self):
        """
        Property to query the validity of this callback

        :return: True if the callback has a notifier; False otherwise
        """

        return bool(self._notifier)

    @property
    def empty(self):
        """
        Property to query the existence of listeners registered to this callback

        :return: True if the callback has listener registered; False otherwise
        """

        return True

    @property
    def connected(self):
        """
        Property to query the 'connected' state of the callback.

        :return: True if the callback has connected itself with the INotifier implementation.
        """

        return False

    @property
    def enabled(self):
        """
        Property to query the 'not empty' and 'connected' state of the callback.

        :return: True if the callback has listeners and is connected the to the INotifier implementation.
        """

        return False

    @property
    def registry(self):
        """
        Property to query all registered functions of a callback

        :return: list<fn>
        """

        return None

    @enabled.setter
    def enabled(self, value):
        """
        Property to set the 'enable' state of the callback.  Modifying the enable state either toggles
        the 'connected' state of the callback but maintains the list of listeners.

        :param bool value: value The enable state of the callback.
        """
        pass

    def resume(self):
        """
        Function that resume the notification connection

        :return: True if the callback connection has been resumed properly; False otherwise
        """

        return self._pop()

    def suspend(self):
        """
        Suspends callback connection
        """

        self._push(False)

    def register(self, fn):
        """
        Adds a listener to this instance.

        :param fn: A valid python function with a variable number of arguments (i.e. *args).
        """

        pass

    def unregister(self, fn):
        """
        Removes a listener from this instance.

        :param fn: A valid python function with a variable number of arguments (i.e. *args).
        """

        pass

    def cleanup(self):
        """
        Function to terminate the callback
        """

        return self._shutdown()

    def _connect(self, fn):
        """
        Internal callback registration function

        :param fn: Python function to register as a listener in the sender
        """

        return self._notifier.register(fn)

    def _disconnect(self, token):
        """
        Internal callback unregister function

        :param token: valid token returned from a previous _connect call
        :return: None if registration was not done or the unchanged value from token otherwise
        """

        if token:
            return self._notifier.unregister(token)

        return None

    def _filter(self, *args):
        """
        Internal function to evaluate if the callback from the notifier is valid.
        Tests the validity of the message with the custom function.

        :param args:  Variable list of arguments received from the notifier
        :return: A tuple of indeterminant length and type if callbacks should be passed to listener; (False, None)
            otherwise.
        """

        return self._notifier.filter(*args)

    def _push(self, state):
        """
        Internal function to set the enable state while maintaining a history of previous enabled states

        :param bool state: the enable state of the callback
        """

        if self.valid:
            self._enabled_stack.append(self.enabled)
            self.enabled = state

    def _pop(self):
        """
        Internal function to restore the enable state to a previous enabled state

        :return: True if the callback is enabled as a result of the registration or False otherwise
        """

        if self.valid and self._enabled_stack:
            self.enabled = self._enabled_stack.pop()

        return self.enabled

    def _shutdown(self, *args):
        """
        Internal force that forces the unregistering and disconnection from sender.

        :param args:
        :return:
        """

        if self._shutdown_token and self._shutdown_notifier:
            self._shutdown_notifier.unregister(self._shutdown_token)
        self._shutdown_notifier = None
        self._notifier = None


class SimpleCallbackWrapper(CallbackWrapper, object):
    """
    Simple implementation for Callback wrapper
    It maintains a one-to-one relation between listener and notifiers without any event filtering
    """

    class RegistryEntry(object):
        def __init__(self, callback, token):
            self.callback = callback
            self.token = token

    def __init__(self, notifier, shutdown_notifier):
        super(SimpleCallbackWrapper, self).__init__(notifier=notifier, shutdown_notifier=shutdown_notifier)

    @property
    def empty(self):
        """
        Property to query the existence of listeners to this callback.

        :return: True if the callback has listeners registered; False otherwise.
        """

        return not bool(self._registry)

    @property
    def connected(self):
        """
        Property to query the 'connected' state of the callback.

        :return: True if the callback has connected itself with the INotifier implementation.
        """

        return all(e.token for e in self._registry)

    @property
    def enabled(self):
        """
        Property to query the 'not empty' and 'connected' state of the callback.

        :return: True if the callback has listeners and is connected the to the INotifier implementation.
        """

        return not self.empty and bool(self.connected)

    @enabled.setter
    def enabled(self, value):
        """!
        Property to set the 'enable' state of the callback.  Modifying the enable state either toggles
        the 'connected' state of the callback but maintains the list of listeners.

        :param bool value: The enable state of the callback.
        """

        for entry in self._registry:
            if not value and entry.token:
                entry.token = self._disconnect(entry.token)
            elif value and not entry.token:
                entry.token = self._connect(entry.callback)

    def register(self, fn):
        """
        Adds a listener to this instance

        :param fn fn: a valid Python function with a variable number of arguments (exp. *args)
        """

        entry = next((e for e in self._registry if e.callback == fn), None)
        logger.debug(
            'Started: ({}) {} Register - fn:"{}", entry:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(fn), str(entry)))
        if not entry:
            token = self._connect(fn) if self.connected else None
            logger.debug(
                '({}) {} Register - token:"{}"'.format(str(self._notifier), self.__class__.__name__, str(token)))
            self._registry.append(SimpleCallbackWrapper.RegistryEntry(fn, token))
        logger.debug('Completed: ({}) {} Register'.format(str(self._notifier), self.__class__.__name__))

    def unregister(self, fn):
        """
        Removes a listener from this instance

        :param fn: a valid Python function with a variable number of arguments (exp. *args)
        """

        entry = next((e for e in self._registry if e.callback == fn), None)
        logger.debug(
            'Started: ({}) {} Unregister - fn:"{}", entry:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(fn), str(entry)))
        if entry:
            self._disconnect(entry.token)
            self._registry.remove(entry)
        logger.debug('Completed: ({}) {} Unregister'.format(str(self._notifier), self.__class__.__name__))

    def _shutdown(self, *args):
        """
        Forces an unregistering from the notifier
        """

        logger.debug('Started: ({}) {} Shutdown'.format(str(self._notifier), self.__class__.__name__))
        for entry in self._registry:
            logger.debug(
                '{}._shutdown - Disconnecting ({}) {}'.format(str(self._notifier), self.__class__.__name__, str(entry)))
            self._disconnect(entry.token)
        del self._registry[:]

        super(SimpleCallbackWrapper, self)._shutdown(*args)
        logger.debug('Complete: ({}) {} Shutdown'.format(str(self._notifier), self.__class__.__name__))


class FilterCallbackWrapper(CallbackWrapper, object):
    """
    Filter implementation for Callback wrapper, It allows to filtering the callback generated from the notifier.
    It maintains a many-to-one relation between listeners and notifiers.
    """

    class RegistryEntry(object):
        def __init__(self, callback):
            self.callback = callback

    def __init__(self, notifier, shutdown_notifier):
        super(FilterCallbackWrapper, self).__init__(notifier=notifier, shutdown_notifier=shutdown_notifier)

        self._token = None

    @property
    def empty(self):
        """
        Property to query the existence of listeners to this callback.

        :return: True if the callback has listeners registered; False otherwise.
        """

        return not bool(self._registry)

    @property
    def connected(self):
        """
        Property to query the 'connected' state of the callback.

        :return: True if the callback has connected itself with the INotifier implementation.
        """

        return bool(self._token)

    @property
    def enabled(self):
        """
        Property to query the 'not empty' and 'connected' state of the callback.

        :return: True if the callback has listeners and is connected the to the INotifier implementation.
        """

        return not self.empty and bool(self.connected)

    @enabled.setter
    def enabled(self, value):
        """
        Property to set the 'enable' state of the callback.  Modifying the enable state either toggles
        the 'connected' state of the callback but maintains the list of listeners.

        :param value: The enable state of the callback.
        """

        if not value and self._token:
            self._token = self._disconnect(self._token)
        elif value and not self._token:
            self._token = self._connect(self._notify)

    def _shutdown(self, *args):
        """
        Forces an unregistering from the notifier
        """

        logger.debug('Started: ({}) {} Shutdown'.format(str(self._notifier), self.__class__.__name__))
        if self._token:
            self._token = self._disconnect(self._token)
            self._token = None
        del self._registry[:]

        super(self.__class__, self)._shutdown(*args)
        logger.debug('Complete: ({}) {} Shutdown'.format(str(self._notifier), self.__class__.__name__))

    def _notify(self, *args):
        """
        Internal function registered with the notifier. Evaluates the condition with _filter during the callback.
        If its valid, it will broadcast the callback to the listener via _execute().
        All notifier data is passed on to the user via _execute().

        :param args: A variable list of arguments received from the notifier
        :return:
        """

        fn_args = self._filter(*args)
        if fn_args[0]:
            self._execute(*fn_args[1:])

    def _execute(self, *args):
        """
        Internal function to notify all listeners registered to the current instance of the class

        :param args: A variable list of arguments received from the notifier
        """

        for entry in self._registry:
            try:
                entry.callback(*args)
            except Exception as exc:
                logger.error('{} | {}'.format(exc, traceback.format_exc()))

    def register(self, fn):
        """
        Adds a listener to this instance

        :param fn: a valid Python function with a variable number of arguments (exp. *args)
        """

        logger.debug(
            'Started: ({}) {} Register - fn:"{}", IsEmpty:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(fn), bool(self.empty)))
        if self.empty:
            self._token = self._connect(self._notify)
            logger.debug(
                '({}) {} Register - token:"{}"'.format(str(self._notifier), self.__class__.__name__, str(self._token)))
        self._registry.append(FilterCallbackWrapper.RegistryEntry(fn))
        logger.debug('Completed: ({}) {} Register'.format(str(self._notifier), self.__class__.__name__))

    def unregister(self, fn):
        """
        Removes a listener from this instance

        :param fn: a valid Python function with a variable number of arguments (exp. *args)
        """

        entry = next((e for e in self._registry if e.callback == fn), None)
        logger.debug(
            'Started: ({}) {} Unregister - fn:"{}", IsEmpty:"{}"'.format(
                str(self._notifier), self.__class__.__name__, str(fn), bool(self.empty)))

        if entry:
            self._registry.remove(entry)

        if self.empty and self.connected:
            logger.debug(
                '({}) {} Unregister token:"{}"'.format(str(self._notifier), self.__class__.__name__, str(self._token)))
            self._token = self._disconnect(self._token)
        logger.debug('Completed: ({}) {} Unregister'.format(str(self._notifier), self.__class__.__name__))
