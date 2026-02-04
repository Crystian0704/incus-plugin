# incus_exec

Execute commands in Incus instances

Execute commands inside Incus instances (containers and VMs) using the `incus exec` command.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `name` | True |  |  | Name of the instance to execute command in. |
| `command` | True |  |  | The command to execute. Can be a string or a list of arguments. |
| `remote` | False | local |  | The remote server to execute on. Defaults to 'local'. |
| `project` | False | default |  | The project the instance belongs to. Defaults to 'default'. |
| `user` | False |  |  | User ID to run the command as. |
| `group` | False |  |  | Group ID to run the command as. |
| `cwd` | False |  |  | Directory to run the command in. |
| `env` | False |  |  | Dictionary of environment variables to set. |
| `mode` | False | non-interactive | ['interactive', 'non-interactive'] | Execution mode. 'interactive' attaches to the terminal (mostly for manual runs, but supported). 'non-interactive' (default) captures stdout/stderr. |

## Examples

```yaml
- name: Run a simple command
  crystian.incus.incus_exec:
    name: my-container
    command: uptime
- name: Run as specific user
  crystian.incus.incus_exec:
    name: my-container
    command: whoami
    user: 1000
- name: Run in specific directory with env vars
  crystian.incus.incus_exec:
    name: my-container
    command: ls -la
    cwd: /var/log
    env:
      MY_VAR: "hello"
```

## Return Values

```yaml
stdout:
  description: The standard output of the command
  returned: always
  type: str
stderr:
  description: The standard error of the command
  returned: always
  type: str
rc:
  description: The return code of the command
  returned: always
  type: int
cmd:
  description: The command executed
  returned: always
  type: str
```
