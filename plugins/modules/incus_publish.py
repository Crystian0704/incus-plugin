#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_publish
short_description: Publish Incus images from instances
description:
  - Create new images from existing instances or snapshots using `incus publish`.
version_added: "1.0.0"
options:
  instance:
    description:
      - Name of the source instance.
    required: true
    type: str
    aliases: [ name, source ]
  snapshot:
    description:
      - Name of the snapshot to publish from.
      - If not provided, publishes the current instance state (requires instance to be stopped usually).
    required: false
    type: str
  alias:
    description:
      - Alias for the new image.
    required: true
    type: str
  public:
    description:
      - Whether the new image should be public.
    required: false
    type: bool
    default: false
  expire:
    description:
      - Expiration date for the new image.
    required: false
    type: str
  reuse:
    description:
      - Overwrite existing image alias if it exists.
    required: false
    type: bool
    default: false
  properties:
    description:
      - Dictionary of properties to set on the new image.
    required: false
    type: dict
  compression:
    description:
      - Compression algorithm to use.
    required: false
    type: str
  remote:
    description:
      - The remote server.
      - Defaults to 'local'.
    required: false
    type: str
    default: local
  project:
    description:
      - The project the instance belongs to.
      - Defaults to 'default'.
    required: false
    type: str
    default: default
author:
  - Crystian (@crystian)
'''
EXAMPLES = r'''
- name: Publish instance as image
  crystian.incus.incus_publish:
    instance: my-container
    alias: my-custom-image
    public: true
- name: Publish snapshot
  crystian.incus.incus_publish:
    instance: my-container
    snapshot: snap0
    alias: my-stable-image
    reuse: true
'''
RETURN = r'''
msg:
  description: Status message
  returned: always
  type: str
fingerprint:
  description: Fingerprint of the created image
  returned: always
  type: str
'''
from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import os
class IncusPublish(object):
    def __init__(self, module):
        self.module = module
        self.instance = module.params['instance']
        self.snapshot = module.params['snapshot']
        self.alias = module.params['alias']
        self.public = module.params['public']
        self.expire = module.params['expire']
        self.reuse = module.params['reuse']
        self.properties = module.params['properties']
        self.compression = module.params['compression']
        self.remote = module.params['remote']
        self.project = module.params['project']
        self.target_source = self.instance
        if self.snapshot:
            self.target_source = "{}/{}".format(self.instance, self.snapshot)
        if self.remote and self.remote != 'local':
             self.target_source = "{}:{}".format(self.remote, self.target_source)
    def run_incus(self, args):
        cmd = ['incus']
        if self.project:
            cmd.extend(['--project', self.project])
        cmd.extend(args)
        env = os.environ.copy()
        env['LC_ALL'] = 'C'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        stdout, stderr = p.communicate()
        return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
    def check_alias_exists(self):
        target_alias = self.alias
        if self.remote and self.remote != 'local':
            target_alias = "{}:{}".format(self.remote, self.alias)
        cmd_args = ['image', 'info', target_alias]
        rc, _, _ = self.run_incus(cmd_args)
        return rc == 0
    def run(self):
        if self.check_alias_exists():
            if not self.reuse:
                self.module.exit_json(changed=False, msg="Image alias '{}' already exists".format(self.alias))
            else:
                pass
        cmd_args = ['publish', self.target_source]
        cmd_args.extend(['--alias', self.alias])
        if self.public:
            cmd_args.append('--public')
        if self.reuse:
            cmd_args.append('--reuse')
        if self.expire:
            cmd_args.extend(['--expire', self.expire])
        if self.compression:
            cmd_args.extend(['--compression', self.compression])
        if self.properties:
            for k, v in self.properties.items():
                cmd_args.append("{}={}".format(k, v))
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Image would be published")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to publish image: " + err, stdout=out, stderr=err)
        fingerprint = ""
        for line in out.splitlines():
            if "published with fingerprint:" in line:
                fingerprint = line.split(":")[-1].strip()
        self.module.exit_json(changed=True, msg="Image published", fingerprint=fingerprint)
def main():
    module = AnsibleModule(
        argument_spec=dict(
            instance=dict(type='str', required=True, aliases=['name', 'source']),
            snapshot=dict(type='str', required=False),
            alias=dict(type='str', required=True),
            public=dict(type='bool', default=False),
            expire=dict(type='str', required=False),
            reuse=dict(type='bool', default=False),
            properties=dict(type='dict', required=False),
            compression=dict(type='str', required=False),
            remote=dict(type='str', default='local', required=False),
            project=dict(type='str', default='default', required=False),
        ),
        supports_check_mode=True,
    )
    manager = IncusPublish(module)
    manager.run()
if __name__ == '__main__':
    main()
