# Ansible Collection - crystian.incus

Ansible Collection for managing Incus containers and virtual machines.

## Requirements

This collection requires the `incus` client to be installed on the Ansible control node (where you run the playbook).

- **Incus Client**: `incus` or `incus-client` package must be installed and available in the PATH.
- **Python**: 3.6+

### Tested Configuration
The collection was developed and validated in the following environment:
- **Host OS**: Debian 12
- **Incus Server/Client**: 6.21
- **Ansible**: 13.3.0
- **Ansible Core**: 2.20.2

## Installation

### From Ansible Galaxy (Not yet published)
```bash
ansible-galaxy collection install crystian.incus
```

### From Git
```bash
ansible-galaxy collection install git+https://github.com/Crystian0704/incus-plugin.git
```

### Local Build
```bash
ansible-galaxy collection build
ansible-galaxy collection install crystian-incus-1.0.0.tar.gz
```

## Modules

| Module | Description |
|Args|---|
| `incus_instance` | Create, manage, and delete Incus instances (containers/VMs). |
| `incus_storage` | Manage Incus storage pools. |
| `incus_storage_volume` | Manage Incus storage volumes. |
| `incus_profile` | Manage Incus profiles. |
| `incus_project` | Manage Incus projects. |
| `incus_image` | Manage Incus images. |
| `incus_remote` | Manage Incus remotes. |
| `incus_exec` | Execute commands in instances. |
| `incus_file` | Manage files in instances. |
| `incus_snapshot` | Manage instance snapshots. |

## Usage Examples

### Create a Container
```yaml
- name: Create a Debian container
  crystian.incus.incus_instance:
    name: my-container
    remote_image: images:debian/12
    state: present
    started: true
```

### Create a Virtual Machine
```yaml
- name: Create a Debian VM
  crystian.incus.incus_instance:
    name: my-vm
    remote_image: images:debian/12
    type: virtual-machine
    config:
      limits.cpu: 2
      limits.memory: 2GiB
    state: present
```

### Execute Command
```yaml
- name: Upgrade packages
  crystian.incus.incus_exec:
    instance: my-container
    command: apt-get update && apt-get upgrade -y
```



## Running Tests

Integration tests are included to validate the functionality of the collection.

### Prerequisites
- Incus server running and configured on the local machine (`incus admin init`).
- `incus` client available in PATH.
- Permissions to manage incus (membership in `incus`).

### Running Integration Suite
Run the full integration test suite using `ansible-playbook`:

```bash
ansible-playbook tests/integration.yml
```

You can also run specific module tests using tags:
```bash
# Test only incus_instance module
ansible-playbook tests/integration.yml --tags incus_instance
```

## Known Limitations

- **Missing Modules**: `incus_network` for `incus network` and `incus_cluster` for `incus cluster` are not yet implemented.
- **Storage Backends**: Support for some specific storage backends is incomplete.
- **Testing**: More complex integration tests and edge cases need to be covered.

## Disclaimer

> [!WARNING]
> This collection was built with the assistance of **Google Antigravity** and **Gemini 3 Pro**.
> **Sandbox Validation Required**: All usage must be validated in a sandbox/test environment before production use.

## License
MIT
