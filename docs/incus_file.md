# incus_file

Manage files in Incus instances

Manage files in Incus instances (push, pull, delete).
Designed to follow Ansible's `copy`, `fetch`, and `file` nomenclature.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `name` | True |  |  | Name of the instance. |
| `state` | False | pushed | ['pushed', 'pulled', 'absent'] | State of the file. {'pushed': "Push a local file ('src') or content ('content') to the instance ('dest')."} {'pulled': "Pull a file from the instance ('src') to local destination ('dest')."} {'absent': "Delete a file from the instance ('dest')."} |
| `src` | False |  |  | Source path. {"If state='pushed'": 'Local path to the file to push.'} {"If state='pulled'": 'Remote path inside the instance.'} |
| `dest` | False |  |  | Destination path. {"If state='pushed'": 'Remote path inside the instance.'} {"If state='pulled'": 'Local destination path.'} {"If state='absent'": 'Remote path to delete.'} |
| `content` | False |  |  | Content to push to the file (when state=pushed). Mutually exclusive with 'src'. |
| `owner` | False |  |  | Owner name or ID for the pushed file. If a name is provided, it is resolved inside the instance. |
| `group` | False |  |  | Group name or ID for the pushed file. If a name is provided, it is resolved inside the instance. |
| `mode` | False |  |  | File permissions for the pushed file (e.g. '0644'). |
| `remote` | False | local |  | The remote server. Defaults to 'local'. |
| `project` | False | default |  | The project the instance belongs to. Defaults to 'default'. |

## Examples

```yaml
- name: Push a local file (copy style)
  crystian.incus.incus_file:
    name: my-container
    src: /tmp/local_file.txt
    dest: /root/remote_file.txt
    owner: root
    group: root
    mode: '0644'
    state: pushed
- name: Push content directly
  crystian.incus.incus_file:
    name: my-container
    content: "Hello from Ansible"
    dest: /root/hello.txt
    state: pushed
- name: Pull a file (fetch style)
  crystian.incus.incus_file:
    name: my-container
    src: /etc/hosts
    dest: /tmp/container_hosts
    state: pulled
- name: Delete a file (file style)
  crystian.incus.incus_file:
    name: my-container
    dest: /tmp/garbage.txt
    state: absent
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
```
