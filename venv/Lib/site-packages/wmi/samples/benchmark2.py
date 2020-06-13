import imp
import os

from distutils import sysconfig

path = os.path.dirname(os.path.abspath(__file__))
mi_wmi_path = os.path.join(
    os.path.join(os.path.dirname(path), "wmi"), "__init__.py")

path = sysconfig.get_python_lib()
old_wmi_path = os.path.join(path, "wmi.py")

VM_NAME = 'vm1'


def test_mi():
    import mi

    with mi.Application() as a:
        with a.create_session(protocol=mi.PROTOCOL_WMIDCOM) as s:
            with s.exec_query(
                    u"root/virtualization/v2",
                    u"select * from Msvm_VirtualSystemManagementService") as q:
                svc = q.get_next_instance()

                c = svc.get_class()
                p = a.create_method_params(c, u"GetSummaryInformation")

                with s.exec_query(
                        u"root/virtualization/v2",
                        u"select * from Msvm_ComputerSystem where "
                        "ElementName = '%s'" % VM_NAME) as q1:
                    vm = q1.get_next_instance()

                    with s.get_associators(
                            u"root/virtualization/v2",
                            vm, assoc_class=u"Msvm_SettingsDefineState",
                            result_class=u"Msvm_VirtualSystem"
                            "SettingData") as q2:
                        vssd = q2.get_next_instance()

                        p[u'SettingData'] = (vssd,)
                        p[u'requestedInformation'] = (4, 100, 103, 105)

                        with s.invoke_method(
                                svc, u"GetSummaryInformation", p) as q3:
                            r = q3.get_next_instance()
                            print("Result: %s" % r[u"ReturnValue"])
                            summary_info = r[u"SummaryInformation"][0]

                            print("vCPUs: %s" %
                                  summary_info[u"NumberOfProcessors"])
                            print("EnabledState: %s" %
                                  summary_info[u"EnabledState"])
                            print("Memory: %s" % summary_info[u"MemoryUsage"])
                            print("UpTime: %s" % summary_info[u"UpTime"])


def test_wmi_new():
    wmi = imp.load_source('wmi', old_wmi_path)
    test_wmi(wmi)


def test_wmi_old():
    wmi = imp.load_source('wmi', mi_wmi_path)
    test_wmi(wmi)


def test_wmi(wmi):
    conn = wmi.WMI(moniker="root\\virtualization\\v2")
    svc = conn.Msvm_VirtualSystemManagementService()[0]
    vm = conn.query(
        "select * from Msvm_ComputerSystem where ElementName = '%s'" %
        VM_NAME)[0]

    vssd = vm.associators(
        wmi_association_class="Msvm_SettingsDefineState",
        wmi_result_class="Msvm_VirtualSystemSettingData")[0]

    (ret_val, summary_info) = svc.GetSummaryInformation(
        [4, 100, 103, 105],
        [vssd.path_()])

    print("Result: %s" % ret_val)
    summary_info = summary_info[0]

    print("vCPUs: %s" % summary_info.NumberOfProcessors)
    print("EnabledState: %s" % summary_info.EnabledState)
    print("Memory: %s" % summary_info.MemoryUsage)
    print("UpTime: %s" % summary_info.UpTime)


if __name__ == '__main__':
    import timeit
    print("Running with MI module...")
    t_new = timeit.timeit(
        "test_mi()", setup="from __main__ import test_mi", number=10)
    print("Running with new WMI module...")
    t_wrap = timeit.timeit(
        "test_wmi_new()", setup="from __main__ import test_wmi_new", number=10)
    print("Running with old WMI module...")
    t_old = timeit.timeit(
        "test_wmi_old()", setup="from __main__ import test_wmi_old", number=10)

    print("Old WMI module: %s seconds" % t_old)
    print("New WMI module: %s seconds" % t_wrap)
    print("MI module: %s seconds" % t_new)

    print("Performance improvement (MI over old WMI): {percent:.2%}".format(
        percent=(1 - t_new / t_old)))
