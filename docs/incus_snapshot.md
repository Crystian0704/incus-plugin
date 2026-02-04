# incus_snapshot

Manage Incus instance snapshots

Create, delete, restore, or rename snapshots of Incus instances.

## Parameters

| Parameter | Required | Default | Choices | Description |
|---|---|---|---|---|
| `instance` | True |  |  | Name of the instance. |
| `snapshot_name` | True |  |  | Name of the snapshot. Required for most operations except some list scenarios (though not implemented here). |
| `state` | False | present | ['present', 'absent', 'restored', 'renamed'] | State of the snapshot. {'present': 'Create a snapshot.'} {'absent': 'Delete a snapshot.'} {'restored': 'Restore the instance from this snapshot.'} {'renamed': "Rename the snapshot (requires 'new_name')."} |
| `new_name` | False |  |  | New name for the snapshot (used with state='renamed'). |
| `expires` | False |  |  | Expiry date for the snapshot (e.g. '30d'). Used only when creating (state='present'). |
| `reuse` | False | False |  | Whether to overwrite an existing snapshot with the same name. Used only when state='present'. |
| `stateful` | False | False |  | Whether to include running state in the snapshot (for VMs) or restore state. Used with state='present' or state='restored'. |
| `remote` | False | local |  | The remote server. Defaults to 'local'. |
| `project` | False | default |  | The project the instance belongs to. Defaults to 'default'. |

## Examples

```yaml
- name: Create a snapshot
  crystian.incus.incus_snapshot:
    instance: my-container
    snapshot_name: snap0
    state: present
- name: Create a stateful snapshot (VM only)
  crystian.incus.incus_snapshot:
    instance: my-vm
    snapshot_name: state-snap
    stateful: true
    state: present
- name: Restore a snapshot
  crystian.incus.incus_snapshot:
    instance: my-container
    snapshot_name: snap0
    state: restored
- name: Rename a snapshot
  crystian.incus.incus_snapshot:
    instance: my-container
    snapshot_name: snap0
    new_name: snap-initial
    state: renamed
- name: Delete a snapshot
  crystian.incus.incus_snapshot:
    instance: my-container
    snapshot_name: snap0
    state: absent
```

## Return Values

```yaml
msg:
  description: Status message
  returned: always
  type: str
```
