from endstone import Logger
from endstone.event import EventPriority
from typing import Type, Callable, Any, get_type_hints
import inspect
from abc import ABC

# https://github.com/niko-at-chalupa/endstone-clans-api/blob/17af142a5c780fe418cec91431924fb873ac7525/src/endstone_clans_api/events.py

class StreamlabsEvent(ABC):
    @property
    def event_name(self) -> str:
        return self.__class__.__name__

def streamlabs_event_handler(func=None, *, priority: EventPriority = EventPriority.NORMAL):
    """
    Decorator to register an event handler.

    The first argument of the decorated method must be a subclass of SteamlabsEvent.

    # Example
    ```python
    @streamlabs_event_handle
    def on_some_event(event: SomeStreamlabsEvent):
        ...
    ```
    """
    def decorator(f):
        setattr(f, "_is_streamlabs_event_handler", True)
        setattr(f, "_streamlabs_priority", priority)
        return f

    if func:
        return decorator(func)

    return decorator

class StreamlabsEventHandler:
    def __init__(self, logger: Logger):
        self._logger = logger
        self._handlers: dict[Type[StreamlabsEvent], list[Callable[[Any], Any]]] = {}

    def register_events(self, listener: Any):
        for attr_name in dir(listener):
            attr = getattr(listener, attr_name)
            if not callable(attr) or not getattr(attr, "_is_clan_event_handler", False):
                continue

            hints = get_type_hints(attr)
            hints.pop("return", None)

            event_type = next(iter(hints.values()), None)

            if not inspect.isclass(event_type) or not issubclass(event_type, StreamlabsEvent):
                self._logger.error(f"Failed to register clan event handler {attr_name}: No StreamlabsEvent type hint found.")
                continue

            self._handlers[event_type].append(attr)
            self._handlers[event_type].sort(key=lambda x: getattr(x, "_clan_priority").value)

    def call_event(self, event: StreamlabsEvent) -> None:
        for registered_type, handlers in self._handlers.items():
            if isinstance(event, registered_type):
                handler: Callable[[Any], Any]
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        handler_name = getattr(handler, "__name__", str(handler))
                        self._logger.error(f"Error while calling clan event handler {handler_name}: {e}")
                        import traceback
                        self._logger.error(traceback.format_exc())