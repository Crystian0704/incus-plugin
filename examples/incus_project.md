# incus_project

Manage Incus projects.

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `name` | Yes | - | Name of the project. |
| `description` | No | - | Project description. |
| `config` | No | - | Dictionary of project configuration (features, limits, restrictions). |
| `source` | No | - | Path to YAML file for project definition. |
| `state` | No | `present` | `present` or `absent`. |
| `remote` | No | `local` | Remote Incus server. |
| `rename_from` | No | - | Rename an existing project to `name`. |

## Examples

### Create Restricted Project
```yaml
- name: Create restricted project
  crystian.incus.incus_project:
    name: restricted-env
    description: "Sandbox Environment"
    config:
      features.images: "false"
      features.profiles: "true"
      limits.containers: "5"
      restricted: "true"
      restricted.containers.nesting: "allow"
```

### Create from Source
```yaml
- name: Project from source
  crystian.incus.incus_project:
    name: my-project
    source: /path/to/project-config.yaml
    config:
      limits.containers: "10" # Override source
```

### Delete Project
```yaml
- name: Delete project
  crystian.incus.incus_project:
    name: restricted-env
    state: absent
```
