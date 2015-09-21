#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import smallfile
from smallfile import SMFResultException, KB_PER_GB


def output_results(invoke_list, prm_host_set, prm_thread_count, pct_files_min):
    if len(invoke_list) < 1:
        raise SMFResultException('no pickled invokes read, so no results'
                                 )
    my_host_invoke = invoke_list[0]  # pick a representative one
    total_files = 0
    total_records = 0
    max_elapsed_time = 0.0
    for invk in invoke_list:  # for each parallel SmallfileWorkload

        # add up work that it did
        # and determine time interval over which test ran

        assert isinstance(invk, smallfile.SmallfileWorkload)
        status = 'ok'
        if invk.status:
            status = 'ERR: ' + os.strerror(invk.status)
        fmt = 'host = %s,thr = %s,elapsed = %f'
        fmt += ',files = %d,records = %d,status = %s'
        print(fmt %
              (invk.onhost, invk.tid, invk.elapsed_time,
               invk.filenum_final, invk.rq_final, status))
        total_files += invk.filenum_final
        total_records += invk.rq_final
        max_elapsed_time = max(max_elapsed_time, invk.elapsed_time)

    print('total threads = %d' % len(invoke_list))
    print('total files = %d' % total_files)
    rszkb = my_host_invoke.record_sz_kb
    if rszkb == 0:
        rszkb = my_host_invoke.total_sz_kb
    if rszkb * my_host_invoke.BYTES_PER_KB > my_host_invoke.biggest_buf_size:
        rszkb = my_host_invoke.biggest_buf_size / my_host_invoke.BYTES_PER_KB
    if total_records > 0:
        total_data_gb = total_records * rszkb * 1.0 / KB_PER_GB
        print('total data = %9.3f GB' % total_data_gb)
    if len(invoke_list) < len(prm_host_set) * prm_thread_count:
        print('WARNING: failed to get some responses from workload generators')
    max_files = my_host_invoke.iterations * len(invoke_list)
    pct_files = 100.0 * total_files / max_files
    print('%6.2f%% of requested files processed, minimum is %6.2f' %
          (pct_files, pct_files_min))
    if status != 'ok':
        raise SMFResultException(
            'at least one thread encountered error, test may be incomplete')
    if max_elapsed_time > 0.001:  # can't compute rates if it ended too quickly

        print('%f sec elapsed time' % max_elapsed_time)
        files_per_sec = total_files / max_elapsed_time
        print('%f files/sec' % files_per_sec)
        if total_records > 0:
            iops = total_records / max_elapsed_time
            print('%f IOPS' % iops)
            mb_per_sec = iops * rszkb / 1024.0
            print('%f MB/sec' % mb_per_sec)
    if status == 'ok' and pct_files < pct_files_min:
        raise SMFResultException(
            'not enough total files processed, change test parameters')
