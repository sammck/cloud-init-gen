#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Mapping between cloud-init mime types and '#' comment header conventions
"""

from typing import Optional, List, Dict

class CloudInitPartType:
  """
  A descriptor that correlates a MIME type with it's associated cloud-init comment
  header line; e.g., "Content-Type: text/cloud-config" with "#cloud-config". This
  is used by the renderer to pick the optimal rendering of the part.
  """

  mime_type: str
  """The full MIME type; e.g., 'text/cloud-boothook'"""
  mime_subtype: str

  comment_tag: Optional[str]=None
  """The portion of comment_line after '#'. For '#!', this is just '!', and does not include the
     script commandline. If None, there is no comment header associated with the MIME type."""

  comment_line: Optional[str]=None
  """The portion of the comment header that identifies its MIME type. For '#!', this is just '!#', and does not include the
     script commandline. If None, there is no comment header associated with the MIME type."""

  def __init__(self, mime_subtype: str, comment_tag: Optional[str]=None):
    """Construct a descriptor mapping a MIME type to a comment tag

    Args:
        mime_subtype (str): The MIME type without the leading "text/"
        comment_tag (Optional[str], optional):
                            The comment tag without the leading "#", or None
                            if there is no comment header associated with the
                            MIME type. For shebang types, this is just "!".
                            Defaults to None.
    """
    self.mime_subtype = mime_subtype
    self.mime_type = 'text/' + mime_subtype
    self.comment_tag = comment_tag
    self.comment_line = None if comment_tag is None else '#' + comment_tag

_part_type_list: List[CloudInitPartType] = [
    CloudInitPartType('cloud-boothook', 'boothook'),                    # A script with a shebang header
    CloudInitPartType('cloud-config', 'cloud-config'),                  # A YAML doc with rich config data
    CloudInitPartType('cloud-config-archive', 'cloud-config-archive'),  # a YAML doc that contains a list of docs, like multipart mime
    CloudInitPartType('cloud-config-jsonp', 'cloud-config-jsonp'),      # fine-grained merging with vendor-provided cloud-config
    CloudInitPartType('jinja2', "# template: jinja"),                   # expand jinja2 template. 2nd line is comment describing actual part type
    CloudInitPartType('part-handler', 'part-handler'),                  # part contains python code that can process custom mime types for subsequent parts
    CloudInitPartType('upstart-job', 'upstart-job'),                    # content plated into a file under /etc/init, to be consumed by upstart
    CloudInitPartType('x-include-once-url', 'include-once'),            # List of urls that are read one at a time and processed as any item, but only once
    CloudInitPartType('x-include-url', 'include'),                      # list of urls that are read one at a time and processed as any item
    CloudInitPartType('x-shellscript', '!'),                            # simple userdata shell script (comment line has variable chars)
    CloudInitPartType('x-shellscript-per-boot'),                        # shell script run on every boot
    CloudInitPartType('x-shellscript-per-instance'),                    # shell script run once per unique instance
    CloudInitPartType('x-shellscript-per-once'),                        # shell script run only once
  ]
"""A list of MIME types that are pre-known to cloud-init"""

mime_to_cloud_init_part_type: Dict[str, CloudInitPartType] = dict((x.mime_type, x) for x in _part_type_list)
"""A map from full MIME type to associated CloudInitPartType"""

comment_to_cloud_init_part_type: Dict[str, CloudInitPartType] = dict((x.comment_line, x) for x in _part_type_list if not x.comment_line is None)
"""A map from comment header line (Just "#!" for shebang lines) to associated CloudInitPartType"""
