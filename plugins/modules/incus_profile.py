#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: incus_profile
short_description: Manage Incus profiles
description:
  - Create, update, and delete Incus configuration profiles.
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the profile.
    required: true
    type: str
  description:
    description:
      - Description of the profile.
    required: false
    type: str
  config:
    description:
      - Dictionary of configuration options (e.g., 'limits.cpu': '2').
    required: false
    type: dict
  devices:
    description:
      - Dictionary of devices.
    required: false
    type: dict
  state:
    description:
      - State of the profile.
      - 'present': Ensure profile exists and matches config.
      - 'absent': Ensure profile is deleted.
    required: false
    type: str
    choices: [ present, absent ]
    default: present
  rename_from:
    description:
      - If provided, and appropriate, rename an existing profile to 'name'.
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
      - The project context.
      - Defaults to 'default'.
    required: false
    type: str
    default: default
author:
  - Crystian (@crystian)
'''

EXAMPLES = r'''
- name: Create a web server profile
  crystian.incus.incus_profile:
    name: web-profile
    description: "Profile for web servers"
    config:
      limits.cpu: "2"
      limits.memory: "4GiB"
    devices:
      eth0:
        name: eth0
        type: nic
        network: incusbr0
      root:
        path: /
        pool: default
        type: disk

- name: Delete a profile
  crystian.incus.incus_profile:
    name: web-profile
    state: absent
'''

RETURN = r'''
msg:
  description: Status message
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import os
import yaml
import copy

class IncusProfile(object):
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.source = module.params['source']
        self.description = module.params['description']
        self.config = module.params['config']
        self.devices = module.params['devices']
        self.state = module.params['state']
        self.rename_from = module.params['rename_from']
        self.remote = module.params['remote']
        self.project = module.params['project']

    def load_source(self):
        if not self.source:
             return {}
        
        if not os.path.exists(self.source):
             self.module.fail_json(msg="Source file '{}' not found".format(self.source))
             
        try:
            with open(self.source, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.module.fail_json(msg="Failed to read source file '{}': {}".format(self.source, str(e)))

    def get_desired_state(self, current_profile=None):
        # Base is source file or empty
        desired = self.load_source()
        
        # If current profile exists and we handle 'update', do we merge with current?
        # Ansible philosophy: Desired state is what we define.
        # If source is NOT provided, and we only provide specific keys (e.g. config={'a':1}),
        # do we want to Keep existing other keys (Merge) or Replace?
        # In my method `update` previously, I implemented Merge.
        # But if `source` is provided, `source` IS the base truth.
        # So: Desired = Source + Params.
        
        # If Source is NOT provided:
        # We need to decide: Are we managing the WHOLE profile or specific keys?
        # The prompt implies "inclusion of file... so it can be extensive".
        # This suggests defining the WHOLE profile.
        # But `config` param allows partial edits?
        
        # Decision:
        # If `source` is provided: Desired = Source content updated by params.
        # If `source` is NOT provided: Desired = Current Profile updated by params.
        
        if not self.source and current_profile:
             # Merge params into current (Partial Update logic)
             desired = copy.deepcopy(current_profile)
        elif not self.source and not current_profile:
             # Default empty base
             desired = {'config': {}, 'devices': {}, 'description': ''}
             
        # Merge Params
        if self.description is not None:
             desired['description'] = self.description
             
        if self.config is not None:
             if 'config' not in desired or desired['config'] is None:
                 desired['config'] = {}
             
             for k, v in self.config.items():
                 # Handle removals or updates
                 # If we assume merges:
                 if v is None:
                     if k in desired['config']: del desired['config'][k]
                 else:
                     desired['config'][k] = str(v)

        if self.devices is not None:
             if 'devices' not in desired or desired['devices'] is None:
                 desired['devices'] = {}
                 
             for k, v in self.devices.items():
                 # Device merge logic
                 # If user supplies device 'eth0', it replaces 'eth0' from source
                 desired['devices'][k] = v
                 
        return desired

    # (Keep run_incus and run_incus_input)
    # Re-using existing methods but integrating get_desired_state logic

    def run_incus(self, args, check_rc=True):
        cmd = ['incus']
        if self.project:
            cmd.extend(['--project', self.project])
        cmd.extend(args)
        
        env = os.environ.copy()
        env['LC_ALL'] = 'C'
        
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=env)
        stdout, stderr = p.communicate()
        
        if check_rc and p.returncode != 0:
             return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
             
        return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
    
    def run_incus_input(self, args, input_data):
        cmd = ['incus']
        if self.project:
            cmd.extend(['--project', self.project])
        cmd.extend(args)

        env = os.environ.copy()
        env['LC_ALL'] = 'C'
        
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=env)
        stdout, stderr = p.communicate(input=input_data.encode('utf-8'))
        return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')

    def get_profile(self):
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
            
        rc, out, err = self.run_incus(['profile', 'show', target], check_rc=False)
        if rc == 0:
            try:
                return yaml.safe_load(out)
            except:
                pass
        return None

    def exists(self):
        return self.get_profile() is not None

    def create(self):
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
            
        # Create empty
        rc, out, err = self.run_incus(['profile', 'create', target], check_rc=False)
        if rc != 0:
             self.module.fail_json(msg="Failed to create profile: " + err, stdout=out, stderr=err)
             
        # Configure
        self.update(new_create=True)
    
    def update(self, new_create=False):
        current = self.get_profile()
        if not current:
            self.module.fail_json(msg="Profile not found for update")

        # Calculate Desired State
        desired = self.get_desired_state(current_profile=current)
        
        # Compare
        updated = False
        
        # Check description
        if current.get('description') != desired.get('description'):
            updated = True
            
        # Check config
        if current.get('config') != desired.get('config'):
            updated = True
            
        # Check devices
        if current.get('devices') != desired.get('devices'):
            updated = True
            
        if not updated and not new_create:
            self.module.exit_json(changed=False, msg="Profile matches configuration")
            
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Profile would be updated")
            
        # Apply YAML
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
            
        yaml_content = yaml.dump(desired)
        rc, out, err = self.run_incus_input(['profile', 'edit', target], yaml_content)
        
        if rc != 0:
             self.module.fail_json(msg="Failed to update profile: " + err, stdout=out, stderr=err)
             
        self.module.exit_json(changed=True, msg="Profile updated")

    def delete(self):
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
            
        if self.module.check_mode:
             self.module.exit_json(changed=True, msg="Profile would be deleted")
             
        rc, out, err = self.run_incus(['profile', 'delete', target], check_rc=False)
        if rc != 0:
             self.module.fail_json(msg="Failed to delete profile: " + err, stdout=out, stderr=err)
             
        self.module.exit_json(changed=True, msg="Profile deleted")

    def run(self):
        profile = self.get_profile()
        
        if self.state == 'present':
            if not profile:
                if self.module.check_mode:
                    self.module.exit_json(changed=True, msg="Profile would be created")
                self.create()
            else:
                self.update()
                
        elif self.state == 'absent':
             if profile:
                 self.delete()
             else:
                 self.module.exit_json(changed=False, msg="Profile not found")

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            source=dict(type='path', required=False),
            description=dict(type='str', required=False),
            config=dict(type='dict', required=False),
            devices=dict(type='dict', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            rename_from=dict(type='str', required=False),
            remote=dict(type='str', default='local', required=False),
            project=dict(type='str', default='default', required=False),
        ),
        supports_check_mode=True,
    )

    manager = IncusProfile(module)
    manager.run()

if __name__ == '__main__':
    main()
