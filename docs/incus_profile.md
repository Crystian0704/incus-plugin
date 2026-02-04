# incus_profile

Manage Incus profiles

Create, update, and delete Incus configuration profiles.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `name` | True |  |  | Name of the profile. |
| `description` | False |  |  | Description of the profile. |
| `config` | False |  |  | Dictionary of configuration options (e.g., 'limits.cpu': '2'). |
| `devices` | False |  |  | Dictionary of devices. |
| `state` | False | present | ['present', 'absent'] | State of the profile. {'present': 'Ensure profile exists and matches config.'} {'absent': 'Ensure profile is deleted.'} |
| `rename_from` | False |  |  | If provided, and appropriate, rename an existing profile to 'name'. |
| `remote` | False | local |  | The remote server. Defaults to 'local'. |
| `project` | False | default |  | The project context. Defaults to 'default'. |

## Examples

```yaml
- name: Create a web server profile
  crystian.incus.incus_profile:
    name: web-profile
    description: "Profile for web servers"
    config:
      limits.cpu: "2"
      limits.memory: "4GiB"
    devices:
      eth0:
        name: eth0
        type: nic
        network: incusbr0
      root:
        path: /
        pool: default
        type: disk
- name: Delete a profile
  crystian.incus.incus_profile:
    name: web-profile
    state: absent
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
```
