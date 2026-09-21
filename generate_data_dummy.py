"""Generate reproducible teaching signals, NOT measured human gait or an ML dataset."""
from pathlib import Path
import csv,json,zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analisis_langkah import analyze

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data_dummy'

def save_csv(path,header,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)

def main():
    OUT.mkdir(exist_ok=True)
    t=np.arange(1150)*.02
    cases=[
        ('01_diam',0,0,0,'Diam dengan noise kecil; referensi nol.'),
        ('02_langkah_teratur',2,2.2,40,'Satu siklus buatan mewakili satu langkah: 2 Hz.'),
        ('03_langkah_pelan_lemah',1.2,.9,24,'Amplitudo kecil: threshold awal dapat melewatkan langkah.'),
        ('04_langkah_cepat',3,2.4,60,'Jeda antar siklus sekitar333 ms; coba tau_min=500 ms.'),
        ('05_goyangan_bukan_langkah',2,2.2,0,'Sinyal sengaja identik dengan kasus02, tetapi label aktivitas bukan langkah.'),
        ('06_sensor_miring',2,2.2,40,'Rotasi sumbu tetap60 derajat dari kasus02; magnitude tetap sama.'),
        ('07_amplitudo_berubah',2,2.2,40,'Separuh aktivitas amplitudo0,8, separuh2,2 m/s2.'),
        ('08_sampel_hilang',2,2.2,40,'Kasus02 dengan sampel10,00 sampai10,18 detik dibuang; analyzer harus menolak.'),
    ]
    base_noise=np.random.default_rng(42).normal(0,.035,(len(t),3))
    summary=[];answers=[]
    fig,axs=plt.subplots(4,2,figsize=(15,12),sharex=True,layout='constrained')
    for ax,(name,hz,amp,reference,description) in zip(axs.flat,cases):
        phase=2*np.pi*hz*(t-3)
        envelope=np.where(t>=3,amp,0)
        if name.startswith('07'):envelope=np.where(t<3,0,np.where(t<13,.8,amp))
        xyz=base_noise.copy()
        xyz[:,2]+=9.80665+envelope*np.sin(phase)
        # Small lateral components, without trying to model biomechanics.
        xyz[:,0]+=envelope*.12*np.sin(phase+.4)
        xyz[:,1]+=envelope*.08*np.sin(phase*2)
        if name.startswith('06'):
            angle=np.pi/3
            rotation=np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]])
            xyz=xyz@rotation.T
        # Gyro is intentionally zero: this is an acceleration-only teaching model.
        rows=np.column_stack([np.round(t*1000),xyz,np.zeros((len(t),3))])
        keep=np.ones(len(t),dtype=bool)
        if name.startswith('08'):keep=(t<10)|(t>=10.2)
        rows=rows[keep];tt=t[keep]
        path=OUT/(name+'.csv')
        save_csv(path,['timestamp','accX','accY','accZ','gyroX','gyroY','gyroZ'],np.round(rows,6))
        active=rows[rows[:,0]>=3000,:4].copy();active[:,0]-=3000
        save_csv(OUT/(name+'.activity.csv'),['timestamp','accX','accY','accZ'],active)
        events=(3+(np.arange(reference)+.25)/hz).tolist() if reference else []
        save_csv(OUT/(name+'.events.csv'),['timestamp','event'],[(round(v*1000,3),'synthetic_step') for v in events])
        meta=dict(synthetic=True,source='generate_data_dummy.py; seed42; analytical signal, not sensor recording',
                  scenario=name,description=description,sample_rate_hz=50,baseline_ms=3000,activity_duration_ms=20000,
                  units=dict(timestamp='ms',acceleration='m/s2',gyro='rad/s'),reference_steps=reference,
                  reference_definition='One positive sinusoid maximum per modeled step; not measured foot contact. Goyangan has zero steps by scenario definition.',
                  gyro_note='All zeros, intentionally unmodeled. Do not use to learn gyro behavior.',
                  rows=len(rows),timing_ok=bool(keep.all()),seed=42)
        default=None
        for config,high,interval in [('default',1.2,.3),('threshold_rendah',.6,.3),('jeda_500ms',1.2,.5)]:
            try:
                times,_,filtered,peaks,result=analyze(path,high=high,min_interval=interval)
                predicted=result['predicted_steps']
                error=abs(predicted-reference)
                answer=dict(scenario=name,configuration=config,high=high,min_interval_s=interval,reference=reference,predicted=predicted,
                            error_percent=round(100*error/reference,2) if reference else '',false_steps_per_minute=predicted*3 if not reference else '',status='OK')
                if config=='default':default=(times,filtered,peaks);meta['default_detector']=result
            except ValueError as e:
                answer=dict(scenario=name,configuration=config,high=high,min_interval_s=interval,reference=reference,predicted='',error_percent='',false_steps_per_minute='',status=str(e))
                if config=='default':meta['default_detector_error']=str(e)
            answers.append(answer)
        (OUT/(name+'.metadata.json')).write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
        mag=np.linalg.norm(rows[:,1:4],axis=1)
        if default:
            times,filtered,peaks=default
            ax.plot(times,filtered,lw=1,color='#147d92');ax.scatter(times[peaks],filtered[peaks],s=14,color='#dd6544')
            count=len(peaks)
        else:
            ax.plot(tt,mag-9.80665,lw=1,color='#147d92');ax.axvspan(10,10.2,color='red',alpha=.3);count='ditolak'
        ax.axhline(1.2,color='#dd6544',ls='--',lw=.8);ax.axvspan(0,3,color='gray',alpha=.12)
        ax.set_title(f'{name} | referensi={reference}, detector={count}',fontsize=10)
        ax.set_ylabel('Deviasi magnitude (m/s²)');ax.set_xlabel('Waktu (s)')
        summary.append(dict(scenario=name,reference_steps=reference,predicted_steps_default=count,samples=len(rows),description=description))
    fig.suptitle('DATA SINTETIS — latihan threshold, bukan rekaman langkah manusia',fontsize=17)
    fig.savefig(OUT/'ringkasan_skenario.png',dpi=160);plt.close(fig)
    save_csv(OUT/'ringkasan.csv',summary[0].keys(),[v.values() for v in summary])
    save_csv(OUT/'kunci_eksperimen.csv',answers[0].keys(),[v.values() for v in answers])
    # Verify dataset properties and intended failure examples using the saved CSVs.
    a=np.genfromtxt(OUT/'02_langkah_teratur.csv',delimiter=',',skip_header=1)
    b=np.genfromtxt(OUT/'05_goyangan_bukan_langkah.csv',delimiter=',',skip_header=1)
    c=np.genfromtxt(OUT/'06_sensor_miring.csv',delimiter=',',skip_header=1)
    assert np.array_equal(a,b)
    assert np.allclose(np.linalg.norm(a[:,1:4],axis=1),np.linalg.norm(c[:,1:4],axis=1),atol=2e-6)
    assert summary[0]['predicted_steps_default']==0
    assert summary[1]['predicted_steps_default']==40
    assert summary[2]['predicted_steps_default']<24
    assert summary[4]['predicted_steps_default']>0
    assert summary[7]['predicted_steps_default']=='ditolak'
    for name,*_ in cases:
        d=np.genfromtxt(OUT/(name+'.activity.csv'),delimiter=',',skip_header=1)
        assert d[0,0]==0 and np.isfinite(d).all()
    with zipfile.ZipFile(ROOT.parent/'Data_Dummy_Langkah_Exilir.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.glob('*')):
            if p.is_file():z.write(p,'data_dummy/'+p.name)
        z.write(Path(__file__),'generate_data_dummy.py')
        z.write(ROOT/'analisis_langkah.py','analisis_langkah.py')
        z.write(ROOT/'requirements.txt','requirements.txt')
    print(json.dumps(summary,indent=2,ensure_ascii=False))
    print('PASS: CSV, timing rejection, orientation invariance, deliberate ambiguity, baseline and known counts.')

if __name__=='__main__':main()
