#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""
Utilities to assist in constructing well-formed user-data blocks to be
processed by cloud-init.

See https://cloudinit.readthedocs.io/en/latest/topics/format.html for
details on the format of the cloud-init user-data block.

cloud-init and user-data are commonly used by cloud infrastructure
services (e.g., AWS EC2) to give a way for the user to force a
newly provisioned cloud VM to initialize itself on first boot. For
example, you can provide a command script to run, or you can specify
a list of packages to be installed, or user accounts to be created.

The specification for user-data is quite rich, and it is even possible
to embed multiple independent initialization documents in a single
user-data block. This is achieved with multi-part MIME encoding.

Some user-data parts may include structured data, encoded as YAML.

The classes and functions in this module take care of all the formatting
and rendering, and conversion from structured Jsonable data to YAML. In
addition, if the resulting binary data exceeds 16KB (the limit for cloud-init
user-data), the block will be compressed with GZIP in an attempt to fit
it into the allowed maximum size.

Once you have built and rendered a user-data block, you pass it to
the cloud services provider at VM creation time (generally as
a base64-encoded string). For example, if you are using boto3 to
drive AWS ec2, you might say:

import boto3
from cloud_init_gen import CloudInitDoc

ec2 = boto3.client('ec2')

user_data = CloudInitDoc()
user_data.add('''#boothook\n#!/bin/bash\necho "running boot-hook now" > /var/log/boothook.log''')

cloud_cfg = dict(
    groups = [
        {
            'ubuntu': [ 'root', 'sys' ]
          },
        'cloud-users'
      ]
  )
user_data.add(cloud_cfg)  # will be rendered as yaml with MIME type text/cloud-config

resp = ec2.run_instances(
    ...
    UserData=user_data.render_base64()
    ...
  )

"""

from .version import __version__

from .typehints import JsonableDict
from .exceptions import CloudInitGenError
from .renderable import CloudInitRenderable
from .part import CloudInitPart, MimeHeadersConvertible
from .cloud_init_doc import CloudInitDoc, CloudInitDocConvertible
from .simple import (
    render_cloud_init_text,
    render_cloud_init_binary,
    render_cloud_init_base64
  )

__all__ = [
    "JsonableDict", 
    "CloudInitGenError",
    "CloudInitRenderable",
    "CloudInitPart",
    "MimeHeadersConvertible",
    "CloudInitDoc",
    "CloudInitDocConvertible",
    "render_cloud_init_text",
    "render_cloud_init_binary",
    "render_cloud_init_base64",
  ]
