#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""
Abstract base class for objects than can be rendered to a
cloud-init user-data part in text form.
"""
from typing import Optional
from abc import ABC, abstractmethod

class CloudInitRenderable(ABC):
  """Abstract base class for cloud-init renderable items"""

  @abstractmethod
  def is_null_content(self) -> bool:
    """Return True if this is a null document

    Returns:
        bool: True if rendering this document will return None
    """
    ...

  @abstractmethod
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
    ...

