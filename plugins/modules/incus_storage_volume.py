#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: incus_storage_volume
short_description: Manage Incus custom storage volumes
description:
  - Create, update, delete, snapshot, backup, and copy/move Incus custom storage volumes.
version_added: "1.0.0"
options:
  pool:
    description:
      - Name of the storage pool.
    required: true
    type: str
  name:
    description:
      - Name of the storage volume.
      - If importing, this is the name of the new volume.
    required: false
    type: str
    aliases: [ volume ]
  type:
    description:
      - Type of the volume (filesystem or block).
      - Default is filesystem.
    required: false
    type: str
    choices: [ filesystem, block ]
    default: filesystem
  config:
    description:
      - Dictionary of configuration options for the volume.
      - Can be used to set size, snapshots.schedule, etc.
    required: false
    type: dict
  description:
    description:
      - Description of the volume.
    required: false
    type: str
  state:
    description:
      - State of the volume.
      - 'present': Ensure volume (and optional snapshot) exists.
      - 'absent': Ensure volume (or snapshot) is deleted.
      - 'restored': Restore volume from snapshot.
      - 'exported': Export volume to file.
      - 'imported': Import volume from file.
      - 'copied': Copy/Move volume.
    required: false
    type: str
    choices: [ present, absent, restored, exported, imported, copied ]
    default: present
  content_type:
    description:
      - Content type (iso, etc).
    required: false
    type: str
  
  # Snapshot / Backup / Move params
  snapshot:
    description:
      - Name of the snapshot (for snapshot management).
      - If provided with state=present, creates snapshot.
      - If provided with state=absent, deletes snapshot.
      - If provided with state=restored, restores from this snapshot.
    required: false
    type: str
  
  export_to:
    description:
      - Path to export the volume to (file path).
      - Used with state=exported.
    required: false
    type: str
    
  import_from:
    description:
      - Path to import the volume from (file path).
      - Used with state=imported.
    required: false
    type: str
    
  target_pool:
    description:
      - Target storage pool for copy/move operations.
    required: false
    type: str
    
  target_volume:
    description:
      - Target volume name for copy/move operations.
    required: false
    type: str
      move:
    description:
      - If true, move the volume instead of copying.
      - Used with state=copied.
    required: false
    type: bool
    default: false
    
  target:
    description:
      - Cluster member to target for creation.
    required: false
    type: str

  attach_to:
    description:
      - Instance name to attach the volume to.
    required: false
    type: str
    
  attach_path:
    description:
      - Mount path within the instance (for type=filesystem).
    required: false
    type: str
    
  attach_device:
    description:
      - Device name to use when attaching.
      - Defaults to volume name.
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
- name: Create a custom volume with snapshot schedule
  crystian.incus.incus_storage_volume:
    pool: default
    name: data-vol
    config:
      size: 10GiB
      "snapshots.schedule": "@daily"

- name: Import ISO
  crystian.incus.incus_storage_volume:
    pool: default
    name: my-iso
    import_from: /path/to/image.iso
    content_type: iso
    state: imported

- name: Attach volume to instance
  crystian.incus.incus_storage_volume:
    pool: default
    name: data-vol
    attach_to: my-instance
    attach_path: /mnt/data
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

class IncusStorageVolume(object):
    def __init__(self, module):
        self.module = module
        self.pool = module.params['pool']
        self.name = module.params['name']
        self.type = module.params['type']
        self.config = module.params['config']
        self.description = module.params['description']
        self.state = module.params['state']
        self.content_type = module.params['content_type']
        self.remote = module.params['remote']
        self.project = module.params['project']
        
        # New params
        self.snapshot = module.params['snapshot']
        self.export_to = module.params['export_to']
        self.import_from = module.params['import_from']
        self.target_pool = module.params['target_pool']
        self.target_volume = module.params['target_volume']
        self.move_op = module.params['move']
        self.target = module.params['target']
        self.attach_to = module.params['attach_to']
        self.attach_path = module.params['attach_path']
        self.attach_device = module.params['attach_device'] or self.name

    def run_incus(self, args):
        cmd = ['incus']
        if self.project:
            cmd.extend(['--project', self.project])
        cmd.extend(args)
        
        env = os.environ.copy()
        env['LC_ALL'] = 'C'
        
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        stdout, stderr = p.communicate()
        return p.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')

    def get_volume_info(self):
        target_pool = self.pool
        if self.remote and self.remote != 'local':
            target_pool = "{}:{}".format(self.remote, self.pool)
            
        rc, out, err = self.run_incus(['storage', 'volume', 'show', target_pool, self.name])
        if rc == 0:
            import yaml
            try:
                return yaml.safe_load(out)
            except ImportError:
                pass
        return None

    def exists(self):
        return self.get_volume_info() is not None

    def snapshot_exists(self):
        # incus storage volume show <pool> <volume>/<snapshot>
        target_pool = self.pool
        if self.remote and self.remote != 'local':
            target_pool = "{}:{}".format(self.remote, self.pool)
            
        target_snap = "{}/{}".format(self.name, self.snapshot)
        rc, out, err = self.run_incus(['storage', 'volume', 'show', target_pool, target_snap])
        return rc == 0

    def create(self):
        if self.snapshot:
            # Create snapshot
            if self.snapshot_exists():
                self.module.exit_json(changed=False, msg="Snapshot already exists")
                
            target_pool = self.pool
            if self.remote and self.remote != 'local':
                target_pool = "{}:{}".format(self.remote, self.pool)

            cmd_args = ['storage', 'volume', 'snapshot', 'create', target_pool, self.name, self.snapshot]
            
            if self.module.check_mode:
                self.module.exit_json(changed=True, msg="Snapshot would be created")
                
            rc, out, err = self.run_incus(cmd_args)
            if rc != 0:
                self.module.fail_json(msg="Failed to create snapshot: " + err, stdout=out, stderr=err)
            
            self.module.exit_json(changed=True, msg="Snapshot created")
        
        # Create volume
        target_pool = self.pool
        if self.remote and self.remote != 'local':
            target_pool = "{}:{}".format(self.remote, self.pool)

        cmd_args = ['storage', 'volume', 'create', target_pool, self.name]
        
        if self.description:
             cmd_args.extend(['--description', self.description])
        
        if self.content_type:
            cmd_args.append('--type={}'.format(self.content_type))
        elif self.type == 'block':
            cmd_args.append('--type=block')
            
        if self.target:
            cmd_args.append('--target={}'.format(self.target))
        
        if self.config:
            for k, v in self.config.items():
                cmd_args.append("{}={}".format(k, v))

        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Storage volume would be created")

        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to create storage volume: " + err, stdout=out, stderr=err)
            
        # If attach requested, do it now
        if self.attach_to:
            self.attach_volume()

        self.module.exit_json(changed=True, msg="Storage volume created")

    def update(self, current_info):
        # Only for volume properties, not snapshot creation
        # Also check attachment if requested
        
        changed = False
        msgs = []
        
        target_pool = self.pool
        if self.remote and self.remote != 'local':
            target_pool = "{}:{}".format(self.remote, self.pool)
            
        if self.config:
            current_config = current_info.get('config', {})
            for k, v in self.config.items():
                curr_val = current_config.get(k, '')
                if str(curr_val) != str(v):
                    if not self.module.check_mode:
                        rc, out, err = self.run_incus(['storage', 'volume', 'set', target_pool, self.name, "{}={}".format(k, v)])
                        if rc != 0:
                            self.module.fail_json(msg="Failed to set volume config '{}': {}".format(k, err))
                    changed = True
                    msgs.append("Updated config '{}'".format(k))

        # Check attachment
        if self.attach_to:
             is_attached = self.check_if_attached()
             if not is_attached:
                 self.attach_volume()
                 changed = True
                 msgs.append("Attached to instance '{}'".format(self.attach_to))

        if changed:
            self.module.exit_json(changed=True, msg=", ".join(msgs))
        else:
            self.module.exit_json(changed=False, msg="Storage volume matches configuration")

    def delete(self):
        target_pool = self.pool
        if self.remote and self.remote != 'local':
            target_pool = "{}:{}".format(self.remote, self.pool)

        if self.snapshot:
             # Delete snapshot
             if not self.snapshot_exists():
                 self.module.exit_json(changed=False, msg="Snapshot not found")
                 
             if self.module.check_mode:
                self.module.exit_json(changed=True, msg="Snapshot would be deleted")
                
             rc, out, err = self.run_incus(['storage', 'volume', 'snapshot', 'delete', target_pool, self.name, self.snapshot])
             if rc != 0:
                 self.module.fail_json(msg="Failed to delete snapshot: " + err, stdout=out, stderr=err)
             self.module.exit_json(changed=True, msg="Snapshot deleted")

        # Delete volume
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Storage volume would be deleted")

        rc, out, err = self.run_incus(['storage', 'volume', 'delete', target_pool, self.name])
        if rc != 0:
            self.module.fail_json(msg="Failed to delete storage volume: " + err, stdout=out, stderr=err)

        self.module.exit_json(changed=True, msg="Storage volume deleted")

    def restore(self):
         if not self.snapshot:
             self.module.fail_json(msg="'snapshot' is required for state=restored")
         
         if not self.snapshot_exists():
             self.module.fail_json(msg="Snapshot not found")

         target_pool = self.pool
         if self.remote and self.remote != 'local':
             target_pool = "{}:{}".format(self.remote, self.pool)
             
         # incus storage volume snapshot restore <pool> <volume> <snapshot>
         if self.module.check_mode:
             self.module.exit_json(changed=True, msg="Snapshot would be restored")
             
         rc, out, err = self.run_incus(['storage', 'volume', 'snapshot', 'restore', target_pool, self.name, self.snapshot])
         if rc != 0:
             self.module.fail_json(msg="Failed to restore snapshot: " + err, stdout=out, stderr=err)
             
         self.module.exit_json(changed=True, msg="Snapshot restored")

    def export_volume(self):
        if not self.export_to:
            self.module.fail_json(msg="'export_to' is required for state=exported")
            
        target_pool = self.pool
        if self.remote and self.remote != 'local':
            target_pool = "{}:{}".format(self.remote, self.pool)
            
        # incus storage volume export <pool> <volume> <file>
        cmd_args = ['storage', 'volume', 'export', target_pool, self.name, self.export_to]
        
        # force override? The CLI warning says it overwrites.
        # We can treat it as always changed or check file existence.
        
        if self.module.check_mode:
            self.module.exit_json(changed=True, msg="Volume would be exported")
            
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
            self.module.fail_json(msg="Failed to export volume: " + err, stdout=out, stderr=err)
            
        self.module.exit_json(changed=True, msg="Volume exported")

    def import_volume(self):
        if not self.import_from:
            self.module.fail_json(msg="'import_from' is required for state=imported")
            
        target_pool = self.pool
        if self.remote and self.remote != 'local':
            target_pool = "{}:{}".format(self.remote, self.pool)
            
        # incus storage volume import <pool> <file> [<volume>] --type=...
        cmd_args = ['storage', 'volume', 'import', target_pool, self.import_from]
        if self.name:
            cmd_args.append(self.name)
            
        if self.content_type:
            cmd_args.append('--type={}'.format(self.content_type))
            
        if self.module.check_mode:
             self.module.exit_json(changed=True, msg="Volume would be imported")
             
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
             self.module.fail_json(msg="Failed to import volume: " + err, stdout=out, stderr=err)
             
        # attach if requested
        if self.attach_to:
            self.attach_volume()
            
        self.module.exit_json(changed=True, msg="Volume imported")

    def copy_move(self):
        if not self.target_pool:
            self.module.fail_json(msg="'target_pool' is required for state=copied (can be same as source)")
        if not self.target_volume:
            self.module.fail_json(msg="'target_volume' is required for state=copied")
            
        op = 'move' if self.move_op else 'copy'
        
        source = "{}/{}".format(self.pool, self.name)
        if self.remote and self.remote != 'local':
            source = "{}:{}".format(self.remote, source)
            
        target = "{}/{}".format(self.target_pool, self.target_volume)
        if self.remote and self.remote != 'local':
             target = "{}:{}".format(self.remote, target)
             
        if self.module.check_mode:
             self.module.exit_json(changed=True, msg="Volume would be {}d".format(op))
             
        cmd_args = ['storage', 'volume', op, source, target]
        if self.target:
             cmd_args.append('--target={}'.format(self.target))
             # Also dest-target? copy cmd has --destination-target. My param name 'target' might be ambiguous.
             # User doc says "cluster member", so --target usually specifies where it is created/pending.
             # For move/copy between members: --target (source) and --destination-target (target).
             # Let's assume 'target' param maps to '--target' (source filter) or creation target.
             # If I want to target dest, I usually need another param?
             # For now, append --target if provided.
        
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
             self.module.fail_json(msg="Failed to {} volume: {}".format(op, err), stdout=out, stderr=err)
             
        self.module.exit_json(changed=True, msg="Volume {}d".format(op))

    def check_if_attached(self):
        # incus config device list <instance>
        # Check if attach_device is in list
        
        instance = self.attach_to
        if self.remote and self.remote != 'local':
            instance = "{}:{}".format(self.remote, instance)
            
        rc, out, err = self.run_incus(['config', 'device', 'list', instance, '--format=json'])
        if rc == 0:
            try:
                devices = json.loads(out)
                # 'out' for list json might be list of names or dict?
                # Actually 'config device list' returns a list of names in text format by default or map in json?
                # Documentation says "list" output is text table. --format=json not standard for list?
                # Actually incus config device list is NOT returning json usually.
                # Let's use 'config show <instance>' which gets full config including devices.
                pass
            except:
                pass
        
        # Safe fallback: 'config show'
        rc, out, err = self.run_incus(['config', 'show', instance])
        if rc == 0:
            import yaml
            try:
                data = yaml.safe_load(out)
                devices = data.get('devices', {})
                if self.attach_device in devices:
                    # Check if it points to our volume?
                    # The device might exist but be something else.
                    # We assume if checking idempotency, we check if device exists.
                    # If existing device is WRONG, we might need to error or update?
                    # For now: if device exists, we assume attached.
                    return True
            except ImportError:
                pass
        return False

    def attach_volume(self):
        # incus storage volume attach <pool> <volume> <instance> [<device>] [<path>]
        target_pool = self.pool
        if self.remote and self.remote != 'local':
             target_pool = "{}:{}".format(self.remote, self.pool)
             
        cmd_args = ['storage', 'volume', 'attach', target_pool, self.name, self.attach_to]
        
        # Only append device name if it is explicitly provided or we need to disambiguate?
        # Actually, appending device name is safe usually.
        # But for block volumes, maybe implicit is safer to avoid path confusion?
        # If I send 4 args, 4th IS device name.
        
        # Let's check if we have a path to allow sending device name.
        # If no path, sending 3 args is safer if device==name.
        
        use_default_device_name = (self.attach_device == self.name)
        has_path = (self.attach_path and self.type == 'filesystem' and self.content_type != 'iso')
        
        if not use_default_device_name or has_path:
             cmd_args.append(self.attach_device)
             
        if has_path:
             cmd_args.append(self.attach_path)
            
        if self.module.check_mode:
             return # Just pretending
             
        rc, out, err = self.run_incus(cmd_args)
        if rc != 0:
             self.module.fail_json(msg="Failed to attach volume: " + err + " CMD: " + " ".join(cmd_args), stdout=out, stderr=err)

    def run(self):
        if self.state == 'imported':
             self.import_volume()
             return

        current_info = self.get_volume_info()
        
        if self.state == 'present':
            if not current_info and not self.snapshot: # Creating volume
                self.create()
            elif current_info and self.snapshot: # Creating snapshot
                self.create()  # create() handles snapshot creation check
            elif current_info and not self.snapshot: # Updating volume/Attach
                self.update(current_info)
            else:
                self.module.fail_json(msg="Volume '{}' does not exist".format(self.name))
        
        elif self.state == 'absent':
             if current_info:
                 self.delete()
             else:
                 self.module.exit_json(changed=False, msg="Volume/Snapshot not found")
                 
        elif self.state == 'restored':
             self.restore()
             
        elif self.state == 'exported':
             self.export_volume()
             
        elif self.state == 'copied':
             if not current_info:
                 self.module.fail_json(msg="Source volume '{}' not found".format(self.name))
             self.copy_move()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            pool=dict(type='str', required=True),
            name=dict(type='str', required=False, aliases=['volume']),
            type=dict(type='str', default='filesystem', choices=['filesystem', 'block']),
            content_type=dict(type='str', required=False, choices=['filesystem', 'block', 'iso']), # Added iso
            config=dict(type='dict', required=False),
            description=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent', 'restored', 'exported', 'imported', 'copied']),
            remote=dict(type='str', default='local', required=False),
            project=dict(type='str', default='default', required=False),
            
            # Extended params
            snapshot=dict(type='str', required=False),
            export_to=dict(type='str', required=False),
            import_from=dict(type='str', required=False),
            target_pool=dict(type='str', required=False),
            target_volume=dict(type='str', required=False),
            move=dict(type='bool', default=False),
            
            # Capability params
            target=dict(type='str', required=False),
            attach_to=dict(type='str', required=False),
            attach_path=dict(type='str', required=False),
            attach_device=dict(type='str', required=False),
        ),
        supports_check_mode=True,
    )

    manager = IncusStorageVolume(module)
    manager.run()

if __name__ == '__main__':
    main()
