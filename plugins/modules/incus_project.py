#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_project
short_description: Manage Incus projects
description:
  - Create, update, and delete Incus projects.
  - configure limits, features, and restrictions.
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the project.
    required: true
    type: str
  description:
    description:
      - Description of the project.
    required: false
    type: str
  config:
    description:
      - "Dictionary of configuration options (e.g., 'features.images': 'false')."
      - Handles limits, restrictions, and features.
    required: false
    type: dict
  source:
    description:
      - Path to a YAML file containing project definition.
    required: false
    type: path
  state:
    description:
      - State of the project.
      - 'present': Ensure project exists and matches config.
      - 'absent': Ensure project is deleted.
    required: false
    type: str
    choices: [ present, absent ]
    default: present
  rename_from:
    description:
      - If provided, rename the specified project to 'name'.
    required: false
    type: str
  remote:
    description:
      - The remote server.
      - Defaults to 'local'.
    required: false
    type: str
    default: local
author:
  - Crystian (@crystian)
'''
EXAMPLES = r'''
- name: Create a restricted project
  crystian.incus.incus_project:
    name: dev-project
    description: "Development environment"
    config:
      features.images: "false"
      features.profiles: "true"
      limits.containers: "5"
      restricted: "true"
      restricted.containers.nesting: "allow"
- name: Delete a project
  crystian.incus.incus_project:
    name: dev-project
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
class IncusProject(object):
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.source = module.params['source']
        self.description = module.params['description']
        self.config = module.params['config']
        self.state = module.params['state']
        self.rename_from = module.params['rename_from']
        self.remote = module.params['remote']
    def run_incus(self, args, check_rc=True):
        cmd = ['incus']
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
        cmd.extend(args)
        env = os.environ.copy()
        env['LC_ALL'] = 'C'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=env)
        stdout, stderr = p.communicate(input=input_data.encode('utf-8'))
        return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
    def get_project_info(self, name_override=None):
        name = name_override or self.name
        target = name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, name)
        rc, out, err = self.run_incus(['project', 'show', target], check_rc=False)
        if rc == 0:
            try:
                return yaml.safe_load(out)
            except:
                pass
        return None
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
    def get_desired_state(self, current_info=None):
        desired = self.load_source()
        if not self.source and current_info:
             desired = copy.deepcopy(current_info)
        elif not self.source and not current_info:
             desired = {'config': {}, 'description': ''}
        if self.description is not None:
             desired['description'] = self.description
        if self.config is not None:
             if 'config' not in desired or desired['config'] is None:
                 desired['config'] = {}
             for k, v in self.config.items():
                 if v is None:
                     if k in desired['config']: del desired['config'][k]
                 else:
                     desired['config'][k] = str(v)
        return desired
    def create(self):
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
        rc, out, err = self.run_incus(['project', 'create', target], check_rc=False)
        if rc != 0:
             self.module.fail_json(msg="Failed to create project: " + err, stdout=out, stderr=err)
        self.update(new_create=True)
    def update(self, new_create=False):
        current = self.get_project_info()
        if not current:
            self.module.fail_json(msg="Project not found for update")
        desired = self.get_desired_state(current_info=current)
        updated = False
        if current.get('description') != desired.get('description'):
            updated = True
        if current.get('config') != desired.get('config'):
            updated = True
        if not updated and not new_create:
            self.module.exit_json(changed=False, msg="Project matches configuration")
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Project would be updated")
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
        yaml_content = yaml.dump(desired)
        rc, out, err = self.run_incus_input(['project', 'edit', target], yaml_content)
        if rc != 0:
             self.module.fail_json(msg="Failed to update project: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Project updated")
    def delete(self):
        target = self.name
        if self.remote and self.remote != 'local':
            target = "{}:{}".format(self.remote, self.name)
        if self.module.check_mode:
             self.module.exit_json(changed=True, msg="Project would be deleted")
        rc, out, err = self.run_incus(['project', 'delete', target], check_rc=False)
        if rc != 0:
             self.module.fail_json(msg="Failed to delete project: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Project deleted")
    def rename(self):
         target_old = self.rename_from
         target_new = self.name
         if self.remote and self.remote != 'local':
             target_old = "{}:{}".format(self.remote, self.rename_from)
             target_new = "{}:{}".format(self.remote, self.name)
         if self.module.check_mode:
             self.module.exit_json(changed=True, msg="Project would be renamed")
         rc, out, err = self.run_incus(['project', 'rename', target_old, target_new], check_rc=False)
         if rc != 0:
             self.module.fail_json(msg="Failed to rename project: " + err, stdout=out, stderr=err)
         self.module.exit_json(changed=True, msg="Project renamed")
    def run(self):
        current = self.get_project_info()
        if self.state == 'present':
            if self.rename_from:
                old_info = self.get_project_info(name_override=self.rename_from)
                if old_info and not current:
                    self.rename()
                    return 
                elif old_info and current:
                     self.module.fail_json(msg="Cannot rename: valid project '{}' already exists".format(self.name))
                elif not old_info:
                     self.module.fail_json(msg="Cannot rename: source project '{}' not found".format(self.rename_from))
            if not current:
                if self.module.check_mode:
                    self.module.exit_json(changed=True, msg="Project would be created")
                self.create()
            else:
                self.update()
        elif self.state == 'absent':
             if current:
                 self.delete()
             else:
                 self.module.exit_json(changed=False, msg="Project not found")
def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            description=dict(type='str', required=False),
            config=dict(type='dict', required=False),
            source=dict(type='path', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            rename_from=dict(type='str', required=False),
            remote=dict(type='str', default='local', required=False),
        ),
        supports_check_mode=True,
    )
    manager = IncusProject(module)
    manager.run()
if __name__ == '__main__':
    main()
