# incus_storage_volume

Manage Incus custom storage volumes

Create, update, delete, snapshot, backup, and copy/move Incus custom storage volumes.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `pool` | True |  |  | Name of the storage pool. |
| `name` | False |  |  | Name of the storage volume. If importing, this is the name of the new volume. |
| `type` | False | filesystem | ['filesystem', 'block'] | Type of the volume (filesystem or block). Default is filesystem. |
| `config` | False |  |  | Dictionary of configuration options for the volume. Can be used to set size, snapshots.schedule, etc. |
| `description` | False |  |  | Description of the volume. |
| `state` | False | present | ['present', 'absent', 'restored', 'exported', 'imported', 'copied'] | State of the volume. {'present': 'Ensure volume (and optional snapshot) exists.'} {'absent': 'Ensure volume (or snapshot) is deleted.'} {'restored': 'Restore volume from snapshot.'} {'exported': 'Export volume to file.'} {'imported': 'Import volume from file.'} {'copied': 'Copy/Move volume.'} |
| `content_type` | False |  |  | Content type (iso, etc). |
| `snapshot` | False |  |  | Name of the snapshot (for snapshot management). If provided with state=present, creates snapshot. If provided with state=absent, deletes snapshot. If provided with state=restored, restores from this snapshot. |
| `export_to` | False |  |  | Path to export the volume to (file path). Used with state=exported. |
| `import_from` | False |  |  | Path to import the volume from (file path). Used with state=imported. |
| `target_pool` | False |  |  | Target storage pool for copy/move operations. |
| `target_volume` | False |  |  | Target volume name for copy/move operations. |
| `move` | False | False |  | If true, move the volume instead of copying. Used with state=copied. |
| `target` | False |  |  | Cluster member to target for creation. |
| `attach_to` | False |  |  | Instance name to attach the volume to. |
| `attach_path` | False |  |  | Mount path within the instance (for type=filesystem). |
| `attach_device` | False |  |  | Device name to use when attaching. Defaults to volume name. |
| `remote` | False | local |  | The remote server. Defaults to 'local'. |
| `project` | False | default |  | The project context. Defaults to 'default'. |

## Examples

```yaml
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
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
```
