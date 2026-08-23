from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np


class CameraSource(ABC):

    @abstractmethod
    def open(self) -> bool: ...

    @abstractmethod
    def read(self) -> tuple[bool, object]: ...

    @abstractmethod
    def release(self) -> None: ...

    def mark_disconnected(self) -> None:
        self.release()

    def close(self) -> None:
        self.release()

    @property
    @abstractmethod
    def device_id(self) -> str: ...

    @property
    @abstractmethod
    def label(self) -> str: ...

    @property
    @abstractmethod
    def width(self) -> int: ...

    @property
    @abstractmethod
    def height(self) -> int: ...

    @property
    @abstractmethod
    def fps(self) -> float: ...

    @property
    @abstractmethod
    def is_open(self) -> bool: ...

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} id={self.device_id!r} "
            f"label={self.label!r} open={self.is_open}>"
        )
