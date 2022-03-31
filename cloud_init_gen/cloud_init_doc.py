#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""
Implementation of CloudInitDoc, a container that can render cloud-init
user-data documents that are single-part or multi-part.
"""

from base64 import b64encode
from typing import Optional, List, Union

from io import BytesIO
import gzip

from .typehints import JsonableDict
from .exceptions import CloudInitGenError
from .renderable import CloudInitRenderable
from .part import (
    CloudInitPart,
    CloudInitPartConvertible,
    MimeHeadersConvertible
  )

GZIP_FIXED_MTIME: float = 0.0
"""A fixed mktime() value that is used for the timestamp when gzipping cloud-init data.
   This makes the rendered data deterministic and stable, which helps keep infrastructure
   automation tools like terraform and Pulumi from needlessly updating cloud instances. """


CloudInitDocConvertible = Optional[
          Union[
              CloudInitRenderable,
              str,
              bytes,
              JsonableDict,
            ]
        ]
"""Type hint for values that can be used as initialization content for a CloudInitDoc"""

class CloudInitDoc(CloudInitRenderable):
  """
  A container for a complete cloud-init user-data document, which may consist of
  zero or more CloudInnitDataPart's, or can be a raw bytes value to
  be passed directly to cloud-init.
  """

  parts: List[CloudInitRenderable]
  """If raw_binary is None, a List of renderable parts to be rendered. An empty list
     indicates an empty/null user-data document. A list with a single item
     results in that item being directly rendered. A list with more than
     one item is rendered as a multipart MIME document.  Ignored if
     raw_binary is not None."""

  raw_binary: Optional[bytes]=None
  """If not None, a raw binary encoding of the entire user-data document,
     which can be passed directly to cloud-init. This field exists only
     so that users can choose to render user-data themselves, and still
     pass the result to an API that expects CloudInitDoc."""

  def __init__(
        self,
        content: CloudInitDocConvertible=None,
        mime_type: Optional[str]=None,
        headers: MimeHeadersConvertible=None
      ):
    """Create a container for a complete cloud-init user-data document,
       which may consist of zero or more CloudInnitDataPart's, or can
       be a raw bytes value to be passed directly to cloud-init.

    Args:
        content (CloudInitDocConvertible, optional):
           If None, an empty document is created--parts can be added before rendering with add().
           If another CloudInitDoc object, creates a clone of that object.
           If a bytes value, then this parameter is directly used for final raw binary
           rendering of the document (This option exists only
           so that users can choose to render user-data themselves, and still
           pass the result to an API that expects CloudInitDoc).
           Otherwise, causes a single part to be immediately added to the document
           as if add() had been called.  Included for convenience in creating single-part
           documents, which is common.  Defaults to None.
        mime_type (Optional[str], optional):
           If content is not None and not bytes, as described for add(). Ignored if content is None. Defaults to None.
        headers (MimeHeadersConvertible, optional):
           If content is not None and not bytes, as described for add(). Ignored if content is None. Defaults to None.

    Raises:
        CloudInitGenError: An error occured building the first part of the document.
    """
    self.parts = []
    if not content is None:
      if isinstance(content, CloudInitDoc):
        self.parts = content.parts[:]
        self.raw_binary = content.raw_binary
      elif isinstance(content, bytes):
        if len(content) > 16383:
          raise CloudInitGenError(f"raw binary user data too big: {len(content)}")
        self.raw_binary = content
      else:
        self.add(content, mime_type=mime_type, headers=headers)

  def add(self,
        content: Union[CloudInitRenderable, CloudInitPartConvertible],
        mime_type: Optional[str]=None,
        headers: MimeHeadersConvertible=None
      ):
    """Add a single renderable part of a potentially multi-part cloud-init document.

    Args:
        content (Optional[Union[CloudInitPart, str, JsonableDict]]): 
                            The content to be rendered for the part. If mime_type is None, this can be:
                               1. None, indicating this is a null part. No action will be taken.
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
                               5. A CloudInitRenderable that has already been initialized. The item is
                                  directly added as a part.
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
        CloudInitGenError: An attempt was made to add a part to a document that was created with raw_binary
        CloudInitGenError: An error occured building the part
    """
    if not content is None:
      if not self.raw_binary is None:
        raise CloudInitGenError(f"Cannot add parts to CloudInitDoc initialized with raw binary payload")
      if not isinstance(content, CloudInitRenderable):
        content = CloudInitPart(content, mime_type=mime_type, headers=headers)
      if not content.is_null_content():
        self.parts.append(content)

  def is_null_content(self) -> bool:
    """Return True if this is a null document

    Returns:
        bool: True if rendering this document will return None
    """
    return self.raw_binary is None and len(self.parts) ==0

  def render(
        self,
        include_mime_version: bool=True,
        force_mime: bool=False,
        include_from: bool=False
      ) -> Optional[str]:
    """Renders the entire cloudinit user-data document to a string suitable for passing
       to cloud-init directly. For single-part documents, renders them directly. For
       multi-part documents, wraps the parts in a multipart MIME encoding.

    Args:
        include_mime_version (bool, optional):
                        True if a MIME-Version header should be included.
                        Ignored if a single-part document and comment-style
                        headers are selected. Note that cloud-init REQUIRES
                        this header for the outermost MIME document, so for
                        compatibility it should be left at True. Defaults to True.
        force_mime (bool, optional): If True, MIME-style headers will be used.
                        By default, a comment-style header will be used if this
                        is a single-part document and there is an appropriate
                        comment header for for the single part's MIME type.
                        Defaults to False.
        include_from (bool, optional): If True, any 'From' header associated with
                        the part will be included; otherwise it will be stripped.
                        Defaults to False. This parameter is included as part of
                        CloudInitRenderable interface, but it has no effect on
                        CloudInitDoc.

    Returns:
        Optional[str]: The entire document rendered as a string suitable for passing to cloud-init
                       directly, or None if this is a null/empty document (with zero parts). If
                       raw_binary was provided at construction time, then that value
                       is simply decoded as UTF-8.
    """
    result: Optional[str]
    if self.raw_binary is None:
      if not len(self.parts) > 0 and not include_mime_version:
        raise CloudInitGenError("include_mime_version MUST be True for the outermost cloud_init_data part")
      if len(self.parts) == 0:
        result = None
      elif len(self.parts) == 1:
        result = self.parts[0].render(include_mime_version=include_mime_version, force_mime=force_mime)
      else:
        # Parts of a multi-part document are forced into MIME mode
        rendered_parts = [ part.render(force_mime=True, include_mime_version=False) for part in self.parts ]

        # Find a unique boundary string that is not in any of the rendered parts
        unique = 0

        while True:
          boundary = f'::{unique}::'
          for rp in rendered_parts:
            assert not rp is None
            if boundary in rp:
              break
          else:
            break
          unique += 1
        
        result = f'Content-Type: multipart/mixed; boundary="{boundary}"\n'
        if include_mime_version:
          result += 'MIME-Version: 1.0\n'
        result += '\n'
        for rp in rendered_parts:
          result += f"--{boundary}\n{rp}\n"
        result += f"--{boundary}--\n"
    else:
      result = self.raw_binary.decode('utf-8')

    return result

  def render_binary(self, include_mime_version: bool=True) -> Optional[bytes]:
    """Renders the entire cloudinit user-data document to a binary bytes buffer suitable for passing
       to cloud-init directly. For single-part documents, renders them directly. For
       multi-part documents, wraps the parts in a multipart MIME encoding.

    Args:
        include_mime_version (bool, optional):
                        True if a MIME-Version header should be included.
                        Ignored if a single-part document and comment-style
                        headers are selected. Note that cloud-init REQUIRES
                        this header for the outermost MIME document, so for
                        compatibility it should be left at True. Defaults to True.
        force_mime (bool, optional): If True, MIME-style headers will be used.
                        By default, a comment-style header will be used if this
                        is a single-part document and there is an appropriate
                        comment header for for the single part's MIME type.
                        Defaults to False.

    Returns:
        Optional[bytes]: The entire document rendered as a UTF-8-encoded bytes suitable for passing to cloud-init
                       directly, or None if this is a null/empty document (with zero parts). If
                       raw_binary was provided at construction time, then that value
                       is directly returned.
    """
    if self.raw_binary is None:
      content = self.render(include_mime_version=include_mime_version)
      bcontent = None if content is None else content.encode('utf-8')
      if not bcontent is None and len(bcontent) >= 16383:
        buff = BytesIO()
        # NOTE: we use a fixed modification time when zipping so that the resulting compressed data is
        # always the same for a given input. This prevents Pulumi from unnecessarily replacing EC2 instances
        # because it looks like the cloud-init user-data changed when it really did not.
        with gzip.GzipFile(None, 'wb', compresslevel=9, fileobj=buff, mtime=GZIP_FIXED_MTIME) as g:
          g.write(bcontent)
        compressed = buff.getvalue()
        if len(compressed) > 16383:
          raise CloudInitGenError(f"EC2 cloud_init_data too big: {len(bcontent)} before compression, {len(compressed)} after")
        bcontent = compressed
    else:
      bcontent = self.raw_binary
    return bcontent

  def render_base64(self, include_mime_version: bool=True) -> Optional[str]:
    """Renders the entire cloudinit user-data document to a base-64 encoded binary block suitable for passing
       to cloud-init directly. For single-part documents, renders them directly. For
       multi-part documents, wraps the parts in a multipart MIME encoding.

    Args:
        include_mime_version (bool, optional):
                        True if a MIME-Version header should be included.
                        Ignored if a single-part document and comment-style
                        headers are selected. Note that cloud-init REQUIRES
                        this header for the outermost MIME document, so for
                        compatibility it should be left at True. Defaults to True.
        force_mime (bool, optional): If True, MIME-style headers will be used.
                        By default, a comment-style header will be used if this
                        is a single-part document and there is an appropriate
                        comment header for for the single part's MIME type.
                        Defaults to False.

    Returns:
        Optional[str]: The entire document rendered as a base-64 encoded binary block suitable
                       for passing to cloud-init directly, or None if this is a null/empty
                       document (with zero parts). If raw_binary was provided at construction
                       time, then that value is simply encoded with base-64.
    """
    bcontent = self.render_binary(include_mime_version=include_mime_version)
    b64 = None if bcontent is None else b64encode(bcontent).decode('utf-8')
    return b64
