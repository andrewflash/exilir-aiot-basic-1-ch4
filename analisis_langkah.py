"""Plot and evaluate the raw lab CSV. Uses actual timestamps; no automatic resampling."""
import argparse, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def analyze(path,high=1.2,low=.3,min_interval=.3,baseline=3.,duration=20.):
    if high<=low or min_interval<=0 or baseline<=0 or duration<=0:raise ValueError('Invalid parameters')
    d=np.genfromtxt(path,delimiter=',',names=True)
    t=np.atleast_1d(d['timestamp'])/1000
    xyz=np.column_stack([np.atleast_1d(d[k]) for k in ['accX','accY','accZ']])
    if len(t)<5 or not np.isfinite(t).all() or not np.isfinite(xyz).all() or np.any(np.diff(t)<=0):raise ValueError('Invalid data/timestamps')
    if abs(t[0])>.001:raise ValueError('Raw CSV must start at zero')
    dt=np.diff(t)
    if np.any(np.abs(dt-.02)>.0021):raise ValueError('Intervals outside 18–22ms; inspect timing before analysis')
    if t[-1]<baseline+duration-.1:raise ValueError('Recording does not cover requested interval')
    m=np.linalg.norm(xyz,axis=1);g0=float(np.median(m[t<baseline]));q=m-g0
    f=np.array([q[max(0,k-4):k+1].mean() for k in range(len(q))])
    peaks=[];armed=True;last=-np.inf
    for k in range(2,len(t)):
        if f[k]<low:armed=True
        j=k-1
        if not baseline<=t[j]<baseline+duration:continue
        if armed and f[j]>f[j-1] and f[j]>=f[k] and f[j]>high and t[j]-last>=min_interval:
            peaks.append(j);last=t[j];armed=False
    result=dict(predicted_steps=len(peaks),g0_m_s2=g0,high_m_s2=high,low_m_s2=low,
                min_interval_s=min_interval,filter_samples=5,activity_duration_s=duration,
                peak_times_s=[float(t[j]) for j in peaks])
    return t,xyz,f,peaks,result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('csv',type=Path)
    p.add_argument('--high',type=float,default=1.2);p.add_argument('--low',type=float,default=.3)
    p.add_argument('--min-interval',type=float,default=.3);p.add_argument('--reference',type=int)
    a=p.parse_args()
    if a.reference is not None and a.reference<0:p.error('Reference must be >= 0')
    t,xyz,f,peaks,r=analyze(a.csv,a.high,a.low,a.min_interval)
    if a.reference is not None:
        r['reference_steps']=a.reference;r['signed_error']=r['predicted_steps']-a.reference
        r['absolute_error']=abs(r['signed_error'])
        if a.reference:r['relative_error_percent']=100*r['absolute_error']/a.reference
        else:r['false_steps_per_minute']=r['predicted_steps']*60/r['activity_duration_s']
    fig,axs=plt.subplots(2,1,figsize=(12,7),sharex=True,layout='constrained')
    for j,name in enumerate(['ax','ay','az']):axs[0].plot(t,xyz[:,j],label=name)
    axs[0].set_ylabel('Akselerasi (m/s²)');axs[0].legend()
    axs[1].plot(t,f,label='Deviasi magnitude terfilter');axs[1].scatter(t[peaks],f[peaks],label='Kandidat',color='coral')
    axs[1].axhline(a.high,color='red',ls='--',label='T_high');axs[1].axhline(a.low,color='gray',ls=':',label='T_low')
    for ax in axs:ax.axvspan(0,3,color='gray',alpha=.15);ax.axvline(3,color='black',ls=':')
    axs[1].set(xlabel='Waktu sensor (s)',ylabel='m/s²');axs[1].legend()
    fig.suptitle(a.csv.name+' — area abu-abu: baseline')
    prefix=a.csv.with_suffix('');fig.savefig(str(prefix)+'.plot.png',dpi=150)
    Path(str(prefix)+'.hasil.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps(r,indent=2))

if __name__=='__main__':main()
