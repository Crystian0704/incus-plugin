# incus_image

Manage Incus images

Manage images in the Incus image store.
Supports copying from remotes, importing from files, exporting to files, and deleting.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `alias` | True |  |  | Alias of the image. Used as the primary identifier for presence checks if fingerprint is not provided. |
| `fingerprint` | False |  |  | Fingerprint of the image. If provided, used to verify the exact image identity. |
| `state` | False | present | ['present', 'absent', 'exported'] | State of the image. {'present': 'Ensure image exists (copy or import if missing).'} {'absent': 'Ensure image is removed.'} {'exported': 'Export image to file.'} |
| `source` | False |  |  | Source for the image when state='present'. Can be a remote image (e.g. 'images:alpine/edge') or a local file path. If it looks like a file path, it is treated as an import. If it looks like a remote:alias, it is treated as a copy. |
| `dest` | False |  |  | Destination path for exported image (when state='exported'). |
| `properties` | False |  |  | Dictionary of properties to set on the image. |
| `aliases` | False |  |  | List of additional aliases to assign to the image. |
| `public` | False | False |  | Whether the image should be public. |
| `auto_update` | False | False |  | Whether to auto-update the image (valid for remote copies). |
| `remote` | False | local |  | The remote server. Defaults to 'local'. |
| `project` | False | default |  | The project instance belongs to. Defaults to 'default'. |

## Examples

```yaml
- name: Copy alpine image from images remote
  crystian.incus.incus_image:
    alias: my-alpine
    source: images:alpine/edge
    state: present
- name: Import image from local file
  crystian.incus.incus_image:
    alias: custom-image
    source: /tmp/image.tar.gz
    state: present
- name: Export image to file
  crystian.incus.incus_image:
    alias: my-alpine
    dest: /tmp/my-alpine-backup.tar.gz
    state: exported
- name: Delete image
  crystian.incus.incus_image:
    alias: my-alpine
    state: absent
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
fingerprint:
  description: Fingerprint of the managed image
  returned: when available
  type: str
```
