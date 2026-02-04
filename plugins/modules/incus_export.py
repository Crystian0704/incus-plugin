#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_export
short_description: Export Incus instances
description:
  - Export Incus instances to backup files.
version_added: "1.0.0"
options:
  instance:
    description:
      - Name of the instance to export.
    required: true
    type: str
    aliases: [ name ]
  path:
    description:
      - Destination path for the backup file.
      - If it is a directory, the file will be named <instance>.tar.gz (or similar) inside it.
    required: true
    type: path
    aliases: [ dest ]
  compression:
    description:
      - Compression algorithm (e.g. gzip, bzip2, none).
    required: false
    type: str
  optimized:
    description:
      - Use optimized storage format (driver specific).
    required: false
    type: bool
    default: false
  instance_only:
    description:
      - Export only the instance volume without snapshots.
    required: false
    type: bool
    default: false
  force:
    description:
      - Overwrite destination file if it exists.
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
      - The project the instance belongs to.
      - Defaults to 'default'.
    required: false
    type: str
    default: default
author:
  - Crystian (@crystian)
'''
EXAMPLES = r'''
- name: Export instance to file
  crystian.incus.incus_export:
    instance: my-container
    path: /backups/my-container.tar.gz
- name: Export optimized backup
  crystian.incus.incus_export:
    instance: my-container
    path: /backups/my-container.bin
    optimized: true
    force: true
'''
RETURN = r'''
msg:
  description: Status message
  returned: always
  type: str
file:
  description: Path to the exported file
  returned: always
  type: str
'''
from ansible.module_utils.basic import AnsibleModule
import subprocess
import os
class IncusExport(object):
    def __init__(self, module):
        self.module = module
        self.instance = module.params['instance']
        self.path = module.params['path']
        self.compression = module.params['compression']
        self.optimized = module.params['optimized']
        self.instance_only = module.params['instance_only']
        self.force = module.params['force']
        self.remote = module.params['remote']
        self.project = module.params['project']
        self.target = self.instance
        if self.remote and self.remote != 'local':
            self.target = "{}:{}".format(self.remote, self.instance)
    def run_incus(self, args):
        cmd = ['incus']
        if self.project:
            cmd.extend(['--project', self.project])
        cmd.extend(args)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
    def run(self):
        dest_path = self.path
        if os.path.isdir(dest_path):
             pass
        if os.path.exists(dest_path) and not os.path.isdir(dest_path):
            if not self.force:
                self.module.exit_json(changed=False, msg="File '{}' already exists".format(dest_path), file=dest_path)
            else:
                if not self.module.check_mode:
                    try:
                        os.remove(dest_path)
                    except OSError as e:
                        self.module.fail_json(msg="Failed to remove existing file: " + str(e))
        cmd_args = ['export', self.target, dest_path]
        if self.compression:
            cmd_args.extend(['--compression', self.compression])
        if self.optimized:
            cmd_args.append('--optimized-storage')
        if self.instance_only:
            cmd_args.append('--instance-only')
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Export would be performed")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to export instance: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Export successful", file=dest_path)
def main():
    module = AnsibleModule(
        argument_spec=dict(
            instance=dict(type='str', required=True, aliases=['name']),
            path=dict(type='path', required=True, aliases=['dest']),
            compression=dict(type='str', required=False),
            optimized=dict(type='bool', default=False),
            instance_only=dict(type='bool', default=False),
            force=dict(type='bool', default=False),
            remote=dict(type='str', default='local', required=False),
            project=dict(type='str', default='default', required=False),
        ),
        supports_check_mode=True,
    )
    manager = IncusExport(module)
    manager.run()
if __name__ == '__main__':
    main()
