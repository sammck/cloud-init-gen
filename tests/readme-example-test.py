#!/usr/bin/env python3

from typing import cast

import shlex
import json
import boto3
from cloud_init_gen import CloudInitDoc, JsonableDict

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

# will be rendered as yaml with implicit MIME type text/cloud-config
user_data.add(cast(JsonableDict, cloud_cfg))

print(f"Final user-data (text):\n====================\n{user_data.render()}\n====================")
print(f"Final user-data (base64):\n====================\n{user_data.render_base64()}\n====================")
