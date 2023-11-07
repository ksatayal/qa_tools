#!/usr/bin/env python

import peri_tasks as tasks
import sys
import argparse
from datetime import datetime, timedelta, timezone

def goDataCleanzing(dut_name,daysBefore=-1):
    if dut_name == "vm33":
        tasks.every_30_minutes("vm33","vm34","vm35",daysBefore)
    else:
        tasks.every_30_minutes(dut_name,"vmFhNone","vmRtrNone",daysBefore)



if __name__ == "__main__":

    argp = argparse.ArgumentParser(description='Summarize 5GC/Fronthaul(UERAMSIM) collected metrics')

    argp.add_argument("--dut", type=str,default="vm33",help='The VM host which installed Harmony')
    argp.add_argument("--since",type=str,default="",help='in UTC time in format ex: "2023-11-01T12:34:56Z"')
    argp.add_argument("--daysBefore",type=int,default=-1,help='negative interger for days before, ex: -1 means 1 day ago, -3 means 3 days ago')
    argp.add_argument("--ueransim_host", type=str,default="VM for running UERANSIM container")

    args = argp.parse_args()

    dut_name = args.dut
    since_utc = args.since
    daysBefore = args.daysBefore
    vmFh = args.ueransim_host

    tasks.every_30_minutes(vmDut=dut_name,vmFh=vmFh,since_utc=since_utc,daysBefore=daysBefore)

    #intDataCollecting(dut_name)

    #tasks.get_last_10_min_datapoints(dut_name)

    #goDataCleanzing(dut_name,daysBefore=int(daysBefore))
