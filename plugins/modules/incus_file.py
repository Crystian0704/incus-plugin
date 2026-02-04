#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_file
short_description: Manage files in Incus instances
description:
  - Manage files in Incus instances (push, pull, delete).
  - Designed to follow Ansible's `copy`, `fetch`, and `file` nomenclature.
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the instance.
    required: true
    type: str
    aliases: [ instance ]
  state:
    description:
      - State of the file.
      - 'pushed': Push a local file ('src') or content ('content') to the instance ('dest').
      - 'pulled': Pull a file from the instance ('src') to local destination ('dest').
      - 'absent': Delete a file from the instance ('dest').
    required: false
    type: str
    choices: [ pushed, pulled, absent ]
    default: pushed
  src:
    description:
      - Source path.
      - If state='pushed': Local path to the file to push.
      - If state='pulled': Remote path inside the instance.
    required: false
    type: path
  dest:
    description:
      - Destination path.
      - If state='pushed': Remote path inside the instance.
      - If state='pulled': Local destination path.
      - If state='absent': Remote path to delete.
    required: false
    type: path
    aliases: [ path ]
  content:
    description:
      - Content to push to the file (when state=pushed).
      - Mutually exclusive with 'src'.
    required: false
    type: str
  owner:
    description:
      - Owner name or ID for the pushed file.
      - If a name is provided, it is resolved inside the instance.
    required: false
    type: raw
  group:
    description:
      - Group name or ID for the pushed file.
      - If a name is provided, it is resolved inside the instance.
    required: false
    type: raw
  mode:
    description:
      - File permissions for the pushed file (e.g. '0644').
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
- name: Push a local file (copy style)
  crystian.incus.incus_file:
    name: my-container
    src: /tmp/local_file.txt
    dest: /root/remote_file.txt
    owner: root
    group: root
    mode: '0644'
    state: pushed
- name: Push content directly
  crystian.incus.incus_file:
    name: my-container
    content: "Hello from Ansible"
    dest: /root/hello.txt
    state: pushed
- name: Pull a file (fetch style)
  crystian.incus.incus_file:
    name: my-container
    src: /etc/hosts
    dest: /tmp/container_hosts
    state: pulled
- name: Delete a file (file style)
  crystian.incus.incus_file:
    name: my-container
    dest: /tmp/garbage.txt
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
import os
import tempfile
import shutil
class IncusFile(object):
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.state = module.params['state']
        self.src = module.params['src']
        self.dest = module.params['dest']
        self.content = module.params['content']
        self.owner = module.params['owner']
        self.group = module.params['group']
        self.mode = module.params['mode']
        self.remote = module.params['remote']
        self.project = module.params['project']
        self.target = self.name
        if self.remote and self.remote != 'local':
            self.target = "{}:{}".format(self.remote, self.name)
    def run_incus(self, args):
        cmd = ['incus']
        if self.project:
            cmd.extend(['--project', self.project])
        cmd.extend(args)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
    def resolve_id(self, name_or_id, id_type):
        """
        Resolve user/group name to ID inside the instance.
        id_type: 'u' for user, 'g' for group.
        """
        if name_or_id is None:
            return None
        try:
            return int(name_or_id)
        except ValueError:
            pass 
        cmd_args = ['exec', self.target, '--', 'id', '-{}'.format(id_type), str(name_or_id)]
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to resolve {} '{}': {}".format(
                'user' if id_type == 'u' else 'group', name_or_id, err))
        return int(out.strip())
    def push(self):
        source_path = self.src
        dest_path = self.dest
        temp_path = None
        if not dest_path:
             self.module.fail_json(msg="'dest' is required for state=pushed")
        if self.content is not None:
            if self.src:
                self.module.fail_json(msg="Parameters 'content' and 'src' are mutually exclusive")
            fd, temp_path = tempfile.mkstemp()
            with os.fdopen(fd, 'w') as f:
                f.write(self.content)
            source_path = temp_path
        elif not source_path:
            self.module.fail_json(msg="Either 'src' or 'content' is required for state=pushed")
        if not os.path.exists(source_path):
             self.module.fail_json(msg="Source file '{}' does not exist".format(source_path))
        cmd_args = ['file', 'push', source_path, "{}/{}".format(self.target, dest_path.lstrip('/'))]
        uid = self.resolve_id(self.owner, 'u')
        gid = self.resolve_id(self.group, 'g')
        if uid is not None:
            cmd_args.extend(['--uid', str(uid)])
        if gid is not None:
            cmd_args.extend(['--gid', str(gid)])
        if self.mode is not None:
            cmd_args.extend(['--mode', self.mode])
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="File would be pushed")
        rc, out, err = self.run_incus(cmd_args)
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if rc != 0:
            self.module.fail_json(msg="Failed to push file: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="File pushed successfully")
    def pull(self):
        remote_src = self.src
        local_dest = self.dest
        if not remote_src:
             self.module.fail_json(msg="'src' (remote path) is required for state=pulled")
        if not local_dest:
             self.module.fail_json(msg="'dest' (local path) is required for state=pulled")
        cmd_args = ['file', 'pull', "{}/{}".format(self.target, remote_src.lstrip('/')), local_dest]
        if self.module.check_mode:
             self.module.exit_json(changed=True, msg="File would be pulled")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to pull file: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="File pulled successfully")
    def absent(self):
        remote_dest = self.dest
        if not remote_dest:
             self.module.fail_json(msg="'dest' (remote path) is required for state=absent")
        cmd_args = ['file', 'delete', "{}/{}".format(self.target, remote_dest.lstrip('/'))]
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="File would be deleted")
        rc, out, err = self.run_incus(cmd_args)
        if rc == 0:
             self.module.exit_json(changed=True, msg="File deleted")
        else:
            if "not found" in err.lower() or "no such file" in err.lower():
                self.module.exit_json(changed=False, msg="File already absent")
            else:
                self.module.fail_json(msg="Failed to delete file: " + err, stdout=out, stderr=err)
    def run(self):
        if self.state == 'pushed':
            self.push()
        elif self.state == 'pulled':
            self.pull()
        elif self.state == 'absent':
            self.absent()
def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, aliases=['instance']),
            state=dict(type='str', default='pushed', choices=['pushed', 'pulled', 'absent']),
            src=dict(type='path', required=False),
            dest=dict(type='path', required=False, aliases=['path']),
            content=dict(type='str', required=False),
            owner=dict(type='raw', required=False),
            group=dict(type='raw', required=False),
            mode=dict(type='str', required=False),
            remote=dict(type='str', default='local', required=False),
            project=dict(type='str', default='default', required=False),
        ),
        supports_check_mode=True,
    )
    manager = IncusFile(module)
    manager.run()
if __name__ == '__main__':
    main()
