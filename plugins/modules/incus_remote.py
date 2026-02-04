#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: incus_remote
short_description: Manage Incus remotes
description:
  - Add, remove, and manage Incus remote servers.
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the remote.
    required: true
    type: str
  url:
    description:
      - URL of the remote (e.g. https://1.2.3.4:8443).
      - Required when adding a new remote, unless token implies it.
    required: false
    type: str
  protocol:
    description:
      - Protocol to use (incus or simplestreams).
    required: false
    type: str
    default: incus
  token:
    description:
      - Trust token for adding the remote.
    required: false
    type: str
  password:
    description:
      - Trust password (if token not provided).
      - Note: Prefer tokens for better security and non-interactive usage.
    required: false
    type: str
  accept_certificate:
    description:
      - Whether to automatically accept the server certificate.
    required: false
    type: bool
    default: false
  state:
    description:
      - State of the remote.
      - 'present': Ensure remote exists.
      - 'absent': Ensure remote is removed.
    required: false
    type: str
    choices: [ present, absent ]
    default: present
  project:
    description:
      - Default project to use for this remote.
    required: false
    type: str
author:
  - Crystian (@crystian)
'''

EXAMPLES = r'''
- name: Add a remote using a token
  crystian.incus.incus_remote:
    name: my-cluster
    token: "eyJhbGciOi..."
    accept_certificate: true

- name: Add a remote using password and URL
  crystian.incus.incus_remote:
    name: my-server
    url: "https://192.168.1.50:8443"
    password: "secret-password"
    accept_certificate: true

- name: Remove a remote
  crystian.incus.incus_remote:
    name: my-server
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

class IncusRemote(object):
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.url = module.params['url']
        self.protocol = module.params['protocol']
        self.token = module.params['token']
        self.password = module.params['password']
        self.accept_certificate = module.params['accept_certificate']
        self.state = module.params['state']
        self.project = module.params['project']

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

    def get_remote_info(self):
        rc, out, err = self.run_incus(['remote', 'list', '--format=json'], check_rc=False)
        if rc == 0:
            try:
                remotes = json.loads(out)
                # Remotes is a dict: {name: {url: ..., ...}}
                if self.name in remotes:
                    return remotes[self.name]
            except:
                pass
        return None

    def create(self):
        # incus remote add <name> <url> [flags]
        args = ['remote', 'add', self.name]
        
        if self.url:
            args.append(self.url)
            if self.token:
                 args.append('--token=' + self.token)
            elif self.password:
                 args.append('--password=' + self.password)
        elif self.token:
             args.append(self.token)
        elif self.password:
             # Password with no URL? Unlikely.
             # Maybe simplestreams public?
             pass
            
        if self.accept_certificate:
            args.append('--accept-certificate')
            
        if self.protocol:
            args.append('--protocol=' + self.protocol)
            
        if self.project:
            args.append('--project=' + self.project)
            
        if self.module.check_mode:
             self.module.exit_json(changed=True, msg="Remote would be added")
             
        rc, out, err = self.run_incus(args, check_rc=False)
        if rc != 0:
             self.module.fail_json(msg="Failed to add remote: " + err, stdout=out, stderr=err)
             
        self.module.exit_json(changed=True, msg="Remote added")

    def delete(self):
        if self.module.check_mode:
             self.module.exit_json(changed=True, msg="Remote would be removed")
             
        rc, out, err = self.run_incus(['remote', 'remove', self.name], check_rc=False)
        if rc != 0:
             self.module.fail_json(msg="Failed to remove remote: " + err, stdout=out, stderr=err)
             
        self.module.exit_json(changed=True, msg="Remote removed")

    def update(self, current):
        # Remotes are mostly static once added.
        # We can update URL or Project.
        # `incus remote set-url <name> <url>`
        # `incus remote rename` (not handled here via update, but rename_from potentially)
        
        changed = False
        
        # Check URL
        # current is dict: {'addr': '...', 'public': False, ...}
        if self.url and current.get('addr') != self.url:
             if self.module.check_mode:
                 self.module.exit_json(changed=True, msg="Remote URL would be updated")
             
             rc, out, err = self.run_incus(['remote', 'set-url', self.name, self.url], check_rc=False)
             if rc != 0:
                 self.module.fail_json(msg="Failed to set remote URL: " + err, stdout=out, stderr=err)
             changed = True

        if not changed:
             self.module.exit_json(changed=False, msg="Remote matches configuration")
        else:
             self.module.exit_json(changed=True, msg="Remote updated")

    def run(self):
        current = self.get_remote_info()
        
        if self.state == 'present':
            if not current:
                self.create()
            else:
                self.update(current)
                
        elif self.state == 'absent':
             if current:
                 self.delete()
             else:
                 self.module.exit_json(changed=False, msg="Remote not found")

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            url=dict(type='str', required=False),
            protocol=dict(type='str', default='incus', required=False),
            token=dict(type='str', required=False, no_log=True),
            password=dict(type='str', required=False, no_log=True),
            accept_certificate=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            project=dict(type='str', required=False),
        ),
        supports_check_mode=True,
    )

    manager = IncusRemote(module)
    manager.run()

if __name__ == '__main__':
    main()
