import importlib
import inspect
from typing import Any


class Container:
    def __init__(self):
        self._instances = {}

    def get(self, key: str) -> Any:
        if key in self._instances:
            return self._instances.get(key)
        else:
            return self._instantiate(key)

    def bind(self, key: str, instance: Any) -> None:
        self._instances.update({key: instance})

    def _instantiate(self, key: str) -> Any:
        key_path = key.split('.')
        module = importlib.import_module('.'.join(key_path[:-1]))
        class_reflection = getattr(module, key_path[-1])
        init_signature = inspect.signature(class_reflection.__init__)

        init_arguments = {}
        for name, type in init_signature.parameters.items():
            if name in ['self', 'args', 'kwargs']:
                continue

            type_path = type.annotation.__module__ + '.' + type.annotation.__qualname__
            init_arguments.update({name: self.get(type_path)})

        instance = class_reflection(**init_arguments)
        self.bind(key, instance)

        return instance
