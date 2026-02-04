# incus_remote

Manage Incus remote servers.

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `name` | Yes | - | Name of the remote. |
| `url` | No | - | URL of the remote. |
| `token` | No | - | Trust token for authentication. |
| `password` | No | - | Trust password (alternative to token). |
| `accept_certificate` | No | `false` | Auto-accept server certificate. |
| `state` | No | `present` | `present` or `absent`. |
| `project` | No | - | Default project (e.g. `default`). |

## Examples

### Add Remote with Token
```yaml
- name: Add cluster remote
  crystian.incus.incus_remote:
    name: my-cluster
    token: "..."
    accept_certificate: true
```

### Remove Remote
```yaml
- name: Remove remote
  crystian.incus.incus_remote:
    name: my-cluster
    state: absent
```
