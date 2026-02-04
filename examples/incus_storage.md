# Incus Storage Module

The `incus_storage` module allows you to manage Incus storage pools.

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `name` | Yes | - | Pool name. |
| `driver` | No | - | Storage driver (`dir`, `zfs`, etc). Required for create. |
| `config` | No | - | Pool configuration. |
| `description` | No | - | Pool description. |
| `state` | No | `present` | `present` or `absent`. |

## Examples

### Create Directory Pool
```yaml
- name: Create dir pool
  crystian.incus.incus_storage:
    name: pool-dir
    driver: dir
    config:
      source: /var/lib/incus/storage-pools/pool-dir
```

### Create Loop ZFS Pool
```yaml
- name: Create zfs pool
  crystian.incus.incus_storage:
    name: pool-zfs
    driver: zfs
    config:
      size: 5GiB
```
