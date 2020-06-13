import imp
import os

from distutils import sysconfig


path = os.path.dirname(os.path.abspath(__file__))
mi_wmi_path = os.path.join(
    os.path.join(os.path.dirname(path), "wmi"), "__init__.py")

path = sysconfig.get_python_lib()
old_wmi_path = os.path.join(path, "wmi.py")

VM_NAME = "wmi_benchmark_vm1"
PORT_NAME = "port_name"
SWITCH_NAME = 'external'


def run_test():
    from hyperv.neutron import utilsv2
    from hyperv.neutron import security_groups_driver
    from hyperv.nova import constants
    from hyperv.nova import vmutilsv2

    u = vmutilsv2.VMUtilsV2()

    net_utils = utilsv2.HyperVUtilsV2R2()
    sg_gen = security_groups_driver.SecurityGroupRuleGeneratorR2()
    sg_rules = sg_gen.create_default_sg_rules()

    if u.vm_exists(VM_NAME):
        u.destroy_vm(VM_NAME)

    u.create_vm(VM_NAME, False, 1, "c:\\openstack\\test", ['blah'])
    u.update_vm(VM_NAME, 256, 256, 1, 1, False, 1.0)

    u.set_boot_order(VM_NAME, (0, 1, 2, 3))

    u.create_nic(VM_NAME, PORT_NAME, "00:99:99:99:99:99")

    u.create_scsi_controller(VM_NAME)
    u.get_vm_ide_controller(VM_NAME, 0)
    u.attach_ide_drive(
        VM_NAME, "c:\\VHDs\\test.vhdx", 0, 0, constants.DISK)

    u.get_vm_summary_info(VM_NAME)
    u.list_instances()
    u.get_vm_id(VM_NAME)
    u.set_vm_state(VM_NAME, constants.HYPERV_VM_STATE_ENABLED)

    net_utils.connect_vnic_to_vswitch(SWITCH_NAME, PORT_NAME)
    net_utils.set_vswitch_port_vlan_id(1000, PORT_NAME)
    net_utils.create_security_rules(PORT_NAME, sg_rules)
    net_utils.remove_all_security_rules(PORT_NAME)

    u.set_vm_state(VM_NAME, constants.HYPERV_VM_STATE_DISABLED)
    u.destroy_vm(VM_NAME)


def test_mi():
    wmi = imp.load_source('wmi', mi_wmi_path)
    # Simple way to check we're loading the right module
    wmi._Connection
    run_test()


def test_wmi():
    wmi = imp.load_source('wmi', old_wmi_path)
    # Simple way to check we're loading the right module
    wmi.handle_com_error
    run_test()


if __name__ == '__main__':
    import timeit
    print("Running with new WMI module...")
    t_new = timeit.timeit(
        "test_mi()", setup="from __main__ import test_mi", number=1)
    print("Running with old WMI module...")
    t_old = timeit.timeit(
        "test_wmi()", setup="from __main__ import test_wmi", number=1)

    print("Old WMI module: %s seconds" % t_old)
    print("New WMI module: %s seconds" % t_new)

    print("Performance improvement: {percent:.2%}".format(
        percent=(1 - t_new / t_old)))
