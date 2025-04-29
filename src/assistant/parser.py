from types import TracebackType
from typing import TypedDict, ClassVar, Self
from collections import deque
import logging


debug_logger = logging.getLogger('debug')


class OutputIndexes(TypedDict):
    obj_start: int
    obj_end: int
    exclude_start: int
    exclude_end: int


class ParsedContent(TypedDict):
    message_content: str
    obj_contents: list[str]


class OBJParser:
    _obj_indexes: list[OutputIndexes]
    _obj_start: int | None = None  # The index of the first token of the OBJ block
    _obj_end: int | None = None  # The index of the first token after the OBJ block
    _exclude_start: int | None = None
    _exclude_end: int | None = None
    _counter: int = 0
    _backtrack_queue: deque[str]

    OBJ_VALID_STARTERS: ClassVar[set[str]] = {
        "v", "vt", "vn", "f", "g", "o", "mtllib", "s", "usemtl", "#"
    }
    BACKTRACK_WINDOW_SIZE: ClassVar[int] = 4

    def __init__(self) -> None:
        self._obj_indexes = []
        self._backtrack_queue = deque(maxlen=OBJParser.BACKTRACK_WINDOW_SIZE)

    def process_token(self, token: str) -> None:
        self._backtrack_queue.append(token)

        # Check for start of direct OBJ content (without markdown markers)
        if not self._obj_start and self._is_obj_start_line(token):
            self._obj_start = self._counter

            # Check for code block start (-2 must be a newline): ['```', 'obj', '\n', token]
            if self._backtrack_queue[-4] == '```' and self._backtrack_queue[-3] == 'obj':
                self._exclude_start = self._counter - 3
            else:
                self._exclude_start = self._counter

        # Check for end of direct OBJ content
        elif (
            self._obj_start
            and not self._obj_end
            and self._backtrack_queue[-2].endswith('\n')  # Previous token is a newline
            and not self._is_obj_content(token)
        ):
            self._obj_end = self._counter

            if token == '```':
                self._exclude_end = self._counter + 2  # +2 to include the closing ``` and the newline
            else:
                self._exclude_end = self._counter

            self._finalize_indexes()

        self._counter += 1

    def _finalize_indexes(self) -> None:
        """Store the current set of indices and reset for next potential OBJ block."""
        if (
            self._obj_start
            and self._obj_end
            and self._exclude_start
            and self._exclude_end
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
        
        return any(token.strip() == starter for starter in OBJParser.OBJ_VALID_STARTERS)

    def _is_obj_content(self, token: str) -> bool:
        """Check if token is valid OBJ content."""
        if not token.strip():
            return True  # Empty lines are allowed in OBJ files
        
        return any(token.strip() == elem for elem in OBJParser.OBJ_VALID_STARTERS)

    def get_obj_indexes(self) -> list[OutputIndexes]:
        if not self._obj_end or not self._exclude_end:
            self._obj_end = self._counter
            self._exclude_end = self._counter
            self._finalize_indexes()
        return self._obj_indexes

    @staticmethod
    def extract_obj_content(tokens: list[str], obj_indexes_list: list[OutputIndexes]) -> ParsedContent:
        obj_contents = []
        message_parts = []
        prev_obj_end_idx = 0
        
        for obj_indexes in obj_indexes_list:
            obj_start = obj_indexes['obj_start']
            obj_end = obj_indexes['obj_end']
            exclude_start = obj_indexes['exclude_start']
            exclude_end = obj_indexes['exclude_end']

            excluded_content = ''.join(tokens[prev_obj_end_idx:exclude_start])
            message_parts.append(excluded_content)

            obj_content = ''.join(tokens[obj_start:obj_end])
            obj_contents.append(obj_content)

            prev_obj_end_idx = exclude_end

        excluded_content = ''.join(tokens[prev_obj_end_idx:])
        message_parts.append(excluded_content)

        result = ParsedContent(
            message_content=''.join(message_parts),
            obj_contents=obj_contents
        )
        return result

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
