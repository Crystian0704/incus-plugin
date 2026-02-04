# incus_list

List Incus instances

List Incus instances using the C(incus list) command.
Returns a list of instances with their configuration and state.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `filters` | False |  |  | List of filters to apply (e.g. C("status=running"), C("type=container")). Can be a list of strings or a dictionary. |
| `remote` | False |  |  | The remote server to query (e.g. C("kawa")). |
| `all_remotes` | False | False |  | List instances from all configured remotes with protocol 'incus'. |
| `all_projects` | False | False |  | List instances from all projects. |
| `project` | False |  |  | Project to list instances from. |

## Examples

```yaml
- name: List all local instances
  crystian.incus.incus_list:
  register: all_instances
- name: List running containers
  crystian.incus.incus_list:
    filters:
      - status=Running
      - type=container
  register: running_containers
- name: List instances on remote
  crystian.incus.incus_list:
    remote: kawa
  register: remote_instances
```

## Return Values

```yaml
list:
  description: List of instances
  returned: always
  type: list
  sample:
    - name: my-container
      status: Running
      type: container
      # ... (full incus config)
```
