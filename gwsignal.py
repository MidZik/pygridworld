from inspect import ismethod
import weakref


class Signal:
    """
    A signal is an observable object. Callables can be connected to the signal,
    which will then be called whenever the signal is emitted.
    The order that connected callbacks are called is undefined. It is only guaranteed that each connected
    callback will be called exactly once for each time the signal is emitted.
    """
    __slots__ = ('_callbacks',)

    def __init__(self):
        self._callbacks = []

    def connect(self, callback, *binds):
        """
        Connects a callback to the signal. Whenever the signal is emitted, the callback will be called.
        :param callback: callable to connect to the signal
        :param binds: additional parameters that should be passed to the callback whenever the signal is emitted
        """
        if ismethod(callback):
            # Bound method case
            self._callbacks.append((weakref.ref(callback.__self__), callback.__func__, binds))
        else:
            # Function/callable case
            self._callbacks.append((None, callback, binds))

    def disconnect(self, callback):
        """
        Disconnect a given callback from the signal.
        The callback will no longer be called whenever the signal is emitted.
        :param callback: Callable to disconnect.
        """
        i = self._find_callback(callback)
        self._remove_index(i)

    def emit(self, *args):
        """
        Emits the signal, calling all connected callbacks with the provided args.
        :param args: Args to pass to each callback
        """
        for i in range(len(self._callbacks) - 1, -1, -1):
            ref, callback, binds = self._callbacks[i]
            if ref is not None:
                # Bound method case
                obj = ref()
                if obj is not None:
                    callback(obj, *args, *binds)
                else:
                    # slot object was deleted earlier, remove it.
                    self._remove_index(i)
            else:
                # Function case
                callback(*args, *binds)

    def _find_callback(self, callback):
        if ismethod(callback):
            # Bound method case
            expected_self = callback.__self__
            expected_callback = callback.__func__
        else:
            # Function/callable case
            expected_self = None
            expected_callback = callback

        for i, connection_tuple in enumerate(self._callbacks):
            found_self = connection_tuple[0]
            if found_self is not None:
                # If not none, this is a weakref that needs dereferencing
                found_self = found_self()

            found_callback = connection_tuple[1]

            if found_self is expected_self and found_callback is expected_callback:
                return i

        raise ValueError("Unable to find a connection with the given slot.")

    def _remove_index(self, index):
        """
        Removes an item from the callback list by putting the last item into its position. This makes this an O(1)
        operation, at the expense of making callback calling order undefined.
        :param index: Index to remove from the slots list.
        """
        if index == len(self._callbacks) - 1 or index == -1:
            self._callbacks.pop()
        else:
            self._callbacks[index] = self._callbacks.pop()
