#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_storage
short_description: Manage Incus storage pools
description:
  - Create, update, and delete Incus storage pools.
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the storage pool.
    required: true
    type: str
    aliases: [ pool ]
  driver:
    description:
      - Storage driver to use (e.g. dir, zfs, btrfs, lvm).
      - Required when creating a new pool.
    required: false
    type: str
  config:
    description:
      - Dictionary of configuration options for the storage pool.
    required: false
    type: dict
  description:
    description:
      - Description of the storage pool.
    required: false
    type: str
  state:
    description:
      - State of the storage pool.
      - 'present': Ensure pool exists and matches configuration.
      - 'absent': Ensure pool is deleted.
    required: false
    type: str
    choices: [ present, absent ]
    default: present
  remote:
    description:
      - The remote server.
      - Defaults to 'local'.
    required: false
    type: str
    default: local
  project:
    description:
      - The project context.
      - Defaults to 'default'.
    required: false
    type: str
    default: default
author:
  - Crystian (@crystian)
'''
EXAMPLES = r'''
- name: Create a dir storage pool
  crystian.incus.incus_storage:
    name: my-pool
    driver: dir
    config:
      source: /var/lib/incus/storage-pools/my-pool
    description: "My custom dir pool"
- name: Create a ZFS pool (loop backed)
  crystian.incus.incus_storage:
    name: zfs-pool
    driver: zfs
    config:
      size: 10GiB
- name: Delete a pool
  crystian.incus.incus_storage:
    name: my-pool
    state: absent
'''
RETURN = r'''
msg:
  description: Status message
  returned: always
  type: str
pool:
  description: Pool configuration
  returned: when available
  type: dict
'''
from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import os
class IncusStorage(object):
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.driver = module.params['driver']
        self.config = module.params['config']
        self.description = module.params['description']
        self.state = module.params['state']
        self.remote = module.params['remote']
        self.project = module.params['project']
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
    def get_pool_info(self):
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
        rc, out, err = self.run_incus(['storage', 'show', target])
        if rc == 0:
            import yaml
            try:
                return yaml.safe_load(out)
            except ImportError:
                pass
        return None
    def create(self):
        cmd_args = ['storage', 'create', self.name, self.driver]
        if self.remote and self.remote != 'local':
            cmd_args[2] = "{}:{}".format(self.remote, self.name)
        if self.description:
             cmd_args.extend(['--description', self.description])
        if self.config:
            for k, v in self.config.items():
                cmd_args.append("{}={}".format(k, v))
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Storage pool would be created")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to create storage pool: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Storage pool created")
    def update(self, current_info):
        changed = False
        msgs = []
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
        if self.description is not None and current_info.get('description') != self.description:
            if not self.module.check_mode:
                pass
            pass
        if self.config:
            current_config = current_info.get('config', {})
            for k, v in self.config.items():
                curr_val = current_config.get(k, '')
                if str(curr_val) != str(v):
                    if not self.module.check_mode:
                        rc, out, err = self.run_incus(['storage', 'set', target, "{}={}".format(k, v)])
                        if rc != 0:
                            self.module.fail_json(msg="Failed to set config option '{}': {}".format(k, err))
                    changed = True
                    msgs.append("Updated config '{}'".format(k))
        if changed:
            self.module.exit_json(changed=True, msg=", ".join(msgs))
        else:
            self.module.exit_json(changed=False, msg="Storage pool already matches configuration")
    def delete(self):
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Storage pool would be deleted")
        rc, out, err = self.run_incus(['storage', 'delete', target])
        if rc != 0:
            self.module.fail_json(msg="Failed to delete storage pool: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Storage pool deleted")
    def run(self):
        current_info = self.get_pool_info()
        if self.state == 'present':
            if not current_info:
                if not self.driver:
                    self.module.fail_json(msg="'driver' is required when creating a storage pool")
                self.create()
            else:
                self.update(current_info)
        elif self.state == 'absent':
            if current_info:
                self.delete()
            else:
                self.module.exit_json(changed=False, msg="Storage pool not found")
def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, aliases=['pool']),
            driver=dict(type='str', required=False),
            config=dict(type='dict', required=False),
            description=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            remote=dict(type='str', default='local', required=False),
            project=dict(type='str', default='default', required=False),
        ),
        supports_check_mode=True,
    )
    manager = IncusStorage(module)
    manager.run()
if __name__ == '__main__':
    main()
