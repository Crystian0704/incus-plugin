# incus_export

Export Incus instances

Export Incus instances to backup files.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `instance` | True |  |  | Name of the instance to export. |
| `path` | True |  |  | Destination path for the backup file. If it is a directory, the file will be named <instance>.tar.gz (or similar) inside it. |
| `compression` | False |  |  | Compression algorithm (e.g. gzip, bzip2, none). |
| `optimized` | False | False |  | Use optimized storage format (driver specific). |
| `instance_only` | False | False |  | Export only the instance volume without snapshots. |
| `force` | False | False |  | Overwrite destination file if it exists. |
| `remote` | False | local |  | The remote server. Defaults to 'local'. |
| `project` | False | default |  | The project the instance belongs to. Defaults to 'default'. |

## Examples

```yaml
- name: Export instance to file
  crystian.incus.incus_export:
    instance: my-container
    path: /backups/my-container.tar.gz
- name: Export optimized backup
  crystian.incus.incus_export:
    instance: my-container
    path: /backups/my-container.bin
    optimized: true
    force: true
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
file:
  description: Path to the exported file
  returned: always
  type: str
```
