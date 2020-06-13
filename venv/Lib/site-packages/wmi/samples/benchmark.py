def test_mi():
    import mi

    with mi.Application() as a:
        with a.create_session(protocol=mi.PROTOCOL_WMIDCOM) as s:
            with s.exec_query(
                    u"root\\cimv2", u"select * from win32_process") as q:
                i = q.get_next_instance()
                while i is not None:
                    s = i[u'name']
                    i = q.get_next_instance()


def test_wmi():
    import wmi

    conn = wmi.WMI(moniker="root\\cimv2")
    for i in conn.win32_process():
        s = i.name


if __name__ == '__main__':
    import timeit
    print(timeit.timeit(
        "test_mi()", setup="from __main__ import test_mi", number=20))
    print(timeit.timeit(
        "test_wmi()", setup="from __main__ import test_wmi", number=20))
