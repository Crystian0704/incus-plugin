# incus_project

Manage Incus projects

Create, update, and delete Incus projects.
configure limits, features, and restrictions.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `name` | True |  |  | Name of the project. |
| `description` | False |  |  | Description of the project. |
| `config` | False |  |  | Dictionary of configuration options (e.g., 'features.images': 'false'). Handles limits, restrictions, and features. |
| `source` | False |  |  | Path to a YAML file containing project definition. |
| `state` | False | present | ['present', 'absent'] | State of the project. {'present': 'Ensure project exists and matches config.'} {'absent': 'Ensure project is deleted.'} |
| `rename_from` | False |  |  | If provided, rename the specified project to 'name'. |
| `remote` | False | local |  | The remote server. Defaults to 'local'. |

## Examples

```yaml
- name: Create a restricted project
  crystian.incus.incus_project:
    name: dev-project
    description: "Development environment"
    config:
      features.images: "false"
      features.profiles: "true"
      limits.containers: "5"
      restricted: "true"
      restricted.containers.nesting: "allow"
- name: Delete a project
  crystian.incus.incus_project:
    name: dev-project
    state: absent
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
```
