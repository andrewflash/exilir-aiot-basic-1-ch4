"""Capture one controlled Exilir session. Example: python rekam_serial.py --port COM7 --subject P01 --session S01 --label walking_normal"""
import argparse, csv, json, math, re, time
from pathlib import Path

HEADER = ['timestamp','accX','accY','accZ','gyroX','gyroY','gyroZ']
def parse_sample(line):
    parts=line.split(',')
    if len(parts)!=7: raise ValueError('Expected 7 numeric columns')
    row=[float(v) for v in parts]
    if not all(math.isfinite(v) for v in row): raise ValueError('Non-finite value')
    return row

def export(rows, stem, meta):
    """Keep baseline in raw CSV; export only activity to the EI-compatible CSV."""
    if len(rows)<2 or rows[0][0]!=0 or any(b[0]<=a[0] for a,b in zip(rows,rows[1:])):
        raise ValueError('Invalid start or non-monotonic timestamps')
    gaps=[b[0]-a[0] for a,b in zip(rows,rows[1:])]
    activity=[r for r in rows if 3000<=r[0]<23000]
    if not activity: raise ValueError('No activity segment')
    raw=stem.with_suffix('.csv'); ei=stem.with_name(stem.name+'.activity').with_suffix('.activity.csv')
    with raw.open('x',newline='') as f:
        w=csv.writer(f);w.writerow(HEADER);w.writerows(rows)
    with ei.open('x',newline='') as f:
        w=csv.writer(f);w.writerow(HEADER[:4]);t0=activity[0][0]
        w.writerows([[round(r[0]-t0,3),*r[1:4]] for r in activity])
    meta.update(samples=len(rows),actual_fs_hz=1000*(len(rows)-1)/(rows[-1][0]-rows[0][0]),
                max_interval_ms=max(gaps),min_interval_ms=min(gaps),
                timing_ok=all(18<=g<=22 for g in gaps),activity_start_ms=3000,activity_end_ms=23000,
                activity_csv_start_raw_ms=activity[0][0],acceleration_unit='m/s2',gyro_unit='rad/s',
                reference_steps=None,raw_csv=raw.name,activity_csv=ei.name)
    with stem.with_suffix('.json').open('x',encoding='utf-8') as f:json.dump(meta,f,indent=2)
    return raw,ei,meta

def main():
    import serial
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',required=True)
    for field in ['subject','session','label']:p.add_argument('--'+field,required=True)
    p.add_argument('--position',default='waist');p.add_argument('--out',default='rekaman')
    a=p.parse_args()
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+',v) for v in [a.subject,a.session,a.label]):p.error('Use letters, digits, _ or - for IDs and label')
    folder=Path(a.out);folder.mkdir(parents=True,exist_ok=True)
    stem=folder/f'{a.label}_{a.subject}_{a.session}'
    if any(folder.glob(stem.name+'.*')):p.error('Session already exists; choose new session ID')
    print('Tutup Serial Monitor. Setelah BEGIN: diam; saat MULAI: aktivitas 20 detik.',flush=True)
    rows=[];begin=False;end=False;next_start=0;deadline=time.monotonic()+60
    with serial.Serial(a.port,115200,timeout=.2) as port:
        time.sleep(2);port.reset_input_buffer()
        while time.monotonic()<deadline:
            if not begin and time.monotonic()>=next_start:
                port.write(b's');next_start=time.monotonic()+1
            line=port.readline().decode('ascii',errors='replace').strip()
            if not line:continue
            if line.startswith('#ERROR'):raise RuntimeError(line)
            if line.startswith('#BEGIN'):
                if begin:raise RuntimeError('Unexpected restart')
                begin=True;print('DIAM 3 DETIK — baseline',flush=True);continue
            if not begin:continue
            if line.startswith('#ACTIVITY'):print('\aMULAI aktivitas dan hitungan manual!',flush=True);continue
            if line.startswith('#END'):
                expected=re.search(r'samples=(\d+)',line)
                if not expected or int(expected[1])!=len(rows):raise RuntimeError('Missing serial samples; discard and repeat')
                end=True;print('\aSELESAI. '+line,flush=True);break
            if line.startswith('#') or line==','.join(HEADER):continue
            rows.append(parse_sample(line))
    if not end:raise RuntimeError('No END within 60s; check board/port, repeat session')
    raw,ei,meta=export(rows,stem,dict(subject=a.subject,session=a.session,label=a.label,position=a.position))
    print(f'Saved {raw} and {ei}; fs={meta["actual_fs_hz"]:.2f} Hz; max dt={meta["max_interval_ms"]:.2f} ms')
    if not meta['timing_ok']:print('PERIKSA TIMING: interval di luar 18–22 ms. Jangan langsung training; periksa atau rekam ulang.')
    print('Isi reference_steps pada JSON sesuai hitungan pengamat (hanya interval aktivitas).')

if __name__=='__main__':main()
