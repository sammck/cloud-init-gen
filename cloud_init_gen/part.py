#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""
Implementation of CloudDataPart, a container for a single
part of a potentially multi-part cloud-init user-data document.
"""
from typing import Optional, Union, Tuple, Dict, OrderedDict, Iterable, cast

from base64 import b64encode
import yaml
import email.parser
from collections import OrderedDict as ordereddict

from .typehints import JsonableDict
from .exceptions import CloudInitGenError

from .part_type import (
    mime_to_cloud_init_part_type,
    comment_to_cloud_init_part_type
  )

from .renderable import CloudInitRenderable

MimeHeadersConvertible = Optional[Union[Dict[str, str], Iterable[Tuple[str, str]], OrderedDict[str, str]]]
"""Type hint for value that can be converted to an OrderedDict of MIME headers"""

CloudInitPartConvertible = Optional[Union[str, JsonableDict, 'CloudInitPart']]
"""Type hint for values that can be used as initialization content for a CloudInitPart"""

def _normalize_headers(headers:  MimeHeadersConvertible) -> OrderedDict[str, str]:
  result: Optional[OrderedDict[str, str]]
  if headers is None:
    result = ordereddict()
  else:
    result = ordereddict(headers)
  return result

class CloudInitPart(CloudInitRenderable):
  """A container for a single part of a potentially multi-part cloud-init document"""

  content: Optional[str]
  """The string representation of the part's content, which is interpreted differently depending
     on its type, or None if this is a "null" part, which will be stripped from the
     final document rendering. This string does NOT include any MIME headers associated
     with the document, and except in the case of shebang comment headers (e.g.,
     "#!/bin/bash"), does NOT include the comment header. For YAML parts, this is the
     rendered YAML text. """

  mime_type: str
  """The full MIME type of the part; e.g., "text/cloud-config". """

  mime_version: Optional[str] = None
  """The MIME version, as pulled from the MIME-Version header. If None, "1.0" is assumed."""

  comment_line: Optional[str] = None
  """The full comment line associated with the part. For shebang-style parts this is
     the entire shebang line; e.g., "#!/bin/bash". If None, there is not comment header
     associated with the part's MIME type. If comment_line_included is true, then this line is also
     present in content; otherwise it has been stripped from content."""

  comment_type: Optional[str] = None
  """The portion of comment_line that identifies the part type. For shebang types, this
     is "#!". For all other types this is the same as comment_line. If None, there is
     no comment header associated with the part's MIME type."""

  comment_line_included: bool = False
  """If True, the part is a shebang-style part, and the full shebang line is included
     as the first line in content; otherwise any identifying comment line has been stripped."""

  headers: OrderedDict[str, str]
  """An ordered dictionary of MIME headers associated with the part. MIME-Version and
     Content-Type are explicitly removed from this mapping during construction."""

  def __init__(
        self,
        content: CloudInitPartConvertible,
        mime_type: Optional[str]=None,
        headers: MimeHeadersConvertible=None
      ):
    """Create a container for a single part of a potentially multi-part cloud-init document

    Args:
        content (CloudInitPartConvertible):
                            The content to be rendered for the part. If mime_type is None, this can be:
                               1. None, indicating this is a null part that will be stripped from the final
                                  document.
                               2. A string beginning with "#". The first line is interpreted as
                                  a cloud-init comment header that identifies the type. The remainder
                                  becomes the content of the part (for shebang-style parts the comment
                                  line is also left in the part's content).
                               3. A string beginning with "Content-Type:" or "MIME-Version:". The string
                                  is parsed as a MIME document with embedded headers. The headers in the
                                  document are merged with and override any headers passed to this constructor.
                                  The MIME type of the part is obtained from the "Content-Type" header, and
                                  the payload becomes the part's content.
                               4. A JsonableDict. The content is converted to YAML and the MIME type is
                                  set to "text/cloud-config". This is a common type of input to cloud-init.
                               5. Another CloudInitPart. In this case, a simple clone is created.
                            If mime_type is not None, then content may be:
                               1. A string. The string will be used as the content of the part without further
                                  interpretation.
                               2. A JsonableDict. The dict is converted to YAML, and the YAML string is used
                                  as the part's content.

        mime_type (Optional[str], optional):
                            The full MIME type of the part, or None to infer the MIME type from the
                            content argument, as described above. Defaults to None.

        headers (MimeHeadersConvertible, optional):
                            An optional ordered dict of MIME headers to associate with the part. Content-Type
                            and MIME-Version are explicitly removed from this dict and handled specially. Any
                            additional headers will be included in the rendering of this part if MIME
                            rendering is selected. If comment-header rendering is selected, the headers are
                            discarded. Defaults to None.

    Raises:
        CloudInitGenError: An error occured building the part
    """
    if content is None:
      self.content = None
      self.mime_type = ''
      self.headers = ordereddict()
    elif isinstance(content, CloudInitPart):
      self.content = content.content
      self.mime_type = content.mime_type
      self.headers = ordereddict(content.headers)
    else:
      original_content = content
      is_yaml = isinstance(original_content, dict)
      if is_yaml:
        content = yaml.dump(
            original_content,
            sort_keys=True,
            indent=1,
            default_flow_style=None,
            width=10000,
          )
      str_content = cast(str, content)   # Make mypy happy
      mime_version: Optional[str] = None
      comment_line: Optional[str] = None
      comment_type: Optional[str] = None
      comment_line_included = False
      merged_headers = _normalize_headers(headers)
      if mime_type is None:
        mime_type = merged_headers.pop('Content-Type', None)
      if mime_type is None and is_yaml:
        mime_type = 'text/cloud-config'   # For YAML docs we assume they are cloud-config unless explicitly other
      if mime_type is None:
        parts = str_content.split('\n', 1)
        if len(parts) < 2:
          raise CloudInitGenError(f"CloudInitPart has no mime type and content has no header line: {parts[0]}")
        if parts[0].startswith('#'):
          comment_line = parts[0]
          comment_type = comment_line
          if comment_type.startswith("#!"):
            comment_type = "#!"
          part_type = comment_to_cloud_init_part_type.get(comment_type, None)
          if part_type is None:
            raise CloudInitGenError(f"Unrecognided CloudInitDoc comment tagline: {parts[0]}")
          mime_type = part_type.mime_type
          if comment_type == "#!":    # shebang comments must be left in the document even if mime is used
            comment_line_included = True
          else:
            str_content = parts[1]
        elif parts[0].startswith('MIME-Version:') or parts[0].startswith('Content-Type:'):
          str_content, embedded_headers = cast(Tuple[str, OrderedDict[str, str]], self.extract_headers(str_content))
          mime_type = embedded_headers.pop('Content-Type')
          if mime_type is None:
            raise CloudInitGenError(f"CloudInitPart has Content-Type header: {embedded_headers}")
          merged_headers.update(embedded_headers)
        else:
          raise CloudInitGenError(f"CloudInitPart has no mime type and first line of content does not identify type: {parts[0]}")
          
      if mime_type in [
            'x-shellscript',
            'x-shellscript-per-boot',
            'x-shellscript-per-instance',
            'x-shellscript-per-once' ]:
        comment_type = "#!"
        if comment_line is None:
          comment_line = str_content.split('\n', 1)[0]
        if not comment_line.startswith('#!'):
          raise CloudInitGenError(f"Content-Type \"{mime_type}\" requires shebang on first line of content: {comment_line}")
        comment_line_included = True
      else:
        part_type = mime_to_cloud_init_part_type.get(mime_type, None)
        if not part_type is None:
          comment_type = part_type.comment_line
          comment_line = comment_type

      mime_version = merged_headers.pop('MIME-Version', None)
      self.content = str_content
      self.mime_type = mime_type
      self.mime_version = mime_version
      self.comment_type = comment_type
      self.comment_line = comment_line
      self.comment_line_included = comment_line_included
      self.headers = merged_headers

  @classmethod
  def extract_headers(
        cls,
        content: Optional[str]
      ) -> Tuple[Optional[str], OrderedDict[str, str]]:
    """Parses MIME headers and payload from a MIME document

    Args:
        content (Optional[str]): MIME document to be parsed, or None for a null document

    Returns:
        Tuple[Optional[str], OrderedDict[str, str]]: A tuple containing:
            [0]: The document payload, or None for a null document
            [1]: an OrderedDict containing the headers. Empty for a null document.
    """
    if content is None:
      headers = ordereddict()
    else:
      parser = email.parser.Parser()
      msg = parser.parsestr(content, headersonly=True)
      content = msg.get_payload()
      headers = ordereddict(msg)
    return content, headers

  def is_null_content(self) -> bool:
    """Return True if this is a null document

    Returns:
        bool: True if rendering this document will return None
    """
    return self.content is None

  def render(
        self,
        include_mime_version: bool=True,
        force_mime: bool=False,
        include_from: bool=False,
      ) -> Optional[str]:
    """Renders the single cloudinit part to a string suitable for passing
       to cloud-init directly or for inclusion in a multipart document.

    Args:
        include_mime_version (bool, optional):
                        True if a MIME-Version header should be included.
                        Ignored if comment-style headers are selected. Note
                        that cloud-init REQUIRES this header for the outermost
                        MIME document. For embedded documents in a multipart
                        MIME it is optional. Defaults to True.
        force_mime (bool, optional): If True, MIME-style headers will be used.
                        By default, a comment-style header will be used if there
                        is an appropriate one for this part's MIME type.
                        Defaults to False.
        include_from (bool, optional): If True, any 'From' header associated with
                        the part will be included; otherwise it will be stripped.
                        Defaults to False.

    Returns:
        Optional[str]: The part rendered as a string suitable for passing to cloud-init
                       directly or for inclusion in a multipart document, or None if
                       this is a null part that should be stripped from final rendering.
    """
    result: Optional[str] = None
    if not self.content is None:
      if not force_mime and not self.comment_line is None:
        result = ("" if self.comment_line_included else self.comment_line + '\n') + self.content
      else:
        result = f"Content-Type: {self.mime_type}\n"
        if include_mime_version:
          mime_version = "1.0" if self.mime_version is None else self.mime_version
          result += f"MIME-Version: {mime_version}\n"
        for k,v in self.headers.items():
          if include_from or k != 'From':
            result += f"{k}: {v}\n"
        result += '\n'
        result += self.content
      #if result != '' and not result.endswith('\n'):
      #  result += '\n'
    return result
