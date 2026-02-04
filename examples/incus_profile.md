# incus_profile

Manage Incus configuration profiles.

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `name` | Yes | - | Name of the profile. |
| `description` | No | - | Profile description. |
| `config` | No | - | Dictionary of instance configuration options (e.g. `limits.cpu`). |
| `devices` | No | - | Dictionary of devices (e.g. root disk, nic). |
| `state` | No | `present` | `present` or `absent`. |
| `remote` | No | `local` | Remote Incus server. |
| `project` | No | `default` | Project name. |

## Examples

### Create Web Profile
```yaml
- name: Create web server profile
  crystian.incus.incus_profile:
    name: web-profile
    description: "Standard web server config"
    config:
      limits.cpu: "2"
      limits.memory: "2GB"
    devices:
      eth0:
        name: eth0
        type: nic
        network: incusbr0
      root:
        path: /
        pool: default
        type: disk
```

### Delete Profile
```yaml
- name: Delete profile
  crystian.incus.incus_profile:
    name: web-profile
    state: absent
```
