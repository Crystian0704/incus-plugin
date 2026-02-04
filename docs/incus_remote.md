# incus_remote

Manage Incus remotes

Add, remove, and manage Incus remote servers.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `name` | True |  |  | Name of the remote. |
| `url` | False |  |  | URL of the remote (e.g. https://1.2.3.4:8443). Required when adding a new remote, unless token implies it. |
| `protocol` | False | incus |  | Protocol to use (incus or simplestreams). |
| `token` | False |  |  | Trust token for adding the remote. |
| `password` | False |  |  | Trust password (if token not provided). {'Note': 'Prefer tokens for better security and non-interactive usage.'} |
| `accept_certificate` | False | False |  | Whether to automatically accept the server certificate. |
| `state` | False | present | ['present', 'absent'] | State of the remote. {'present': 'Ensure remote exists.'} {'absent': 'Ensure remote is removed.'} |
| `project` | False |  |  | Default project to use for this remote. |

## Examples

```yaml
- name: Add a remote using a token
  crystian.incus.incus_remote:
    name: my-cluster
    token: "eyJhbGciOi..."
    accept_certificate: true
- name: Add a remote using password and URL
  crystian.incus.incus_remote:
    name: my-server
    url: "https://192.168.1.50:8443"
    password: "secret-password"
    accept_certificate: true
- name: Remove a remote
  crystian.incus.incus_remote:
    name: my-server
    state: absent
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
```
