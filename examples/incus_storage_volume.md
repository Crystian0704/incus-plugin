# Incus Storage Volume Module

The `incus_storage_volume` module allows you to manage Incus custom storage volumes.

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `pool` | Yes | - | Storage pool name. |
| `name` | Yes | - | Volume name. |
| `type` | No | `filesystem` | `filesystem` or `block`. |
| `config` | No | - | Volume configuration (e.g. `size`). |
| `description` | No | - | Volume description. |
| `state` | No | `present` | `present`, `absent`, `restored`, `exported`, `imported`, `copied`. |
| `snapshot` | No | - | Snapshot name (create/delete/restore). |
| `export_to` | No | - | Path to export file. |
| `import_from` | No | - | Path to import file. |
| `target_pool` | No | - | Target pool for copy/move. |
| `target_volume` | No | - | Target volume name for copy/move. |
| `move` | No | `false` | Move instead of copy. |

| `target` | No | - | Cluster member target. |
| `attach_to` | No | - | Instance to attach to. |
| `attach_path` | No | - | Mount path (filesystem). |
| `attach_device` | No | - | Device name. |

## Examples

### Import ISO
```yaml
- name: Import ISO
  crystian.incus.incus_storage_volume:
    pool: default
    name: my-iso
    import_from: /path/to/image.iso
    content_type: iso
    state: imported
```

### Create and Attach
```yaml
- name: Create data volume
  crystian.incus.incus_storage_volume:
    pool: default
    name: data-vol
    config:
      size: 10GiB
    attach_to: "my-instance"
    attach_path: "/mnt/data"
```

### Create Custom Volume
```yaml
- name: Create data volume
  crystian.incus.incus_storage_volume:
    pool: default
    name: data-vol
    config:
      size: 10GiB
      "snapshots.schedule": "@daily"
```

### Snapshot Operations
```yaml
- name: Create snapshot
  crystian.incus.incus_storage_volume:
    pool: default
    name: data-vol
    snapshot: snap0
    state: present

- name: Restore snapshot
  crystian.incus.incus_storage_volume:
    pool: default
    name: data-vol
    snapshot: snap0
    state: restored
```

### Export/Import
```yaml
- name: Export volume
  crystian.incus.incus_storage_volume:
    pool: default
    name: data-vol
    state: exported
    export_to: /tmp/data-vol.tar.gz

- name: Import volume
  crystian.incus.incus_storage_volume:
    pool: default
    import_from: /tmp/data-vol.tar.gz
    name: data-vol-restored
    state: imported
```

### Copy/Move
```yaml
- name: Copy volume
  crystian.incus.incus_storage_volume:
    pool: default
    name: data-vol
    state: copied
    target_pool: backup-pool
    target_volume: data-vol-copy
```

### Create Block Volume
```yaml
- name: Create block volume
  crystian.incus.incus_storage_volume:
    pool: default
    name: block-vol
    type: block
    config:
      size: 5GiB
```
