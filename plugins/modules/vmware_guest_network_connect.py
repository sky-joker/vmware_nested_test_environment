#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, sky-joker
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: vmware_guest_network_connect
short_description: Connect network of Virtual Machine.
description:
  - This module is to connect networks of Virtual Machine.
author:
  - sky-joker (@sky-joker)
requirements:
  - python >= 3.6
  - PyVmomi
options:
  hostname:
    description:
      - The hostname or IP address of the vSphere vCenter or ESXi server.
    type: str
    required: True
  username:
    description:
      - The username of the vSphere vCenter or ESXi server.
    type: str
    required: True
  password:
    description:
      - The password of the vSphere vCenter or ESXi server.
    type: str
    required: True
  validate_certs:
    description:
      - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
    type: bool
    default: True
  name:
    description:
      - The name of the Virtual Machine.
    type: str
    required: True
'''

EXAMPLES = r'''
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from pyVim.connect import SmartConnect, Disconnect
    from pyVmomi import vim
except ImportError:
    pass
import ssl
import atexit


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(type='str', required=True),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True),
            validate_certs=dict(type='bool', default=True),
            name=dict(type='str', required=True),
        ),
        supports_check_mode=True
    )

    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']
    validate_certs = module.params['validate_certs']
    name = module.params['name']

    context = None
    if validate_certs is False:
        if hasattr(ssl, '_create_unverified_context'):
            context = ssl._create_unverified_context()

    try:
        si = SmartConnect(host=hostname,
                          user=username,
                          pwd=password,
                          sslContext=context)
    except Exception as e:
        module.fail_json(msg="Failed to connect to vCenter Server %s" % hostname)

    atexit.register(Disconnect, si)

    content = si.content
    mob_list = content.viewManager.CreateContainerView(content.rootFolder,
                                                       [vim.VirtualMachine],
                                                       True)

    if mob_list.view:
        for mob in mob_list.view:
            if mob.name == name:
                nic_connected_specs = []
                for device in mob.config.hardware.device:
                    spec_device_change = vim.vm.device.VirtualDeviceSpec()
                    if isinstance(device, vim.vm.device.VirtualVmxnet3):
                        spec_device_change.operation = 'edit'
                        spec_device_change.device = device
                        spec_device_change.device.connectable.connected = True
                        nic_connected_specs.append(spec_device_change)

                spec = vim.vm.ConfigSpec()
                spec.deviceChange = nic_connected_specs

                try:
                    mob.ReconfigVM_Task(spec)
                except Exception as e:
                    module.fail_json(msg="Failed to change a network setting of Virtual Machine: %s" % name)

                module.exit_json(changed=True)

        module.fail_json(msg="Not found Virtual Machine: %s" % name)
    else:
        module.fail_json(msg="Not found Virtual Machines")

    module.exit_json(changed=False)


if __name__ == "__main__":
    main()
