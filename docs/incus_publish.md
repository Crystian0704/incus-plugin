# incus_publish

Publish Incus images from instances

Create new images from existing instances or snapshots using `incus publish`.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `instance` | True |  |  | Name of the source instance. |
| `snapshot` | False |  |  | Name of the snapshot to publish from. If not provided, publishes the current instance state (requires instance to be stopped usually). |
| `alias` | True |  |  | Alias for the new image. |
| `public` | False | False |  | Whether the new image should be public. |
| `expire` | False |  |  | Expiration date for the new image. |
| `reuse` | False | False |  | Overwrite existing image alias if it exists. |
| `properties` | False |  |  | Dictionary of properties to set on the new image. |
| `compression` | False |  |  | Compression algorithm to use. |
| `remote` | False | local |  | The remote server. Defaults to 'local'. |
| `project` | False | default |  | The project the instance belongs to. Defaults to 'default'. |

## Examples

```yaml
- name: Publish instance as image
  crystian.incus.incus_publish:
    instance: my-container
    alias: my-custom-image
    public: true
- name: Publish snapshot
  crystian.incus.incus_publish:
    instance: my-container
    snapshot: snap0
    alias: my-stable-image
    reuse: true
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
fingerprint:
  description: Fingerprint of the created image
  returned: always
  type: str
```
