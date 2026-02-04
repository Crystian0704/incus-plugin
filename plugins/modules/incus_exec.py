#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type
DOCUMENTATION = r'''
---
module: incus_exec
short_description: Execute commands in Incus instances
description:
  - Execute commands inside Incus instances (containers and VMs) using the `incus exec` command.
version_added: "1.0.0"
options:
  name:
    description:
      - Name of the instance to execute command in.
    required: true
    type: str
    aliases: [ instance ]
  command:
    description:
      - The command to execute.
      - Can be a string or a list of arguments.
    required: true
    type: raw
  remote:
    description:
      - The remote server to execute on.
      - Defaults to 'local'.
    required: false
    type: str
    default: local
  project:
    description:
      - The project the instance belongs to.
      - Defaults to 'default'.
    required: false
    type: str
    default: default
  user:
    description:
      - User ID to run the command as.
    required: false
    type: int
  group:
    description:
      - Group ID to run the command as.
    required: false
    type: int
  cwd:
    description:
      - Directory to run the command in.
    required: false
    type: path
  env:
    description:
      - Dictionary of environment variables to set.
    required: false
    type: dict
  mode:
    description:
      - Execution mode.
      - "'interactive' attaches to the terminal (mostly for manual runs, but supported)."
      - "'non-interactive' (default) captures stdout/stderr."
    required: false
    type: str
    default: non-interactive
    choices: [ interactive, non-interactive ]
author:
  - Crystian (@crystian)
'''
EXAMPLES = r'''
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
'''
RETURN = r'''
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
'''
from ansible.module_utils.basic import AnsibleModule
import subprocess
import shlex
def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True, aliases=['instance']),
            command=dict(type='raw', required=True),
            remote=dict(type='str', default='local', required=False),
            project=dict(type='str', default='default', required=False),
            user=dict(type='int', required=False),
            group=dict(type='int', required=False),
            cwd=dict(type='path', required=False),
            env=dict(type='dict', required=False),
            mode=dict(type='str', default='non-interactive', choices=['interactive', 'non-interactive'], required=False),
        ),
        supports_check_mode=True,
    )
    name = module.params['name']
    command_param = module.params['command']
    remote = module.params['remote']
    project = module.params['project']
    user = module.params['user']
    group = module.params['group']
    cwd = module.params['cwd']
    env = module.params['env']
    mode = module.params['mode']
    target = name
    if remote and remote != 'local':
        target = "{}:{}".format(remote, name)
    incus_cmd = ['incus', 'exec', target]
    if project:
        incus_cmd.extend(['--project', project])
    if user is not None:
        incus_cmd.extend(['--user', str(user)])
    if group is not None:
        incus_cmd.extend(['--group', str(group)])
    if cwd:
        incus_cmd.extend(['--cwd', cwd])
    if mode == 'interactive':
        incus_cmd.extend(['--mode', 'interactive'])
    else:
        incus_cmd.extend(['--mode', 'non-interactive'])
    if env:
        for k, v in env.items():
            incus_cmd.extend(['--env', "{}={}".format(k, v)])
    incus_cmd.append('--')
    if isinstance(command_param, list):
        cmd_args = [str(x) for x in command_param]
        incus_cmd.extend(cmd_args)
    elif isinstance(command_param, str):
        cmd_args = shlex.split(command_param)
        incus_cmd.extend(cmd_args)
    else:
        module.fail_json(msg="Command must be a string or a list")
    if module.check_mode:
        module.exit_json(changed=False, msg="Command would run: {}".format(" ".join(incus_cmd)), cmd=" ".join(incus_cmd))
    try:
        p = subprocess.Popen(incus_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        rc = p.returncode
        out_str = stdout.decode('utf-8') if stdout else ''
        err_str = stderr.decode('utf-8') if stderr else ''
        if rc != 0:
            module.fail_json(
                msg="Command failed with rc {}".format(rc),
                rc=rc,
                stdout=out_str,
                stderr=err_str,
                cmd=" ".join(incus_cmd)
            )
        module.exit_json(
            changed=True,
            rc=rc,
            stdout=out_str,
            stderr=err_str,
            cmd=" ".join(incus_cmd)
        )
    except Exception as e:
        module.fail_json(msg="Failed to run incus exec: {}".format(str(e)))
if __name__ == '__main__':
    main()
