#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""
Simplified function API for rendering cloud-config user-data documents
"""

from typing import Optional
from .part import MimeHeadersConvertible
from .cloud_init_doc import CloudInitDoc, CloudInitDocConvertible

def render_cloud_init_text(
      content: CloudInitDocConvertible
    ) -> Optional[str]:
  """Render cloud-init document as text.

  A convenience function that optionally creates a cloud-init user-data
  document, then renders it as text. If the provided content is a CloudInitDoc,
  then simply renders it. Otherwise a new document is created using the provided
  content; then renders the document.

  This allows code that accepts a CloudInitDocConvertible as input to blindly
  render a cloud-init user-data document without worrying about normalizing it first.

  Args:
      content (CloudInitDocConvertible):
          The content to be rendered. If a CloudInitDoc, then it is directly rendered.
          Operwise a new CloudInitDoc is created using this content, and the new document
          is rendered.

  Returns:
      Optional[str]: The rendered cloud-init user-data document, as text, or None
                     if it is a null/empty document.
  """
  cloud_init_doc = CloudInitDoc(content)
  # Note: include_mime_version is required by cloud-init for the top-level part,
  # so we don't even allow setting it to False.
  result = cloud_init_doc.render(include_mime_version=True)
  return result

def render_cloud_init_binary(
      content: CloudInitDocConvertible
    ) -> Optional[bytes]:
  """Render cloud-init document as binary bytes.

  A convenience function that optionally creates a cloud-init user-data
  document, then renders it as a binary bytes blob. If the provided content is a CloudInitDoc,
  then simply renders it. Otherwise a new document is created using the provided
  content; then renders the document.

  This allows code that accepts a CloudInitDocConvertible as input to blindly
  render a cloud-init user-data document without worrying about normalizing it first.

  Args:
      content (CloudInitDocConvertible):
          The content to be rendered. If a CloudInitDoc, then it is directly rendered.
          Operwise a new CloudInitDoc is created using this content, and the new document
          is rendered.

  Returns:
      Optional[bytes]: The rendered cloud-init user-data document, as a binary bytes blob, or None
                     if it is a null/empty document.
  """
  cloud_init_doc = CloudInitDoc(content)
  # Note: include_mime_version is required by cloud-init for the top-level part,
  # so we don't even allow setting it to False.
  result = cloud_init_doc.render_binary(include_mime_version=True)
  return result

def render_cloud_init_base64(
      content: CloudInitDocConvertible
    ) -> Optional[str]:
  """Render cloud-init document as a base-64 string encoding of a binary blob.

  A convenience function that optionally creates a cloud-init user-data
  document, then renders it as a binary bytes blob encoded as base-64 string.
  If the provided content is a CloudInitDoc, then simply renders it.
  Otherwise a new document is created using the provided content; then
  renders the document.

  This allows code that accepts a CloudInitDocConvertible as input to blindly
  render a cloud-init user-data document without worrying about normalizing it first.

  Args:
      content (CloudInitDocConvertible):
          The content to be rendered. If a CloudInitDoc, then it is directly rendered.
          Operwise a new CloudInitDoc is created using this content, and the new document
          is rendered.

  Returns:
      Optional[str]: The rendered cloud-init user-data document, as a binary blob encoded
                     into a base-64 string, or None if it is a null/empty document.
  """
  cloud_init_doc = CloudInitDoc(content)
  # Note: include_mime_version is required by cloud-init for the top-level part,
  # so we don't even allow setting it to False.
  result = cloud_init_doc.render_base64(include_mime_version=True)
  return result
