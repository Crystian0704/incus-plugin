# incus_config

Manage Incus instance configuration and devices

Manage configuration options (e.g. limits.memory) and devices for Incus instances.
This module complements C(incus_instance) which is primarily for creation/state.
Useful for modifying running instances or managing complex device setups.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `name` | True |  |  | Name of the instance. |
| `remote` | False |  |  | Remote server to target (e.g., 'myremote'). |
| `state` | False | present | ['present', 'absent'] | ensuring 'present' will update config/devices to match provided values. ensuring 'absent' will remove the specified config keys or devices. |
| `config` | False |  |  | Dictionary of configuration options. If state=present, sets these values. If state=absent, removes these keys (values are ignored, can be list of keys or dict). |
| `devices` | False |  |  | Dictionary of devices to manage. Key is the device name. Value is a dictionary containing 'type' (required for adding) and options. If state=absent, removes these devices (values ignored, can be list of names or dict). |

## Examples

```yaml
- name: Set memory limit
  crystian.incus.incus_config:
    name: my-container
    config:
      limits.memory: 2GiB
- name: Add a network device
  crystian.incus.incus_config:
    name: my-container
    devices:
      eth1:
        type: nic
        nictype: bridged
        parent: incusbr0
- name: Update device MTU
  crystian.incus.incus_config:
    name: my-container
    devices:
      eth1:
        mtu: 1400
- name: Remove configuration
  crystian.incus.incus_config:
    name: my-container
    state: absent
    config:
      - limits.memory
- name: Remove device
  crystian.incus.incus_config:
    name: my-container
    state: absent
    devices:
      - eth1
```

## Return Values

```yaml
# Default return values
```
