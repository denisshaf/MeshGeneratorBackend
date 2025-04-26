from types import TracebackType
from typing import NamedTuple, ClassVar, Self
from collections import deque
import logging


debug_logger = logging.getLogger('debug')


class OutputIndexes(NamedTuple):
    obj_start: int
    obj_end: int
    exclude_start: int
    exclude_end: int


class OBJParser:
    _obj_indexes: list[OutputIndexes]
    _obj_start: int | None = None
    _obj_end: int | None = None
    _exclude_start: int | None = None
    _exclude_end: int | None = None
    _counter: int = 0
    _backtrack_queue: deque

    def __init__(self) -> None:
        self._obj_indexes = []
        self._backtrack_queue = deque(maxlen=2)

    def process_token(self, token: str) -> None:
        self._backtrack_queue.append(token)

        # Handle code block markers
        if token == "```":

            # Check for OBJ block start
            if (
                len(self._backtrack_queue) >= 2
                and self._backtrack_queue[-2] == "obj"
                and not self._obj_start
            ):
                self._exclude_start = self._counter - 1  # Including the 'obj' token
                self._obj_start = self._counter + 1  # Start after this token

            # Check for OBJ block end
            elif self._obj_start and not self._obj_end:
                self._obj_end = self._counter - 1  # End at the token before "```"
                self._exclude_end = self._counter + 1  # Including this token

                # Store the complete index set
                self._finalize_indices()

        # Check for direct OBJ content (without markdown markers)
        elif not self._obj_start and self._is_obj_start_line(token):
            self._obj_start = self._counter
            self._exclude_start = self._counter

        # Check for end of direct OBJ content
        elif self._obj_start and not self._obj_end and not self._is_obj_content(token):
            self._obj_end = self._counter
            self._exclude_end = self._counter
            self._finalize_indices()

        self._counter += 1

    def _finalize_indices(self) -> None:
        """Store the current set of indices and reset for next potential OBJ block."""
        if (
            self._obj_start is not None
            and self._obj_end is not None
            and self._exclude_start is not None
            and self._exclude_end is not None
        ):
            indexes = OutputIndexes(
                obj_start=self._obj_start,
                obj_end=self._obj_end,
                exclude_start=self._exclude_start,
                exclude_end=self._exclude_end,
            )
            self._obj_indexes.append(indexes)
            self._reset_indexes()

    def _is_obj_start_line(self, token: str) -> bool:
        """Check if token starts with valid OBJ commands."""
        if not token.strip():
            return False

        valid_starters = [
            "v ",
            "vt ",
            "vn ",
            "f ",
            "g ",
            "o ",
            "mtllib ",
            "s ",
            "usemtl ",
        ]
        return any(token.lstrip().startswith(starter) for starter in valid_starters)

    def _is_obj_content(self, token: str) -> bool:
        """Check if token is valid OBJ content."""
        if not token.strip():
            return True  # Empty lines are allowed in OBJ files

        valid_elements = [
            "v ",
            "vt ",
            "vn ",
            "f ",
            "g ",
            "o ",
            "mtllib ",
            "s ",
            "usemtl ",
            "# ",
        ]
        return any(token.lstrip().startswith(elem) for elem in valid_elements)

    def get_obj_indexes(self) -> list[OutputIndexes]:
        if self._obj_start is not None and self._obj_end is None:
            self._obj_end = self._counter
            self._exclude_end = self._counter
            self._finalize_indices()
        return self._obj_indexes

    def _reset_indexes(self) -> None:
        self._obj_start = None
        self._obj_end = None
        self._exclude_start = None
        self._exclude_end = None

    def clear(self) -> None:
        self._obj_indexes.clear()

        self._reset_indexes()
        self._counter = 0

    def __enter__(self) -> Self:
        return self
    
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.clear()
