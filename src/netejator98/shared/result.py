"""Result type for robust domain error handling without unchecked exceptions."""

from __future__ import annotations

from typing import Callable, Generic, NoReturn, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")


class Ok(Generic[T]):
    """Represents a successful outcome holding a value."""

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        self._value = value

    @property
    def value(self) -> T:
        return self._value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self._value

    def unwrap_or(self, default: T) -> T:
        return self._value

    def unwrap_err(self) -> NoReturn:
        raise ValueError(f"Called unwrap_err on Ok({self._value!r})")

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        return Ok(fn(self._value))

    def map_err(self, fn: Callable[[E], F]) -> Result[T, F]:
        return Ok(self._value)

    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return fn(self._value)

    def __repr__(self) -> str:
        return f"Ok({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Ok):
            return bool(self._value == other._value)
        return False

    def __hash__(self) -> int:
        return hash((True, self._value))


class Err(Generic[E]):
    """Represents a failed outcome holding an error."""

    __slots__ = ("_error",)

    def __init__(self, error: E) -> None:
        self._error = error

    @property
    def error(self) -> E:
        return self._error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> NoReturn:
        raise ValueError(f"Called unwrap on Err({self._error!r})")

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_err(self) -> E:
        return self._error

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        return Err(self._error)

    def map_err(self, fn: Callable[[E], F]) -> Result[T, F]:
        return Err(fn(self._error))

    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return Err(self._error)

    def __repr__(self) -> str:
        return f"Err({self._error!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Err):
            return bool(self._error == other._error)
        return False

    def __hash__(self) -> int:
        return hash((False, self._error))


Result = Union[Ok[T], Err[E]]

