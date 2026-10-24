"""Evaluasi versi otomatis terhadap subset dataset asli, bukan akurasi webcam."""
import argparse,csv,json,time
from collections import Counter,defaultdict
from pathlib import Path
import cv2,numpy as np
from detector import Detector
BASE=Path(__file__).resolve().parent
NORM=lambda s:s.lower().replace(' ','_')
def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset-root',type=Path,default=BASE);a=p.parse_args()
    rows=[r for r in csv.DictReader((a.dataset_root/'manifest.csv').open()) if r['split']=='test'];out=BASE/'hasil_uji';out.mkdir(exist_ok=True)
    cv2.setNumThreads(1);detector=Detector();pred=[];times=[];counts=defaultdict(Counter)
    for r in rows:
        im=cv2.imread(str(a.dataset_root/r['path']))
        if im is None:raise RuntimeError('Gambar gagal dibaca: '+r['path'])
        start=time.perf_counter();ds=detector.detect(im);times.append((time.perf_counter()-start)*1000)
        sh=NORM(ds[0]['shape']) if ds else 'tidak_terdeteksi';co=NORM(ds[0]['color']) if ds else 'tidak_terdeteksi'
        shape_ok=sh==r['shape'];color_ok=co==r['color'];joint=shape_ok and color_ok
        pred.append({'path':r['path'],'shape':r['shape'],'color':r['color'],'pred_shape':sh,'pred_color':co,'shape_ok':int(shape_ok),'color_ok':int(color_ok),'joint_ok':int(joint)})
        counts[r['shape']]['n']+=1;counts[r['shape']]['shape_ok']+=shape_ok;counts[r['shape']]['joint_ok']+=joint
    with (out/'dataset_predictions.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(pred[0]));w.writeheader();w.writerows(pred)
    result={'version':'automatic-v3','n':len(pred),'shape_correct':sum(r['shape_ok'] for r in pred),'color_correct':sum(r['color_ok'] for r in pred),'joint_correct':sum(r['joint_ok'] for r in pred),'per_shape':dict(counts),'median_ms':float(np.median(times)),'p95_ms':float(np.percentile(times,95)),'opencv':cv2.__version__,'scope':'Synthetic dataset subset; previous calibration/test images now used only as evaluation; no training on real objects.'}
    (out/'dataset_metrics.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
