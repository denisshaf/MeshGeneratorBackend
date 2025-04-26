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

        # Check if we're not already inside an OBJ block
        if self._exclude_start is None:
            # Check for "```obj\n" pattern to start an OBJ block
            queue_list = list(self._backtrack_queue)
            if len(queue_list) >= 3 and queue_list[-3:] == ['```', 'obj', '\n']:
                self._exclude_start = self._counter - 2  # Index of "```" (3rd last token)
                self._obj_start = self._counter + 1  # Index of the next token after "\n"
        else:
            # We're inside an OBJ block, check for "```" pattern to end it
            if token == '```':
                self._obj_end = self._counter - 1  # Index of the last token of OBJ content
                self._exclude_end = self._counter  # Index of "```"
                
                # Create an OutputIndexes object and add it to the list
                output_indexes = OutputIndexes(
                    obj_start=self._obj_start,
                    obj_end=self._obj_end,
                    exclude_start=self._exclude_start,
                    exclude_end=self._exclude_end
                )
                self._obj_indexes.append(output_indexes)
                
                # Reset state to detect more OBJ blocks
                self._obj_start = None
                self._obj_end = None
                self._exclude_start = None
                self._exclude_end = None
        
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


tokens = [
    'here', 'is', 'your', 'obj', 'model:', '\n',
    '```', 'obj', '\n',
    '#', ' ', 'Simple', ' ', 'OBJ', ' ', 'file', '\n', 
    '#', ' ', 'Vertices', '\n', 
    'v', ' ', '-', '1.0', ' ', '-', '1.0', ' ', '-', '1.0', '\n', 
    'v', ' ', '1.0', ' ', '-', '1.0', ' ', '-', '1.0', '\n', 
    'v', ' ', '1.0', ' ', '1.0', ' ', '-', '1.0', '\n', 
    'v', ' ', '-', '1.0', ' ', '1.0', ' ', '-', '1.0', '\n', 
    'v', ' ', '-', '1.0', ' ', '-', '1.0', ' ', '1.0', '\n', 
    'v', ' ', '1.0', ' ', '-', '1.0', ' ', '1.0', '\n', 
    'v', ' ', '1.0', ' ', '1.0', ' ', '1.0', '\n', 
    'v', ' ', '-', '1.0', ' ', '1.0', ' ', '1.0', '\n', 
    '\n', 
    '#', ' ', 'Faces', '\n', 
    'f', ' ', '1', ' ', '2', ' ', '3', ' ', '4', '\n', 
    'f', ' ', '5', ' ', '6', ' ', '7', ' ', '8', '\n', 
    'f', ' ', '1', ' ', '5', ' ', '8', ' ', '4', '\n', 
    'f', ' ', '2', ' ', '6', ' ', '7', ' ', '3', '\n', 
    'f', ' ', '1', ' ', '2', ' ', '6', ' ', '5', '\n', 
    'f', ' ', '4', ' ', '3', ' ', '7', ' ', '8', '\n',
    '```' '\n',
    'are', 'you', 'satisfied', '?'
]


parser = OBJParser()

for t in tokens:
    parser.process_token(t)

print(parser.get_obj_indexes())