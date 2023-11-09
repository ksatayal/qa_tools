
import time, os,sys, json, re, requests
import redis

import numpy as np
np.seterr(divide='ignore', invalid='ignore')
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


REDIS_SVC_IP = os.environ.get('REDIS_SVC_IP','10.22.101.31')
REDIS_SVC_PORT = os.environ.get('TRD_REDIS_PORT',6379)

REDIS_DBNUM_CMDRES_JSON = os.environ.get('REDIS_DBNUM_CMDRES_JSON',5)

NDV=-1 # NO_DATA_VALUE

# {{{ extract_from_timeseries_db() to return dicNfUsage, dicPvUsage, dicDpUsage
def extract_from_timeseries_db(pyatsHost,seqTimestampMinUtc):
    dicNfUsage = {
        "utc_timestamp_min": [],
        "Pid_amfctrl": [],
        "Mem_amfctrl": [],
        "Pid_smfctrl": [],
        "Mem_smfctrl": [],
        "Pid_upfcctrl": [],
        "Mem_upfcctrl": [],
        "Pid_ausfctrl": [],
        "Mem_ausfctrl": [],
        "Pid_udmctrl":  [],
        "Mem_udmctrl": []
    }

    dicPvUsage = {
        "utc_timestamp_min": [],
        "loki": [],
        "influxdb2": [],
        "rmq": [],
        "prom1": [],
        "mongod": [],
        "redis": [],
        "elasticsearch": []
    }

    dicDpUsage = {
        'utc_timestamp_min': [],
        'n3_rxBytes': [],
        'n3_rxPkts': [],
        'n3_txBytes': [],
        'n3_txPkts': [],
        #'n6_rxBytes': [],
        #'n6_rxPkts': [],
        #'n6_txBytes': [],
        #'n6_txPkts': []
    }

    dicDpUsageN5G = {
        'sgi_rxBytes': [],
        'sgi_rxPkts': [],
        'sgi_txBytes': [],
        'sgi_txPkts': [],
    }
    rdb5 = redis.StrictRedis(host=REDIS_SVC_IP,port=REDIS_SVC_PORT,db=REDIS_DBNUM_CMDRES_JSON)

    dic33cnt = 0
    N5G_traffic = False

    setNfKeys = set(dicNfUsage.keys())
    setPvKeys = set(dicPvUsage.keys())
    setDpKeys = set(dicDpUsage.keys())
    for t2 in seqTimestampMinUtc:
        r33 = rdb5.get(f"{pyatsHost}-{t2}")
        if r33:
            dic33cnt += 1
            dic33 = json.loads(r33.decode("UTF-8"))
            setRetDatapoint = set(dic33.keys())
            if setNfKeys.issubset(setRetDatapoint):
                for nfKey in dicNfUsage.keys():
                    dicNfUsage[nfKey].append(dic33[nfKey])

            if setPvKeys.issubset(setRetDatapoint):
                for pvKey in dicPvUsage.keys():
                    dicPvUsage[pvKey].append(dic33[pvKey])

            if setDpKeys.issubset(setRetDatapoint):
                for k in dicDpUsage.keys():
                    dicDpUsage[k].append(dic33[k])

            if set(dicDpUsageN5G.keys()).issubset(setRetDatapoint):
                for k in dicDpUsageN5G.keys():
                    dicDpUsageN5G[k].append(dic33[k])
                N5G_traffic = True

    if N5G_traffic:
        dicDpUsage.update(dicDpUsageN5G)

    return dicNfUsage, dicPvUsage, dicDpUsage
# }}}

# {{{ transform_cal_MBps(dicDpUsage) to return pandas datafrome
def transform_cal_MBps(dicDpUsage):

    try:
        dfDp = pd.DataFrame(dicDpUsage)
        dfDp["utc_timestamp_min"] = pd.to_datetime(dfDp["utc_timestamp_min"])
        tsary = pd.to_datetime(dfDp["utc_timestamp_min"]).to_numpy()
        ts_diff =  np.diff(tsary,prepend=tsary[0])/np.timedelta64(1,'s')

        lstColToDel = []

        dfDp["n3_rxMBytes"] = np.round( dfDp["n3_rxBytes"].to_numpy()/1048576, 2 )
        n3_rxMBytes_diff = np.diff(dfDp["n3_rxMBytes"].to_numpy(),prepend=dfDp["n3_rxMBytes"][0])
        dfDp["n3_rxMBps"] = np.round(np.divide(n3_rxMBytes_diff, ts_diff),2)
        lstColToDel.append("n3_rxBytes")
        lstColToDel.append("n3_rxMBytes")

        dfDp["n3_txMBytes"] = np.round( dfDp["n3_txBytes"].to_numpy()/1048576, 2 )
        n3_txMBytes_diff = np.diff(dfDp["n3_txMBytes"].to_numpy(),prepend=dfDp["n3_txMBytes"][0])
        dfDp["n3_txMBps"] = np.round(np.divide(n3_txMBytes_diff, ts_diff),2)
        lstColToDel.append("n3_txBytes")
        lstColToDel.append("n3_txMBytes")

        #dfDp["n6_rxMBytes"] = np.round( dfDp["n6_rxBytes"].to_numpy()/1048576, 2 )
        #n6_rxMBytes_diff = np.diff(dfDp["n6_rxMBytes"].to_numpy(),prepend=dfDp["n6_rxMBytes"][0])
        #dfDp["n6_rxMBps"] = np.round(np.divide(n6_rxMBytes_diff, ts_diff),2)
        #lstColToDel.append("n6_rxBytes")
        #lstColToDel.append("n6_rxMBytes")

        #dfDp["n6_txMBytes"] = np.round( dfDp["n6_txBytes"].to_numpy()/1048576, 2 )
        #n6_txMBytes_diff = np.diff(dfDp["n6_txMBytes"].to_numpy(),prepend=dfDp["n6_txMBytes"][0])
        #dfDp["n6_txMBps"] = np.round(np.divide(n6_txMBytes_diff, ts_diff),2)
        #lstColToDel.append("n6_txBytes")
        #lstColToDel.append("n6_txMBytes")

        if "sgi_rxBytes" in dfDp:
            dfDp["sgi_rxMBytes"] = np.round( dfDp["sgi_rxBytes"].to_numpy()/1048576, 2)
            sgi_rxMBytes_diff = np.diff(dfDp["sgi_rxMBytes"].to_numpy(),prepend=dfDp["sgi_rxMBytes"][0])
            dfDp["sgi_txMBps"] = np.round(np.divide(sgi_rxMBytes_diff, ts_diff),2)
            lstColToDel.append("sgi_rxBytes")
            lstColToDel.append("sgi_txMBytes")

        if "sgi_txBytes" in dfDp:
            dfDp["sgi_txMBytes"] = np.round( dfDp["sgi_txBytes"].to_numpy()/1048576, 2)
            sgi_txMBytes_diff = np.diff(dfDp["sgi_txMBytes"].to_numpy(),prepend=dfDp["sgi_txMBytes"][0])
            dfDp["sgi_txMBps"] = np.round(np.divide(sgi_txMBytes_diff, ts_diff),2)
            lstColToDel.append("sgi_txBytes")
            lstColToDel.append("sgi_txMBytes")

        n3_rxPkts_diff = np.diff(dfDp["n3_rxPkts"].to_numpy(),prepend=dfDp["n3_rxPkts"][0])
        dfDp["n3_rxPKTps"] = np.round(np.divide(n3_rxPkts_diff, ts_diff), 0)

        n3_txPkts_diff = np.diff(dfDp["n3_txPkts"].to_numpy(),prepend=dfDp["n3_txPkts"][0])
        dfDp["n3_txPKTps"] = np.round(np.divide(n3_txPkts_diff, ts_diff), 0)

        #n6_rxPkts_diff = np.diff(dfDp["n6_rxPkts"].to_numpy(),prepend=dfDp["n6_rxPkts"][0])
        #dfDp["n6_rxPKTps"] = np.round(np.divide(n6_rxPkts_diff, ts_diff), 0)

        #n6_txPkts_diff = np.diff(dfDp["n6_txPkts"].to_numpy(),prepend=dfDp["n6_txPkts"][0])
        #dfDp["n6_txPKTps"] = np.round(np.divide(n6_txPkts_diff, ts_diff), 0)

        if "sgi_rxPkts" in dfDp:
            sgi_rxPkts_diff = np.diff(dfDp["sgi_rxPkts"].to_numpy(),prepend=dfDp["sgi_rxPkts"][0])
            dfDp["sgi_rxPKTps"] = np.round(np.divide(sgi_rxPkts_diff, ts_diff), 0)
            lstColToDel.append("sgi_rxPkts")
        if "sgi_txPkts" in dfDp:
            sgi_txPkts_diff = np.diff(dfDp["sgi_txPkts"].to_numpy(),prepend=dfDp["sgi_txPkts"][0])
            dfDp["sgi_txPKTps"] = np.round(np.divide(sgi_txPkts_diff, ts_diff), 0)
            lstColToDel.append("sgi_txPkts")

        lstColToDel.append("n3_rxPkts")
        lstColToDel.append("n3_txPkts")
        #lstColToDel.append("n6_rxPkts")
        #lstColToDel.append("n6_txPkts")

        df = dfDp.drop(columns=lstColToDel)
        return df
    except Exception as exc:
        print(exc)
        for k,v in dicDpUsage.items():
            print(f"{k} > {len(v)}")
# }}}

# {{{ extract_transform_gNB_usage(vmFh,seqTimestampMinUtc)
def extract_transform_gNB_usage(vmFh,seqTimestampMinUtc):

    dicUpMinUsage = {
        "utc_timestamp_min": [],
        "dlMBytes":[],
        "dlPktCnt":[],
        "ulMBytes":[],
        "ulPktCnt":[],
        "ueTunnelCnt":[],
        "gnbCnt":[],
    }

    rdb5 = redis.StrictRedis(host=REDIS_SVC_IP,port=REDIS_SVC_PORT,db=REDIS_DBNUM_CMDRES_JSON)
    for t3 in seqTimestampMinUtc:

        r34 = rdb5.get(f"{vmFh}-{t3}")
        if r34:
            try:
                dic34 = json.loads(r34.decode('UTF-8'))
                dicUpMinUsage["dlMBytes"].append( round(dic34["rxBytes"]/1024./1024., 2))
                dicUpMinUsage["dlPktCnt"].append( dic34["rxPkts"])

                dicUpMinUsage["ulMBytes"].append( round(dic34["txBytes"]/1024./1024., 2))
                dicUpMinUsage["ulPktCnt"].append( dic34["txPkts"])
                dicUpMinUsage["ueTunnelCnt"].append( dic34.get("numTunnels",NDV) )
                dicUpMinUsage["gnbCnt"].append( dic34.get("numGnb",NDV) )

                dicUpMinUsage["utc_timestamp_min"].append(t3)
            except:
                import sys, traceback
                print(f"{sys.exc_info()}, {traceback.format_exc()}")
                print(r34)
                rdb5.delete(f"{vmFh}-{t3}")
                pass

    if len(dicUpMinUsage["utc_timestamp_min"]) > 0:
        df = pd.DataFrame(dicUpMinUsage)

        df["utc_timestamp_min"] = pd.to_datetime(df["utc_timestamp_min"])
        tsary = pd.to_datetime(df["utc_timestamp_min"]).to_numpy()
        ts_diff =  np.diff(tsary,prepend=tsary[0])/np.timedelta64(1,'s')
        #df["ts_diff"] = np.diff(tsary,prepend=tsary[0])/np.timedelta64(1,'s')
        dlMB = np.diff(df["dlMBytes"].to_numpy(),prepend=df["dlMBytes"][0])
        dlMBps = np.round(np.divide(dlMB,ts_diff),2)
        df["dlMBps"] = dlMBps

        dlPktCnt = np.diff(df["dlPktCnt"].to_numpy(),prepend=df["dlPktCnt"][0])
        dlPktCnt = np.round(np.divide(dlPktCnt,ts_diff))
        df["dlPKTps"] = dlPktCnt

        ulMB = np.diff(df["ulMBytes"].to_numpy(),prepend=df["ulMBytes"][0])
        ulMBps = np.round(np.divide(ulMB,ts_diff),2)
        df["ulMBps"] = ulMBps

        ulPktCnt = np.diff(df["ulPktCnt"].to_numpy(),prepend=df["ulPktCnt"][0])
        ulPktCnt = np.round(np.divide(ulPktCnt,ts_diff))
        df["ulPKTps"] = ulPktCnt

        df = df.drop(columns=["dlPktCnt","ulPktCnt"])

        df.set_index(["utc_timestamp_min"])

        return df
# }}}


# transform_to_hourly(df1) to return hourly timestamp dataframe
def transform_to_hourly(df1):
    df1.set_index("utc_timestamp_min")
    every60min = [i for i in range(0, len(df1["utc_timestamp_min"]) , 60)]
    dfHourly = df1.iloc[every60min]

    bgn = dfHourly["utc_timestamp_min"][0]
    end = dfHourly["utc_timestamp_min"].iloc[-1]
    #print(f"{bgn.strftime('%m%d')} => {end}, {end-bgn}")

    return dfHourly,bgn,end

def visualize_nf_usage(dfPv,vmDut,outfn="/tmp/fgc-NF-usage.png"):

    dfHourly,bgn,end = transform_to_hourly(dfPv)
    figTitle = f"Dut Ataya CP-fgc-NF @{vmDut}: {bgn.strftime('%b %d')} .. {end.strftime('%b %d')} ({end-bgn})"

    df1 = dfHourly[["utc_timestamp_min","Mem_amfctrl","Mem_smfctrl","Mem_upfcctrl","Mem_ausfctrl","Mem_udmctrl"]]
    #print(df1)

    df2 = dfHourly[["utc_timestamp_min","Pid_amfctrl","Pid_smfctrl","Pid_upfcctrl","Pid_ausfctrl","Pid_udmctrl"]]
    #print(df2)

    #define subplot layout
    fig, axes = plt.subplots(nrows=2, ncols=1)

    #add DataFrames to subplots
    df1.plot(ax=axes[0],x="utc_timestamp_min",title=figTitle)
    df2.plot(ax=axes[1],x="utc_timestamp_min")
    plt.savefig(outfn)

def visualize_gNB_usage(dfGnbUsage,outfn="/tmp/gNB-usage.png"):
    """
    ref. https://www.statology.org/pandas-subplots/
    """
    dfHourly,bgn,end = transform_to_hourly(dfGnbUsage)
    df1 = dfHourly[["utc_timestamp_min","dlMBps", "ulMBps"]]
    df2 = dfHourly[["utc_timestamp_min","gnbCnt", "ueTunnelCnt"]]

    figTitle = f"{bgn.strftime('%b %d')} => {end.strftime('%b %d')} ({end-bgn})"

    #define subplot layout
    fig, axes = plt.subplots(nrows=2, ncols=1)

    #add DataFrames to subplots
    df1.plot(ax=axes[0],x="utc_timestamp_min",title=figTitle)
    df2.plot(ax=axes[1],x="utc_timestamp_min")
    plt.savefig(outfn)

def visualize_dp_usage(dfDpUsage,vmDut,outfn="/tmp/DP-usage.png"):

    dfHourly,bgn,end = transform_to_hourly(dfDpUsage)
    figTitle = f"5GC DP @{vmDut}: {bgn.strftime('%b %d')} .. {end.strftime('%b %d')} ({end-bgn})"

    df1 = dfHourly[["utc_timestamp_min","n3_rxMBps", "n3_txMBps"]] #"n6_rxMBps", "n6_txMBps"] ]
    df2 = dfHourly[["utc_timestamp_min","n3_rxPKTps", "n3_txPKTps"]] #"n6_rxPKTps", "n6_txPKTps"] ]

    #define subplot layout
    fig, axes = plt.subplots(nrows=2, ncols=1)

    #add DataFrames to subplots
    df1.plot(ax=axes[0],x="utc_timestamp_min",title=figTitle)
    df2.plot(ax=axes[1],x="utc_timestamp_min")
    plt.savefig(outfn)

def visualize_pv_usage(dfPv,vmDut,outfn="/tmp/PV-usage.png"):

    dfHourly,bgn,end = transform_to_hourly(dfPv)
    figTitle = f"Dut Ataya DATA @{vmDut}: {bgn.strftime('%b %d')} .. {end.strftime('%b %d')} ({end-bgn})"

    df1 = dfHourly[["utc_timestamp_min","loki","influxdb2","rmq","prom1","mongod","redis","elasticsearch"]]
    #print(df1)
    #add DataFrames to subplots
    df1.plot(x="utc_timestamp_min",title=figTitle)
    plt.savefig(outfn)


def store_plotted_fig(fil, remote_path="/home/vm10131/rsyncSrc"):

    import paramiko
    from paramiko import SSHClient
    from scp import SCPClient

    # TODO: hard-coded temprary storage for viewing
    hostname = "10.22.101.31"
    username = "root"
    password = "vm10131"

    ssh2 = SSHClient()
    ssh2.load_system_host_keys()
    ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh2.connect(hostname=hostname,
                username=username,
                password=password)
    # SCPCLient takes a paramiko transport as its only argument
    scpcli = SCPClient(ssh2.get_transport())
    scpcli.put(fil, remote_path)
    scpcli.close()
