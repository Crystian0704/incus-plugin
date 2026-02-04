#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_snapshot
short_description: Manage Incus instance snapshots
description:
  - Create, delete, restore, or rename snapshots of Incus instances.
version_added: "1.0.0"
options:
  instance:
    description:
      - Name of the instance.
    required: true
    type: str
    aliases: [ name ]
  snapshot_name:
    description:
      - Name of the snapshot.
      - Required for most operations except some list scenarios (though not implemented here).
    required: true
    type: str
    aliases: [ snapshot ]
  state:
    description:
      - State of the snapshot.
      - 'present': Create a snapshot.
      - 'absent': Delete a snapshot.
      - 'restored': Restore the instance from this snapshot.
      - 'renamed': Rename the snapshot (requires 'new_name').
    required: false
    type: str
    choices: [ present, absent, restored, renamed ]
    default: present
  new_name:
    description:
      - New name for the snapshot (used with state='renamed').
    required: false
    type: str
  expires:
    description:
      - Expiry date for the snapshot (e.g. '30d').
      - Used only when creating (state='present').
    required: false
    type: str
  reuse:
    description:
      - Whether to overwrite an existing snapshot with the same name.
      - Used only when state='present'.
    required: false
    type: bool
    default: false
  stateful:
    description:
      - Whether to include running state in the snapshot (for VMs) or restore state.
      - Used with state='present' or state='restored'.
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
- name: Create a snapshot
  crystian.incus.incus_snapshot:
    instance: my-container
    snapshot_name: snap0
    state: present
- name: Create a stateful snapshot (VM only)
  crystian.incus.incus_snapshot:
    instance: my-vm
    snapshot_name: state-snap
    stateful: true
    state: present
- name: Restore a snapshot
  crystian.incus.incus_snapshot:
    instance: my-container
    snapshot_name: snap0
    state: restored
- name: Rename a snapshot
  crystian.incus.incus_snapshot:
    instance: my-container
    snapshot_name: snap0
    new_name: snap-initial
    state: renamed
- name: Delete a snapshot
  crystian.incus.incus_snapshot:
    instance: my-container
    snapshot_name: snap0
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
class IncusSnapshot(object):
    def __init__(self, module):
        self.module = module
        self.instance = module.params['instance']
        self.snapshot_name = module.params['snapshot_name']
        self.state = module.params['state']
        self.new_name = module.params['new_name']
        self.expires = module.params['expires']
        self.reuse = module.params['reuse']
        self.stateful = module.params['stateful']
        self.remote = module.params['remote']
        self.project = module.params['project']
        self.cron = module.params['cron']
        self.cron_stopped = module.params['cron_stopped']
        self.pattern = module.params['pattern']
        self.expiry = module.params['expiry']
        self.target_instance = self.instance
        if self.remote and self.remote != 'local':
            self.target_instance = "{}:{}".format(self.remote, self.instance)
        if self.snapshot_name:
            self.target_snapshot = "{}/{}".format(self.target_instance, self.snapshot_name)
        else:
            self.target_snapshot = None
    def run_incus(self, args):
        cmd = ['incus']
        if self.project:
            cmd.extend(['--project', self.project])
        cmd.extend(args)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')
    def exists(self):
        rc, out, err = self.run_incus(['snapshot', 'show', self.target_instance, self.snapshot_name])
        return rc == 0
    def create(self):
        if self.exists():
            if self.reuse:
                pass 
            else:
                self.module.exit_json(changed=False, msg="Snapshot '{}' already exists".format(self.snapshot_name))
        cmd_args = ['snapshot', 'create', self.target_instance, self.snapshot_name]
        if self.reuse:
            cmd_args.append('--reuse')
        if self.expires:
             pass
        if self.stateful:
            cmd_args.append('--stateful')
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Snapshot would be created")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to create snapshot: " + err, stdout=out, stderr=err)
        if self.expires and not self.module.check_mode:
             self.run_incus(['config', 'set', self.target_snapshot, 'snapshots.expiry={}'.format(self.expires)])
        self.module.exit_json(changed=True, msg="Snapshot created")
    def delete(self):
        if not self.exists():
            self.module.exit_json(changed=False, msg="Snapshot not found")
        cmd_args = ['snapshot', 'delete', self.target_instance, self.snapshot_name]
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Snapshot would be deleted")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to delete snapshot: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Snapshot deleted")
    def restore(self):
        if not self.exists():
             self.module.fail_json(msg="Snapshot '{}' does not exist".format(self.snapshot_name))
        cmd_args = ['snapshot', 'restore', self.target_instance, self.snapshot_name]
        if self.stateful:
            cmd_args.append('--stateful')
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Instance would be restored from snapshot")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to restore snapshot: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Instance restored")
    def rename(self):
        if not self.exists():
            self.module.fail_json(msg="Snapshot '{}' does not exist".format(self.snapshot_name))
        if not self.new_name:
            self.module.fail_json(msg="'new_name' is required for state=renamed")
        new_target = "{}/{}".format(self.target_instance, self.new_name)
        rc, _, _ = self.run_incus(['info', new_target])
        if rc == 0:
             self.module.exit_json(changed=False, msg="Snapshot '{}' already exists (as new name)".format(self.new_name))
        cmd_args = ['snapshot', 'rename', self.target_instance, self.snapshot_name, self.new_name]
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Snapshot would be renamed")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to rename snapshot: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Snapshot renamed")
    def configure(self):
        configs = {}
        if self.cron is not None:
            configs['snapshots.schedule'] = self.cron
        if self.cron_stopped is not None:
            configs['snapshots.schedule.stopped'] = str(self.cron_stopped).lower()
        if self.pattern is not None:
            configs['snapshots.pattern'] = self.pattern
        if self.expiry is not None:
            configs['snapshots.expiry'] = self.expiry
        if not configs:
            return
        rc, out, err = self.run_incus(['config', 'show', self.target_instance])
        current_config = {}
        if rc == 0:
            lines = out.splitlines()
            pass
        cmd_args = ['config', 'set', self.target_instance]
        for k, v in configs.items():
            cmd_args.append("{}={}".format(k, v))
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Instance snapshot configuration would be updated")
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to update configuration: " + err, stdout=out, stderr=err)
        self.module.exit_json(changed=True, msg="Instance snapshot configuration updated")
    def run(self):
        if self.state == 'present':
            if self.snapshot_name:
                self.create()
            else:
                self.configure()
        elif self.state == 'absent':
            self.delete()
        elif self.state == 'restored':
            self.restore()
        elif self.state == 'renamed':
            self.rename()
def main():
    module = AnsibleModule(
        argument_spec=dict(
            instance=dict(type='str', required=True, aliases=['name']),
            snapshot_name=dict(type='str', required=False, aliases=['snapshot']),
            state=dict(type='str', default='present', choices=['present', 'absent', 'restored', 'renamed']),
            new_name=dict(type='str', required=False),
            expires=dict(type='str', required=False),
            reuse=dict(type='bool', default=False),
            stateful=dict(type='bool', default=False),
            remote=dict(type='str', default='local', required=False),
            project=dict(type='str', default='default', required=False),
            cron=dict(type='str', required=False),
            cron_stopped=dict(type='bool', required=False),
            pattern=dict(type='str', required=False),
            expiry=dict(type='str', required=False),
        ),
        required_if=[
            ('state', 'absent', ['snapshot_name']),
            ('state', 'restored', ['snapshot_name']),
            ('state', 'renamed', ['snapshot_name', 'new_name']),
        ],
        supports_check_mode=True,
    )
    manager = IncusSnapshot(module)
    manager.run()
if __name__ == '__main__':
    main()
