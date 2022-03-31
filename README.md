cloud-init-gen: Simplified generation of cloud-init user-data documents
=================================================

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Latest release](https://img.shields.io/github/v/release/sammck/cloud-init-gen.svg?style=flat-square&color=b44e88)](https://github.com/sammck/cloud-init-gen/releases)

An API for simplified generation of [cloud-init](https://cloudinit.readthedocs.io/en/latest/) user-data documents.

Table of contents
-----------------

* [Introduction](#introduction)
* [Installation](#installation)
* [Usage](#usage)
  * [API](api)
* [Known issues and limitations](#known-issues-and-limitations)
* [Getting help](#getting-help)
* [Contributing](#contributing)
* [License](#license)
* [Authors and history](#authors-and-history)


Introduction
------------

[cloud-init](https://cloudinit.readthedocs.io/en/latest/) is the industry standard multi-distribution method for cross-platform cloud instance initialization. It is supported across all major public cloud providers (AWS EC2, Azure, Google Cloud, etc.), provisioning systems for private cloud infrastructure, and bare-metal installations.

When a cloud IAAS user creates a VM instance in the cloud (e.g., an EC2 instance), they can optionally provide a _user-data_ document.
This document is passed to [cloud-init](https://cloudinit.readthedocs.io/en/latest/) at VM boot time, which uses the document to,
among other things, configure the VM for first-time use by installing packages, creating OS users, running custom scripts, etc.

Python package `cloud-init-gen` provides a simple API for generation of a well-formed cloud-init _user-data_ document, and rendering the
document into a format expected by cloud service providers (typically base-64).

Some key features of cloud-init-gen:

* Type inference from #-comment and MIME-style headers, as well as explicit MIME-type.
* Automatic re-encoding with #-comment or MIME Conent-Type, minimizing rendered document size.
* Transparent support for multipart cloud-init _user-data_ documents, composed one part at a time.
* Automatic conversion from JSON-friendly structured data to YAML, typical for _cloud-config_ document parts.
* Support for custom MIME types and additional MIME headers.
* Automatic compression with GZIP if necessary to keep rendered binary under 16KB (the maximum _user-data_ size).
* Rendering to string, binary, or binary encoded as a base-64 string.

Installation
------------

### Prerequisites

**Python**: Python 3.7+ is required. See your OS documentation for instructions.

### From PyPi

The current released version of `cloud-init-gen` can be installed with 

```bash
pip3 install cloud-init-gen
```

### From GitHub

[Poetry](https://python-poetry.org/docs/master/#installing-with-the-official-installer) is required; it can be installed with:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Clone the repository and install cloud-init-gen into a private virtualenv with:

```bash
cd <parent-folder>
git clone https://github.com/sammck/cloud-init-gen.git
cd cloud-init-gen
poetry install
```

You can then launch a bash shell with the virtualenv activated using:

```bash
poetry shell
```


Usage
=====


Example
-------

Let's say you want to use [boto3](https://pypi.org/project/boto3/) to create an EC2 instance on
AWS, and you want to do a few things with cloud-init

  1. On every boot, before doing anything else, you want to clear `/var/log/per-boot.log` if it exists, and write the
     boot time to the newly cleared file
  2. On the first boot, you want to install a few Debian/Ubuntu packages, and you want to install the latest version of Docker.
  3. You want to set up docker for authentication to AWS ECR in the same region

```python
import shlex
import json
import boto3
from cloud_init_gen import CloudInitDoc

sess = boto3.session.Session()
aws_region = sess.region_name

sts = sess.client('sts')
resp = sts.get_caller_identity()
aws_account_id = resp['Account']

user_data = CloudInitDoc()

boot_hook = '''#boothook
#!/bin/bash
echo "Booted on $(date)" > /var/log/per-boot.log
'''

user_data.add(boot_hook)  # MIME type text/cloud-boothook is infered from the "#boothook" header.

ecr_domain: str = f"{aws_account_id}.dkr.ecr.{aws_region}.amazonaws.com"
docker_config_obj = {
    "credHelpers": {
        "public.ecr.aws": "ecr-login",
        ecr_domain: "ecr-login"
      }
  }
docker_config = json.dumps(docker_config_obj, separators=(',', ':'), sort_keys=True)

cloud_cfg = dict(
    repo_update = True,
    repo_upgrade = "all",
    apt = dict(
        sources = {
          "docker.list": dict(
              source = "deb [arch=amd64] https://download.docker.com/linux/ubuntu $RELEASE stable",
              keyid = "9DC858229FC7DD38854AE2D88D81803C0EBFCD88"
            ),
          },
      ),

    packages = [
        "jq",
        "awscli",
        "collectd",
        "ca-certificates",
        "curl",
        "gnupg",
        "lsb-release",
        "docker-ce",
        "docker-ce-cli",
        "amazon-ecr-credential-helper",
      ],

    runcmd = [
        [ "bash", "-c", f"mkdir -p /root/.docker && chmod 700 /root/.docker && echo {shlex.quote(docker_config)} > /root/.docker/config.json && chmod 600 /root/.docker/config.json" ],
        [ "bash", "-c", 'echo "it works!"' ],
      ],
  )

user_data.add(cloud_cfg)  # will be rendered as yaml with implicit MIME type text/cloud-config

print(f"Final user-data (text):\n====================\n{user_data.render()}\n====================")
print(f"Final user-data (base64):\n====================\n{user_data.render_base64()}\n====================")

ec2 = sess.client('ec2')
resp = ec2.run_instances(
    ...
    UserData=user_data.render_base64()   # boto3/EC2 expect user-data to be encoded with base-64
    ...
  )
```

Known issues and limitations
----------------------------

* Has not been tested for compatibility against cloud service providers other than AWS EC2.

Getting help
------------

Please report any problems/issues [here](https://github.com/sammck/cloud-init-gen/issues).

Contributing
------------

Pull requests welcome.

License
-------

cloud-init-gen is distributed under the terms of the [MIT License](https://opensource.org/licenses/MIT).  The license applies to this file and other files in the [GitHub repository](http://github.com/sammck/cloud-init-gen) hosting this file.

Authors and history
---------------------------

The author of cloud-init-gen is [Sam McKelvie](https://github.com/sammck).
