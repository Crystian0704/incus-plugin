#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_instance
short_description: Manage Incus instances (create and start)
description:
  - Create and manage Incus instances.
  - Combines functionality of 'incus init' and 'incus launch'.
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the instance.
    required: true
    type: str
  remote:
    description:
      - Remote server to create the instance on.
    required: false
    type: str
  remote_image:
    description:
      - Image to use (e.g., 'images:debian/12').
    required: true
    type: str
  started:
    description:
      - If true, ensure instance is started.
      - If false, ensure instance is stopped.
      - Ignored if state is 'absent'.
    type: bool
    default: true
    required: false
  state:
    description:
      - State of the instance.
      - 'present': Ensure instance exists (and started/stopped based on 'started' param).
      - 'absent': Ensure instance is removed.
    type: str
    choices: ['present', 'absent']
    default: present
    required: false
  force:
    description:
      - Force removal of running instances (only used when state='absent').
    type: bool
    default: false
    required: false
  description:
    description:
      - Description of the instance.
    type: str
    required: false
  empty:
    description:
      - Create an empty instance.
    type: bool
    required: false
    default: false
  ephemeral:
    description:
      - Create an ephemeral instance.
    type: bool
    required: false
    default: false
  vm:
    description:
      - Create a virtual machine instead of a container.
    type: bool
    required: false
    default: false
  type:
    description:
      - Instance type (e.g. 'c1.micro').
    type: str
    required: false
  profiles:
    description:
      - List of profiles to apply to the instance.
    type: list
    elements: str
    required: false
  no_profiles:
    description:
      - Create the instance with no profiles.
    type: bool
    required: false
    default: false
  network:
    description:
      - Network name to attach to.
    type: str
    required: false
  storage:
    description:
      - Storage pool name.
    type: str
    required: false
  target:
    description:
      - Cluster member name to target.
    type: str
    required: false
  config:
    description:
      - "Key/value pairs for instance configuration (e.g. {'limits.cpu': '2'})."
    type: dict
    required: false
  devices:
    description:
      - Key/value pairs for device configuration.
    type: dict
    required: false
  user_data:
    description:
      - Cloud-init user-data content.
      - Sets 'cloud-init.user-data' config option.
    type: str
    required: false
  network_config:
    description:
      - Cloud-init network-config content.
      - Sets 'cloud-init.network-config' config option.
    type: str
    required: false
  vendor_data:
    description:
      - Cloud-init vendor-data content.
      - Sets 'cloud-init.vendor-data' config option.
    type: str
    required: false
  cloud_init_disk:
    description:
      - If true, attaches a 'cloud-init' disk device (source=cloud-init:config).
      - Required for VMs without incus-agent or specific images.
    type: bool
    default: false
    required: false
author:
  - "Antigravity"
'''
EXAMPLES = r'''
- name: Create a container with cloud-init
  crystian.incus.incus_instance:
    name: my-web-server
    remote_image: images:ubuntu/22.04/cloud
    user_data: |
      #cloud-config
      package_upgrade: true
      packages:
        - nginx
- name: Create a VM with cloud-init config disk
  crystian.incus.incus_instance:
    name: my-vm-server
    remote_image: images:debian/12/cloud
    vm: true
    cloud_init_disk: true
    user_data: "{{ lookup('file', 'user-data.yml') }}"
'''
RETURN = r'''
instance:
  description: Instance information
  returned: always
  type: dict
'''
from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import shlex
class IncusInstance(object):
    def __init__(self, module):
        self.module = module
        self.name_param = module.params['name']
        self.remote = module.params['remote']
        self.remote_image = module.params['remote_image']
        self.state = module.params['state']
        self.empty = module.params.get('empty', False)
        if self.state == 'present' and not self.empty and not self.remote_image:
            self.module.fail_json(msg="remote_image is required when creating or updating an instance (state=present)")
        self.name = self.name_param
        if self.remote:
            self.name = "{}:{}".format(self.remote, self.name_param)
        self.started = module.params['started']
        self.state = module.params['state']
        self.force = module.params['force']
        self.vm = module.params['vm']
        self.ephemeral = module.params['ephemeral']
        self.profiles = module.params['profiles']
        self.no_profiles = module.params['no_profiles']
        self.config = module.params['config'] or {}
        self.devices = module.params['devices'] or {}
        self.storage = module.params['storage']
        self.network = module.params['network']
        self.type = module.params['type']
        self.target = module.params['target']
        self.description = module.params['description']
        self.empty = module.params.get('empty', False)
        self.state = module.params['state']
        self.force = module.params['force']
        self.project = module.params.get('project')
        self.user_data = module.params.get('cloud_init_user_data')
        self.network_config = module.params.get('cloud_init_network_config')
        self.vendor_data = module.params.get('cloud_init_vendor_data')
        self.cloud_init_disk = module.params.get('cloud_init_disk')
        if self.user_data:
            self.config['cloud-init.user-data'] = self.user_data
        if self.network_config:
            self.config['cloud-init.network-config'] = self.network_config
        if self.vendor_data:
            self.config['cloud-init.vendor-data'] = self.vendor_data
        if self.cloud_init_disk:
            if 'cloud-init' not in self.devices:
                self.devices['cloud-init'] = {'type': 'disk', 'source': 'cloud-init:config'}
        self.incus_path = module.get_bin_path('incus', required=True)
    def _run_command(self, cmd, check_rc=True):
        try:
            rc, out, err = self.module.run_command(cmd, check_rc=check_rc)
            if check_rc and rc != 0:
                self.module.fail_json(msg="Command execution failed", cmd=cmd, rc=rc, stdout=out, stderr=err)
            return rc, out, err
        except Exception as e:
            self.module.fail_json(msg="Command execution exception: %s" % str(e), cmd=cmd)
    def get_instance_info(self):
        instance_name = self.name
        prefix = ""
        if ":" in self.name:
             parts = self.name.split(':', 1)
             prefix = parts[0] + ":"
             instance_name = parts[1]
        cmd = [self.incus_path, 'list', '--format=json', '{}^{}$'.format(prefix, instance_name)]
        rc, out, err = self._run_command(cmd, check_rc=False)
        if rc == 0:
            try:
                data = json.loads(out)
                if data and len(data) > 0:
                    return data[0]
            except ValueError:
                pass
            return None
        self.module.fail_json(msg="Failed to get instance info", cmd=cmd, rc=rc, stdout=out, stderr=err)
    def create_instance(self):
        cmd = [self.incus_path, 'init', self.remote_image, self.name]
        if self.vm:
            cmd.append('--vm')
        if self.ephemeral:
            cmd.append('--ephemeral')
        if self.empty:
            cmd.append('--empty')
        if self.no_profiles:
            cmd.append('--no-profiles')
        elif self.profiles:
            for p in self.profiles:
                cmd.extend(['--profile', p])
        if self.network:
             cmd.extend(['--network', self.network])
        if self.storage:
             cmd.extend(['--storage', self.storage])
        if self.type == 'virtual-machine':
             cmd.append('--vm')
        elif self.type == 'container':
             pass
        elif self.type:
             cmd.extend(['--type', self.type])
        if self.target:
             cmd.extend(['--target', self.target])
        if self.config:
            for k, v in self.config.items():
                cmd.extend(['--config', '{}={}'.format(k, v)]) 
        if self.description:
             cmd.extend(['--description', self.description])
        self._run_command(cmd)
    def start_instance(self):
        cmd = [self.incus_path, 'start', self.name]
        self._run_command(cmd)
    def stop_instance(self):
        cmd = [self.incus_path, 'stop', self.name]
        self._run_command(cmd)
    def delete_instance(self):
        cmd = [self.incus_path, 'delete', self.name]
        if self.force:
            cmd.append('--force')
        self._run_command(cmd)
    def get_instance_state(self):
        instance_name = self.name_param
        remote_prefix = ""
        if ":" in self.name_param:
            parts = self.name_param.split(':', 1)
            remote_prefix = parts[0] + ":"
            instance_name = parts[1]
        elif self.remote:
             remote_prefix = self.remote + ":"
        query_path = "{}/1.0/instances/{}/state".format(remote_prefix, instance_name)
        cmd = [self.incus_path, 'query', query_path]
        rc, out, err = self._run_command(cmd, check_rc=False)
        if rc == 0:
            try:
                return json.loads(out)
            except ValueError:
                pass
        return None
    def configure_devices(self):
        if not self.devices:
            return
        info = self.get_instance_info()
        current_devices = info.get('devices', {}) if info else {}
        for device_name, device_config in self.devices.items():
             if device_name in current_devices:
                 continue 
             cfg = device_config.copy()
             dtype = cfg.pop('type', None)
             if not dtype:
                 self.module.fail_json(msg="Device '{}' missing required 'type'".format(device_name))
             cmd = [self.incus_path, 'config', 'device', 'add', self.name, device_name, dtype]
             for k, v in cfg.items():
                 cmd.append('{}={}'.format(k, v))
             self._run_command(cmd)
    def run(self):
        info = self.get_instance_info()
        changed = False
        if self.state == 'absent':
            if info:
                if self.module.check_mode:
                    self.module.exit_json(changed=True, msg="Instance would be deleted")
                self.delete_instance()
                changed = True
                self.module.exit_json(changed=changed, instance=None, state=None)
            else:
                self.module.exit_json(changed=False, msg="Instance already absent")
        elif self.state == 'present':
            if not info:
                if self.module.check_mode:
                    self.module.exit_json(changed=True, msg="Instance would be created")
                self.create_instance()
                self.configure_devices()
                changed = True
                info = self.get_instance_info()
                if not info:
                     self.module.fail_json(msg="Instance created but could not be retrieved.", name=self.name)
            current_status = info['status'].lower()
            if self.started and current_status == 'stopped':
                 if self.module.check_mode:
                     self.module.exit_json(changed=True, msg="Instance would be started")
                 self.start_instance()
                 changed = True
            elif not self.started and current_status == 'running':
                 if self.module.check_mode:
                     self.module.exit_json(changed=True, msg="Instance would be stopped")
                 self.stop_instance()
                 changed = True
            if changed:
                info = self.get_instance_info()
            state_info = self.get_instance_state()
            self.module.exit_json(changed=changed, instance=info, state=state_info)
def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            remote=dict(type='str', default='local', required=False),
            remote_image=dict(type='str', required=False),
            started=dict(type='bool', default=True, required=False),
            state=dict(type='str', choices=['present', 'absent'], default='present', required=False),
            force=dict(type='bool', default=False, required=False),
            description=dict(type='str', required=False),
            empty=dict(type='bool', default=False),
            ephemeral=dict(type='bool', default=False),
            vm=dict(type='bool', default=False),
            type=dict(type='str', required=False),
            profiles=dict(type='list', elements='str', required=False),
            no_profiles=dict(type='bool', default=False),
            network=dict(type='str', required=False),
            storage=dict(type='str', required=False),
            target=dict(type='str', required=False),
            config=dict(type='dict', required=False),
            devices=dict(type='dict', required=False),
            project=dict(type='str', default='default', required=False),
            cloud_init_user_data=dict(type='str', required=False),
            cloud_init_network_config=dict(type='str', required=False),
            cloud_init_vendor_data=dict(type='str', required=False),
            cloud_init_disk=dict(type='bool', default=False, required=False),
        ),
        supports_check_mode=True,
    )
    creator = IncusInstance(module)
    creator.run()
if __name__ == '__main__':
    main()
