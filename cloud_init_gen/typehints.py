#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Supplementary type hints"""

from typing import Dict, List, Any, Union

# Note: recursive type hints are not allowed by mypy so this is simplified a bit
Jsonable = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
"""A Type hint for a simple JSON-serializable value; i.e., str, int, float, bool, None, Dict[str, Jsonable], List[Jsonable]"""

JsonableDict = Dict[str, Jsonable]
"""A type hint for a simple JSON-serializable dict; i.e., Dict[str, Jsonable]"""
