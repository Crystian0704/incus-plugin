#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_config
short_description: Manage Incus instance configuration and devices
description:
  - Manage configuration options (e.g. limits.memory) and devices for Incus instances.
  - This module complements C(incus_instance) which is primarily for creation/state.
  - Useful for modifying running instances or managing complex device setups.
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the instance.
    required: true
    type: str
  remote:
    description:
      - Remote server to target (e.g., 'myremote').
    required: false
    type: str
  state:
    description:
      - ensuring 'present' will update config/devices to match provided values.
      - ensuring 'absent' will remove the specified config keys or devices.
    type: str
    choices: ['present', 'absent']
    default: present
  config:
    description:
      - Dictionary of configuration options.
      - If state=present, sets these values.
      - If state=absent, removes these keys (values are ignored, can be list of keys or dict).
    type: raw
    required: false
  devices:
    description:
      - Dictionary of devices to manage.
      - Key is the device name.
      - Value is a dictionary containing 'type' (required for adding) and options.
      - If state=absent, removes these devices (values ignored, can be list of names or dict).
    type: raw
    required: false
author:
  - "Antigravity"
'''
EXAMPLES = r'''
- name: Set memory limit
  crystian.incus.incus_config:
    name: my-container
    config:
      limits.memory: 2GiB
- name: Add a network device
  crystian.incus.incus_config:
    name: my-container
    devices:
      eth1:
        type: nic
        nictype: bridged
        parent: incusbr0
- name: Update device MTU
  crystian.incus.incus_config:
    name: my-container
    devices:
      eth1:
        mtu: 1400
- name: Remove configuration
  crystian.incus.incus_config:
    name: my-container
    state: absent
    config:
      - limits.memory
- name: Remove device
  crystian.incus.incus_config:
    name: my-container
    state: absent
    devices:
      - eth1
'''
RETURN = r'''
# Default return values
'''
from ansible.module_utils.basic import AnsibleModule
import json
class IncusConfig(object):
    def __init__(self, module):
        self.module = module
        self.name_param = module.params['name']
        self.remote = module.params['remote']
        self.state = module.params['state']
        self.config = module.params['config']
        self.devices = module.params['devices']
        self.name = self.name_param
        if self.remote:
            self.name = "{}:{}".format(self.remote, self.name_param)
        self.incus_path = module.get_bin_path('incus', required=True)
    def _run_command(self, cmd, check_rc=True):
        try:
            rc, out, err = self.module.run_command(cmd, check_rc=check_rc)
            if check_rc and rc != 0:
                self.module.fail_json(msg="Command execution failed", cmd=cmd, rc=rc, stdout=out, stderr=err)
            return rc, out, err
        except Exception as e:
            self.module.fail_json(msg="Command execution exception: %s" % str(e), cmd=cmd)
    def get_instance_config(self):
        cmd = [self.incus_path, 'config', 'show', self.name]
        rc, out, err = self._run_command(cmd, check_rc=False)
        if rc != 0:
             self.module.fail_json(msg="Failed to get config", cmd=cmd, rc=rc, stdout=out, stderr=err)
        try:
            import yaml
            return yaml.safe_load(out)
        except ImportError:
            self.module.fail_json(msg="PyYAML is required to parse incus config output")
        except Exception as e:
            self.module.fail_json(msg="Failed to parse config YAML: %s" % str(e))
    def process_config(self, current_config):
        changed = False
        if not self.config:
            return changed
        if self.state == 'absent' and isinstance(self.config, list):
            target_config = {k: None for k in self.config}
        elif isinstance(self.config, dict):
            target_config = self.config
        else:
             self.module.fail_json(msg="'config' must be a dict or list (for absent)")
        local_config = current_config.get('config', {})
        for key, value in target_config.items():
            if self.state == 'present':
                val_str = str(value)
                if key not in local_config or local_config[key] != val_str:
                    if self.module.check_mode:
                        pass
                    else:
                        cmd = [self.incus_path, 'config', 'set', self.name, key, val_str]
                        self._run_command(cmd)
                    changed = True
            elif self.state == 'absent':
                if key in local_config:
                    if self.module.check_mode:
                        pass
                    else:
                        cmd = [self.incus_path, 'config', 'unset', self.name, key]
                        self._run_command(cmd)
                    changed = True
        return changed
    def process_devices(self, current_info):
        changed = False
        if not self.devices:
            return changed
        if self.state == 'absent' and isinstance(self.devices, list):
             target_devices = {k: {} for k in self.devices}
        elif isinstance(self.devices, dict):
             target_devices = self.devices
        else:
             self.module.fail_json(msg="'devices' must be a dict or list (for absent)")
        local_devices = current_info.get('devices', {})
        for dev_name, dev_conf in target_devices.items():
            if self.state == 'present':
                if dev_name not in local_devices:
                    dtype = dev_conf.get('type')
                    if not dtype:
                        self.module.fail_json(msg="Device '{}' missing required 'type' for creation".format(dev_name))
                    if self.module.check_mode:
                         pass
                    else:
                         cmd = [self.incus_path, 'config', 'device', 'add', self.name, dev_name, dtype]
                         for k, v in dev_conf.items():
                             if k != 'type':
                                 cmd.append('{}={}'.format(k, v))
                         self._run_command(cmd)
                    changed = True
                else:
                    current_dev_conf = local_devices[dev_name]
                    for k, v in dev_conf.items():
                        if k == 'type': continue 
                        val_str = str(v)
                        if k not in current_dev_conf or current_dev_conf[k] != val_str:
                             if self.module.check_mode:
                                 pass
                             else:
                                 cmd = [self.incus_path, 'config', 'device', 'set', self.name, dev_name, '{}={}'.format(k, val_str)]
                                 self._run_command(cmd)
                             changed = True
            elif self.state == 'absent':
                if dev_name in local_devices:
                    if self.module.check_mode:
                        pass
                    else:
                        cmd = [self.incus_path, 'config', 'device', 'remove', self.name, dev_name]
                        self._run_command(cmd)
                    changed = True
        return changed
    def run(self):
        try:
            current_info = self.get_instance_config()
        except Exception:
            self.module.fail_json(msg="Could not find instance '{}'".format(self.name))
        changed_config = self.process_config(current_info)
        changed_devices = self.process_devices(current_info)
        changed = changed_config or changed_devices
        self.module.exit_json(changed=changed)
def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            remote=dict(type='str', required=False),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            config=dict(type='raw', required=False),
            devices=dict(type='raw', required=False),
        ),
        supports_check_mode=True,
    )
    runner = IncusConfig(module)
    runner.run()
if __name__ == '__main__':
    main()
