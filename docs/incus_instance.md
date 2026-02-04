# incus_instance

Manage Incus instances (create and start)

Create and manage Incus instances.
Combines functionality of 'incus init' and 'incus launch'.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `name` | True |  |  | Name of the instance. |
| `remote` | False |  |  | Remote server to create the instance on. |
| `remote_image` | True |  |  | Image to use (e.g., 'images:debian/12'). |
| `started` | False | True |  | If true, ensure instance is started. If false, ensure instance is stopped. Ignored if state is 'absent'. |
| `state` | False | present | ['present', 'absent'] | State of the instance. {'present': "Ensure instance exists (and started/stopped based on 'started' param)."} {'absent': 'Ensure instance is removed.'} |
| `force` | False | False |  | Force removal of running instances (only used when state='absent'). |
| `description` | False |  |  | Description of the instance. |
| `empty` | False | False |  | Create an empty instance. |
| `ephemeral` | False | False |  | Create an ephemeral instance. |
| `vm` | False | False |  | Create a virtual machine instead of a container. |
| `type` | False |  |  | Instance type (e.g. 'c1.micro'). |
| `profiles` | False |  |  | List of profiles to apply to the instance. |
| `no_profiles` | False | False |  | Create the instance with no profiles. |
| `network` | False |  |  | Network name to attach to. |
| `storage` | False |  |  | Storage pool name. |
| `target` | False |  |  | Cluster member name to target. |
| `config` | False |  |  | Key/value pairs for instance configuration (e.g. {'limits.cpu': '2'}). |
| `devices` | False |  |  | Key/value pairs for device configuration. |
| `user_data` | False |  |  | Cloud-init user-data content. Sets 'cloud-init.user-data' config option. |
| `network_config` | False |  |  | Cloud-init network-config content. Sets 'cloud-init.network-config' config option. |
| `vendor_data` | False |  |  | Cloud-init vendor-data content. Sets 'cloud-init.vendor-data' config option. |
| `cloud_init_disk` | False | False |  | If true, attaches a 'cloud-init' disk device (source=cloud-init:config). Required for VMs without incus-agent or specific images. |

## Examples

```yaml
- name: Create a container with cloud-init
  crystian.incus.incus_instance:
    name: my-web-server
    remote_image: images:ubuntu/22.04/cloud
    user_data: |
      #cloud-config
      package_upgrade: true
      packages:
        - nginx
- name: Create a VM with cloud-init config disk
  crystian.incus.incus_instance:
    name: my-vm-server
    remote_image: images:debian/12/cloud
    vm: true
    cloud_init_disk: true
    user_data: "{{ lookup('file', 'user-data.yml') }}"
```

## Return Values

```yaml
instance:
  description: Instance information
  returned: always
  type: dict
```
