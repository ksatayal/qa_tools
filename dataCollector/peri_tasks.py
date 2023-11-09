from celery import Celery
import time, os,sys, json, re, requests


from celery.schedules import crontab
from datetime import datetime, timedelta, timezone
import redis

import numpy as np
np.seterr(divide='ignore', invalid='ignore')


import pandas as pd

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

import etl_op as etl


REDIS_SVC_IP = os.environ.get('REDIS_SVC_IP','10.22.101.31')
REDIS_SVC_PORT = os.environ.get('TRD_REDIS_PORT',6379)

REDIS_DBNUM_CELERY_TASKS = os.environ.get('REDIS_DBNUM_CELERY_TASKS',0)
REDIS_DBNUM_CMDQUEUE = os.environ.get('REDIS_DBNUM_CMDQUEUE',3)
REDIS_DBNUM_CMDRES_JSON = os.environ.get('REDIS_DBNUM_CMDRES_JSON',5)

TRD_SVC_IP_PORT=os.environ.get("TRD_SVC_IP_PORT","10.22.101.28:10287")


#appCelery = Celery( #'tasks', \
appCelery = Celery(broker=f'redis://{REDIS_SVC_IP}:{REDIS_SVC_PORT}/{REDIS_DBNUM_CELERY_TASKS}',  \
         backend=f'redis://{REDIS_SVC_IP}:{REDIS_SVC_PORT}/{REDIS_DBNUM_CELERY_TASKS}'  \
        )

def get_last_10_min_datapoints(vmDut="vm33"):

    now = datetime.now(timezone.utc)
    rdb5 = redis.StrictRedis(host=REDIS_SVC_IP,port=REDIS_SVC_PORT,db=REDIS_DBNUM_CMDRES_JSON)

    # data cleanzing for vmDut data, to save to specific csv for later analyzing with pandas...
    seqTimestampMinUtc = []
    t = now + timedelta(minutes=-10)
    while t < now:
        seqTimestampMinUtc.append(t.strftime("%Y-%m-%dT%H:%M"))
        t = t + timedelta(minutes=1)

    dic33cnt = 0
    for t2 in seqTimestampMinUtc:
        print(f"{vmDut}-{t2}")
        r33 = rdb5.get(f"{vmDut}-{t2}")
        if r33:
            dic33cnt += 1
            dic33 = json.loads(r33.decode("UTF-*"))
            print(f"{dic33cnt}  {dic33}")


@appCelery.task
def every_minute(vmDut,vmFh, vmVrtr):
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"{now_str}: task {__name__} got {vmDut}, {vmFh}, {vmVrtr}")

    rdb3 = redis.StrictRedis(host=REDIS_SVC_IP,port=REDIS_SVC_PORT,db=REDIS_DBNUM_CMDQUEUE)
    print(f"{rdb3.keys()}")
    for k in rdb3.scan_iter("CMDQ-*"):
        sr = re.search("CMDQ-([a-z0-9]+)",k.decode("UTF-8"))
        pyatsHost = sr.group(1)
        cmd = rdb3.get(k)
        print(f"{k} : {cmd}")
        dicRshCmd = {"pyats_host": pyatsHost, "cmd": cmd.decode("UTF-8") }
        r = requests.put(f'http://{TRD_SVC_IP_PORT}/private/rshcmd',  \
                    data=json.dumps(dicRshCmd),   \
                    headers={"Content-Type": "application/json"})

        print(r)

    return "ok"


@appCelery.task
def every_30_minutes(vmDut,vmFh="", since_utc="",daysBefore=-1):

    now = datetime.now(timezone.utc)
    #print(f"{now}: task {__name__} got {vmDut}, {vmFh},")

    rdb5 = redis.StrictRedis(host=REDIS_SVC_IP,port=REDIS_SVC_PORT,db=REDIS_DBNUM_CMDRES_JSON)

    if since_utc != "":
        rawdata_since = datetime.strptime(since_utc,"%Y-%m-%dT%H:%M:%S%z")
        #print(f"{since_utc}, raadata from {rawdata_since},now={now}")
    else:
        rawdata_since =  now + timedelta(days=daysBefore)

    # data cleanzing for vmDut data, to save to specific csv for later analyzing with pandas...
    seqTimestampMinUtc = []
    #t = now + timedelta(days=daysBefore)
    print(f"since {rawdata_since} till {now}")
    t = rawdata_since
    while t < now:
        seqTimestampMinUtc.append(t.strftime("%Y-%m-%dT%H:%M"))
        t = t + timedelta(minutes=1)

    #print(f"{seqTimestampMinUtc[0]} to {seqTimestampMinUtc[-1]}, {len(seqTimestampMinUtc)}min")

    dicNfUsage, dicPvUsage, dicDpUsage = etl.extract_from_timeseries_db(vmDut,seqTimestampMinUtc)

    try:
        dfNf = pd.DataFrame(dicNfUsage)
        dfNf["utc_timestamp_min"] = pd.to_datetime(dfNf["utc_timestamp_min"])
        #print(dfNf)
        outfn = f"/tmp/{vmDut}-nf-rawdata-{now.strftime('%m%d')}.csv"
        dfNf.to_csv(outfn,index=True,encoding="UTF-8")
        if os.path.exists(outfn):
            print(f"NF raw data csv saved at {outfn}")
            etl.store_plotted_fig(outfn, remote_path="/home/vm10131/rsyncSrc")

        outfn = f"/tmp/{vmDut}-nf-usages-{now.strftime('%m%d')}{daysBefore}d.png"
        etl.visualize_nf_usage(dfNf,vmDut,outfn=outfn)
        if os.path.exists(outfn):
            print(f"plot figure saved at {outfn}")
            etl.store_plotted_fig(outfn, remote_path="/home/vm10131/rsyncSrc")

    except Exception as exc:
        print(exc)
        for k,v in dicNfUsage.items():
            print(f"{k} > {len(v)}")

    try:
        dfPv = pd.DataFrame(dicPvUsage)
        dfPv["utc_timestamp_min"] = pd.to_datetime(dfPv["utc_timestamp_min"])
        #print(dfPv)
        outfn = f"/tmp/{vmDut}-pv-rawdata-{now.strftime('%m%d')}.csv"
        dfPv.to_csv(outfn,index=True,encoding="UTF-8")
        if os.path.exists(outfn):
            print(f"pv raw data csv saved at {outfn}")
            etl.store_plotted_fig(outfn, remote_path="/home/vm10131/rsyncSrc")
        outfn = f"/tmp/{vmDut}-pv-usages-{now.strftime('%m%d')}{daysBefore}d.png"
        etl.visualize_pv_usage(dfPv,vmDut,outfn=outfn)
        if os.path.exists(outfn):
            print(f"plot figure saved at {outfn}")
            etl.store_plotted_fig(outfn, remote_path="/home/vm10131/rsyncSrc")
    except Exception as exc:
        print(exc)
        for k,v in dicPvUsage.items():
            print(f"{k} > {len(v)}")

    dfN3n6Usage = etl.transform_cal_MBps(dicDpUsage)
    #print(dfN3n6Usage)

    if vmFh != "":
        dfGnbUsage = etl.extract_transform_gNB_usage(vmFh,seqTimestampMinUtc)
        if dfGnbUsage is not None:
            print(dfGnbUsage)
            bgn = dfGnbUsage["utc_timestamp_min"][0]
            end = dfGnbUsage["utc_timestamp_min"].iloc[-1]
            print(f"{bgn} => {end}, {end-bgn}")

            outfn = f"/tmp/{vmFh}-gnb-usages-{now.strftime('%m%d')}{daysBefore}d.csv"
            dfGnbUsage.to_csv(outfn,index=True,encoding="UTF-8")
            if os.path.exists(outfn):
                print(f"pv raw data csv saved at {outfn}")
                etl.store_plotted_fig(outfn, remote_path="/home/vm10131/rsyncSrc")

            outfn = f"/tmp/{vmFh}-gnb-usages-{now.strftime('%m%d')}{daysBefore}d.png"
            etl.visualize_gNB_usage(dfGnbUsage,outfn)
            if os.path.exists(outfn):
                print(f"plot figure saved at {outfn}")
                etl.store_plotted_fig(outfn, remote_path="/home/vm10131/rsyncSrc")

    outfn = f"/tmp/{vmDut}-dp-usages-{now.strftime('%m%d')}{daysBefore}d.csv"
    dfN3n6Usage.to_csv(outfn,index=True,encoding="UTF-8")
    if os.path.exists(outfn):
        print(f"pv raw data csv saved at {outfn}")
        etl.store_plotted_fig(outfn, remote_path="/home/vm10131/rsyncSrc")
    outfn = f"/tmp/{vmDut}-dp-usages-{now.strftime('%m%d')}{daysBefore}d.png"
    etl.visualize_dp_usage(dfN3n6Usage,vmDut,outfn)
    if os.path.exists(outfn):
        print(f"plot figure saved at {outfn}")
        etl.store_plotted_fig(outfn, remote_path="/home/vm10131/rsyncSrc")

appCelery.conf.beat_schedule = {
    # Executes every Monday morning at 7:30 a.m.
    'every-min-vm33-top': {
        'task': 'peri_tasks.every_minute',
        'schedule': 60,
        'args': ('vm33', "vm34", "vm35"),
    },
}
t = """
    'every-half-an-hour-data-cleanzing': {
        'task': 'tasks.every_30_minutes',
        'schedule': crontab(minute='*/30'),
        'args': ('vm33', "vm34", "vm35"),
    },
    """

