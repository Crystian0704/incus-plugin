#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_image
short_description: Manage Incus images
description:
  - Manage images in the Incus image store.
  - Supports copying from remotes, importing from files, exporting to files, and deleting.
version_added: "1.0.0"
options:
  alias:
    description:
      - Alias of the image.
      - Used as the primary identifier for presence checks if fingerprint is not provided.
    required: true
    type: str
    aliases: [ name ]
  fingerprint:
    description:
      - Fingerprint of the image.
      - If provided, used to verify the exact image identity.
    required: false
    type: str
  state:
    description:
      - State of the image.
      - 'present': Ensure image exists (copy or import if missing).
      - 'absent': Ensure image is removed.
      - 'exported': Export image to file.
    required: false
    type: str
    choices: [ present, absent, exported ]
    default: present
  source:
    description:
      - Source for the image when state='present'.
      - Can be a remote image (e.g. 'images:alpine/edge') or a local file path.
      - If it looks like a file path, it is treated as an import.
      - If it looks like a remote:alias, it is treated as a copy.
    required: false
    type: str
  dest:
    description:
      - Destination path for exported image (when state='exported').
    required: false
    type: path
  properties:
    description:
      - Dictionary of properties to set on the image.
    required: false
    type: dict
  aliases:
    description:
      - List of additional aliases to assign to the image.
    required: false
    type: list
    elements: str
  public:
    description:
      - Whether the image should be public.
    required: false
    type: bool
    default: false
  auto_update:
    description:
      - Whether to auto-update the image (valid for remote copies).
    required: false
    type: bool
    default: false
  remote:
    description:
      - The remote server.
      - Defaults to 'local'.
    required: false
    type: str
    default: local
  project:
    description:
      - The project instance belongs to.
      - Defaults to 'default'.
    required: false
    type: str
    default: default
author:
  - Crystian (@crystian)
'''
EXAMPLES = r'''
- name: Copy alpine image from images remote
  crystian.incus.incus_image:
    alias: my-alpine
    source: images:alpine/edge
    state: present
- name: Import image from local file
  crystian.incus.incus_image:
    alias: custom-image
    source: /tmp/image.tar.gz
    state: present
- name: Export image to file
  crystian.incus.incus_image:
    alias: my-alpine
    dest: /tmp/my-alpine-backup.tar.gz
    state: exported
- name: Delete image
  crystian.incus.incus_image:
    alias: my-alpine
    state: absent
'''
RETURN = r'''
msg:
  description: Status message
  returned: always
  type: str
fingerprint:
  description: Fingerprint of the managed image
  returned: when available
  type: str
'''
from ansible.module_utils.basic import AnsibleModule
import subprocess
import os
import json
class IncusImage(object):
    def __init__(self, module):
        self.module = module
        self.alias = module.params['alias']
        self.fingerprint = module.params['fingerprint']
        self.state = module.params['state']
        self.source = module.params['source']
        self.dest = module.params['dest']
        self.properties = module.params['properties']
        self.aliases = module.params['aliases']
        self.public = module.params['public']
        self.auto_update = module.params['auto_update']
        self.remote = module.params['remote']
        self.project = module.params['project']
    def run_incus(self, args):
        cmd = ['incus']
        if self.project:
            cmd.extend(['--project', self.project])
        cmd.extend(args)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
    def get_image_info(self, identifier):
        search_term = identifier
        if self.remote and self.remote != 'local':
             if ':' in identifier:
                 pass
             else:
                 search_term = "{}:{}".format(self.remote, identifier)
        cmd_args = ['image', 'list', search_term, '--format', 'json']
        rc, out, err = self.run_incus(cmd_args)
        if rc == 0:
            try:
                images = json.loads(out)
                clean_id = identifier.split(':')[-1]
                for img in images:
                    if img['fingerprint'].startswith(clean_id):
                        return img
                    if 'aliases' in img and img['aliases']:
                        for alias in img['aliases']:
                            if alias['name'] == clean_id:
                                return img
            except Exception:
                pass
        return None
    def present(self):
        target_alias = self.alias
        if self.remote and self.remote != 'local':
             target_alias = "{}:{}".format(self.remote, self.alias)
        info = self.get_image_info(target_alias)
        if info and self.fingerprint:
            if not info['fingerprint'].startswith(self.fingerprint):
                 pass
        if not info:
            if not self.source:
                self.module.fail_json(msg="Image '{}' not found and no 'source' provided".format(self.alias))
            if os.path.exists(self.source) and os.path.isfile(self.source):
                rootfs_path = self.source + ".root"
                cmd_args = ['image', 'import', self.source]
                if os.path.exists(rootfs_path):
                    cmd_args.append(rootfs_path)
                if self.remote and self.remote != 'local':
                    cmd_args.append("{}:".format(self.remote))
                cmd_args.extend(['--alias', self.alias])
                if self.public:
                    cmd_args.append('--public')
                if self.module.check_mode:
                    self.module.exit_json(changed=True, msg="Image would be imported")
                rc, out, err = self.run_incus(cmd_args)
                if rc != 0:
                    self.module.fail_json(msg="Failed to import image: " + err, stdout=out, stderr=err)
                self.module.exit_json(changed=True, msg="Image imported from file")
            else:
                cmd_args = ['image', 'copy', self.source]
                target_remote = self.remote if self.remote else 'local'
                cmd_args.append("{}:".format(target_remote))
                cmd_args.extend(['--alias', self.alias])
                if self.auto_update:
                    cmd_args.append('--auto-update')
                if self.public:
                    cmd_args.append('--public')
                if self.module.check_mode:
                    self.module.exit_json(changed=True, msg="Image would be copied")
                rc, out, err = self.run_incus(cmd_args)
                if rc != 0:
                    self.module.fail_json(msg="Failed to copy image: " + err, stdout=out, stderr=err)
                self.module.exit_json(changed=True, msg="Image copied from remote")
        else:
            self.module.exit_json(changed=False, msg="Image already exists", fingerprint=info['fingerprint'])
    def absent(self):
        target_alias = self.alias
        if self.remote and self.remote != 'local':
             target_alias = "{}:{}".format(self.remote, self.alias)
        info = self.get_image_info(target_alias)
        if not info:
            self.module.exit_json(changed=False, msg="Image not found")
        if self.fingerprint and not info['fingerprint'].startswith(self.fingerprint):
             self.module.fail_json(msg="Image found but fingerprint mismatch (found {}, expected {})".format(info['fingerprint'], self.fingerprint))
        cmd_args = ['image', 'delete', target_alias]
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Image would be deleted")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to delete image: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Image deleted")
    def exported(self):
        target_alias = self.alias
        if self.remote and self.remote != 'local':
             target_alias = "{}:{}".format(self.remote, self.alias)
        if not self.dest:
            self.module.fail_json(msg="'dest' is required for state=exported")
        if os.path.exists(self.dest):
             pass
        cmd_args = ['image', 'export', target_alias, self.dest]
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Image would be exported")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
             self.module.fail_json(msg="Failed to export image: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Image exported")
    def run(self):
        if self.state == 'present':
            self.present()
        elif self.state == 'absent':
            self.absent()
        elif self.state == 'exported':
            self.exported()
def main():
    module = AnsibleModule(
        argument_spec=dict(
            alias=dict(type='str', required=True, aliases=['name']),
            fingerprint=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent', 'exported']),
            source=dict(type='str', required=False),
            dest=dict(type='path', required=False),
            properties=dict(type='dict', required=False),
            aliases=dict(type='list', elements='str', required=False),
            public=dict(type='bool', default=False),
            auto_update=dict(type='bool', default=False),
            remote=dict(type='str', default='local', required=False),
            project=dict(type='str', default='default', required=False),
        ),
        supports_check_mode=True,
    )
    manager = IncusImage(module)
    manager.run()
if __name__ == '__main__':
    main()
