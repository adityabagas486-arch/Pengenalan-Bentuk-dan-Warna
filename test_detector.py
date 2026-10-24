"""Uji terkontrol, bukan bukti webcam. Jalankan python test_detector.py."""
import json,math
from pathlib import Path
import cv2,numpy as np
from detector import Detector,Stabilizer
BASE=Path(__file__).resolve().parent
COLORS={'Putih':(245,245,245),'Biru':(220,40,30),'Kuning':(0,240,240),'Merah':(20,20,240),'Hitam':(15,15,15),'Hijau':(30,180,30),'Coklat':(42,42,165),'Ungu':(128,0,128),'Pink':(203,192,255)}
POLYS={'Segitiga':[[-65,55],[0,-65],[65,55]],'Persegi':[[-55,-55],[55,-55],[55,55],[-55,55]],'Persegi Panjang':[[-85,-50],[85,-50],[85,50],[-85,50]],'Jajar Genjang':[[-60,-45],[80,-45],[50,45],[-90,45]],'Trapesium':[[-45,-60],[45,-60],[80,60],[-80,60]]}
def sample(shape,color,pos=(220,150),angle=0,gain=1):
    im=np.full((320,480,3),115,np.uint8)
    if shape=='Lingkaran':cv2.circle(im,pos,55,COLORS[color],-1)
    else:
        theta=np.deg2rad(angle);rot=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        pts=(np.array(POLYS[shape])@rot.T+pos).astype(np.int32);cv2.fillPoly(im,[pts],COLORS[color])
    return np.clip(im.astype(float)*gain,0,255).astype(np.uint8)
def main():
    detector=Detector();rows=[]
    for shape in list(POLYS)+['Lingkaran']:
        for color in COLORS:
            for pos,angle,gain in [((150,150),0,1),((320,170),20,1),((220,140),-15,.8)]:
                ds=detector.detect(sample(shape,color,pos,angle,gain));ok=len(ds)==1 and ds[0]['shape']==shape and ds[0]['color']==color
                rows.append({'shape':shape,'color':color,'position':pos,'angle':angle,'gain':gain,'passed':ok,'predicted':[(d['shape'],d['color']) for d in ds]})
    controls=[]
    for level in [0,115,255]:
        ds=detector.detect(np.full((320,480,3),level,np.uint8));controls.append({'case':f'blank_{level}','passed':len(ds)==0})
    st=Stabilizer();ds=detector.detect(sample('Persegi','Merah'));first=st.update(ds,0);gone=st.update([],0.1)
    controls.append({'case':'missing_object_hidden','passed':len(first)==1 and gone==[]})
    new=st.update(detector.detect(sample('Persegi','Biru')),0.2)
    controls.append({'case':'color_replacement','passed':len(new)==1 and new[0]['color']=='Biru'})
    motion=[];st=Stabilizer()
    for i,x in enumerate(range(110,371,20)):
        ds=st.update(detector.detect(sample('Persegi Panjang','Merah',(x,160))),i/30)
        motion.append(len(ds)==1 and ds[0]['shape']=='Persegi Panjang' and ds[0]['color']=='Merah')
    controls.append({'case':'translation_14_frames','passed':all(motion)})
    result={'synthetic_total':len(rows),'synthetic_pass':sum(x['passed'] for x in rows),'failures':[x for x in rows if not x['passed']],'controls':controls,'scope':'Generated controlled images; not independent real-camera validation.'}
    (BASE/'hasil_uji').mkdir(exist_ok=True);(BASE/'hasil_uji/controlled_tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if not all(x['passed'] for x in controls):raise SystemExit(1)
if __name__=='__main__':main()
