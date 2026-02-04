# incus_storage

Manage Incus storage pools

Create, update, and delete Incus storage pools.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `name` | True |  |  | Name of the storage pool. |
| `driver` | False |  |  | Storage driver to use (e.g. dir, zfs, btrfs, lvm). Required when creating a new pool. |
| `config` | False |  |  | Dictionary of configuration options for the storage pool. |
| `description` | False |  |  | Description of the storage pool. |
| `state` | False | present | ['present', 'absent'] | State of the storage pool. {'present': 'Ensure pool exists and matches configuration.'} {'absent': 'Ensure pool is deleted.'} |
| `remote` | False | local |  | The remote server. Defaults to 'local'. |
| `project` | False | default |  | The project context. Defaults to 'default'. |

## Examples

```yaml
- name: Create a dir storage pool
  crystian.incus.incus_storage:
    name: my-pool
    driver: dir
    config:
      source: /var/lib/incus/storage-pools/my-pool
    description: "My custom dir pool"
- name: Create a ZFS pool (loop backed)
  crystian.incus.incus_storage:
    name: zfs-pool
    driver: zfs
    config:
      size: 10GiB
- name: Delete a pool
  crystian.incus.incus_storage:
    name: my-pool
    state: absent
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
pool:
  description: Pool configuration
  returned: when available
  type: dict
```
