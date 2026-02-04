#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_list
short_description: List Incus instances
description:
  - List Incus instances using the C(incus list) command.
  - Returns a list of instances with their configuration and state.
author:
  - "Antigravity"
options:
  filters:
    description:
      - List of filters to apply (e.g. C("status=running"), C("type=container")).
      - Can be a list of strings or a dictionary.
    type: raw
    required: false
  remote:
    description:
      - The remote server to query (e.g. C("kawa")).
    type: str
    required: false
  all_remotes:
    description:
      - List instances from all configured remotes with protocol 'incus'.
    type: bool
    default: false
    required: false
  all_projects:
    description:
      - List instances from all projects.
    type: bool
    default: false
    required: false
  project:
    description:
      - Project to list instances from.
    type: str
    required: false
'''
EXAMPLES = r'''
- name: List all local instances
  crystian.incus.incus_list:
  register: all_instances
- name: List running containers
  crystian.incus.incus_list:
    filters:
      - status=Running
      - type=container
  register: running_containers
- name: List instances on remote
  crystian.incus.incus_list:
    remote: kawa
  register: remote_instances
'''
RETURN = r'''
list:
  description: List of instances
  returned: always
  type: list
  sample:
    - name: my-container
      status: Running
      type: container
      # ... (full incus config)
'''
from ansible.module_utils.basic import AnsibleModule
import json
import subprocess
class IncusList(object):
    def __init__(self, module):
        self.module = module
        self.filters = module.params.get('filters')
        self.remote = module.params.get('remote')
        self.all_remotes = module.params.get('all_remotes')
        self.all_projects = module.params.get('all_projects')
        self.project = module.params.get('project')
        self.incus_path = module.get_bin_path('incus', required=True)
    def _run_command(self, cmd, check_rc=True):
        try:
            rc, out, err = self.module.run_command(cmd, check_rc=check_rc)
            return rc, out, err
        except Exception as e:
            self.module.fail_json(msg="Failed to run command: {}".format(e))
    def get_remotes(self):
        cmd = [self.incus_path, 'remote', 'list', '--format=json']
        rc, out, err = self._run_command(cmd)
        try:
            data = json.loads(out)
            return [name for name, info in data.items() if info.get('Protocol') == 'incus']
        except ValueError:
            self.module.fail_json(msg="Failed to parse remote list", stdout=out, stderr=err)
    def list_instances(self, target_remote=None):
        cmd = [self.incus_path, 'list', '--format=json']
        if self.all_projects:
            cmd.append('--all-projects')
        elif self.project:
            cmd.extend(['--project', self.project])
        target = ""
        current_remote = target_remote if target_remote else self.remote
        if current_remote:
            target = "{}:".format(current_remote)
        if target:
            cmd.append(target)
        if self.filters:
            if isinstance(self.filters, list):
                cmd.extend(self.filters)
            elif isinstance(self.filters, dict):
                for k, v in self.filters.items():
                    cmd.append("{}={}".format(k, v))
            else:
                 cmd.append(str(self.filters))
        rc, out, err = self._run_command(cmd)
        try:
            return json.loads(out)
        except ValueError:
            self.module.fail_json(msg="Failed to parse incus list JSON output", stdout=out, stderr=err)
    def run(self):
        if self.all_remotes:
            remotes = self.get_remotes()
            all_instances = []
            for r in remotes:
                instances = self.list_instances(target_remote=r)
                for i in instances:
                    if 'location' not in i or i['location'] == 'none':
                         i['location'] = r
                all_instances.extend(instances)
            self.module.exit_json(changed=False, list=all_instances)
        else:
            instances = self.list_instances()
            self.module.exit_json(changed=False, list=instances)
def main():
    module = AnsibleModule(
        argument_spec=dict(
            filters=dict(type='raw', required=False),
            remote=dict(type='str', required=False),
            all_remotes=dict(type='bool', default=False),
            all_projects=dict(type='bool', default=False),
            project=dict(type='str', required=False),
        ),
        supports_check_mode=True,
    )
    lister = IncusList(module)
    lister.run()
if __name__ == '__main__':
    main()
