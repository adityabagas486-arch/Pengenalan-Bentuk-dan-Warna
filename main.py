"""Buka kamera: python main.py. Tidak memerlukan klik, palette, atau dataset."""
import argparse,json,sys,time
from pathlib import Path
import cv2
import numpy as np
from detector import Detector,Stabilizer,draw,serializable
BASE=Path(__file__).resolve().parent
TITLE='Bentuk dan Warna - OTOMATIS v3'


def read_image(path):
    raw=np.fromfile(str(path),dtype=np.uint8)
    return cv2.imdecode(raw,cv2.IMREAD_COLOR)


def write_image(path,im):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    ok,buf=cv2.imencode('.png',im)
    if not ok:raise RuntimeError('Gagal membuat gambar PNG.')
    buf.tofile(str(path))


def fit_image(im,width=720):
    h,w=im.shape[:2]
    if w>width:return cv2.resize(im,(width,round(h*width/w)),interpolation=cv2.INTER_AREA)
    return im


def open_camera(index):
    cap=cv2.VideoCapture(index,cv2.CAP_DSHOW) if sys.platform=='win32' else cv2.VideoCapture(index)
    if not cap.isOpened():cap.release();cap=cv2.VideoCapture(index)
    if not cap.isOpened():cap.release();raise RuntimeError('Kamera tidak terbuka. Tutup Zoom/Meet lalu coba python main.py --camera 1')
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,640);cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480);return cap


def screen(raw,detections,fps,recording=False):
    im=draw(raw,detections);H,W=im.shape[:2];panel=np.full((135,W,3),(40,30,24),np.uint8)
    if detections:
        d=detections[0];shape=d['shape'];col=d['color']+(' (perkiraan)' if d['uncertain_color'] else '')
        cv2.putText(panel,shape,(18,36),0,.85,(255,255,255),2,cv2.LINE_AA)
        cv2.putText(panel,col,(18,68),0,.70,(110,235,180),2,cv2.LINE_AA)
    else:
        cv2.putText(panel,'Tunjukkan bendamu',(18,36),0,.80,(255,255,255),2,cv2.LINE_AA)
        cv2.putText(panel,'Mencari bentuk...',(18,67),0,.56,(190,210,220),1,cv2.LINE_AA)
    cv2.putText(panel,'Deteksi otomatis - tidak perlu klik',(18,96),0,.47,(210,220,225),1,cv2.LINE_AA)
    cv2.putText(panel,f'S: foto | R: rekam | Q: keluar | {fps:.1f} FPS',(18,121),0,.44,(210,220,225),1,cv2.LINE_AA)
    if recording:cv2.circle(panel,(W-22,22),7,(0,0,255),-1)
    return np.vstack([im,panel])


def main():
    p=argparse.ArgumentParser(description=TITLE);p.add_argument('--camera',type=int,default=0)
    p.add_argument('--image',type=Path);p.add_argument('--video',type=Path)
    p.add_argument('--output',type=Path,default=BASE/'hasil/output.png')
    p.add_argument('--max-objects',type=int,default=1);p.add_argument('--min-area-ratio',type=float,default=.006)
    a=p.parse_args()
    if not 1<=a.max_objects<=10:p.error('--max-objects harus 1..10')
    if not 0<a.min_area_ratio<.5:p.error('--min-area-ratio harus >0 dan <0.5')
    if a.image and a.video:p.error('Pilih --image atau --video, jangan keduanya.')
    cv2.setNumThreads(2);detector=Detector(a.max_objects,a.min_area_ratio)
    if a.image:
        raw=read_image(a.image)
        if raw is None:raise RuntimeError('Gambar tidak bisa dibaca.')
        ds=detector.detect(raw);write_image(a.output,draw(raw,ds))
        a.output.with_suffix('.json').write_text(json.dumps(serializable(ds),indent=2),encoding='utf-8')
        print(json.dumps(serializable(ds),indent=2));return
    cap=cv2.VideoCapture(str(a.video)) if a.video else open_camera(a.camera)
    if not cap.isOpened():raise RuntimeError('Video tidak bisa dibuka.')
    stabilizer=Stabilizer();writer=None;record_start=None;record_frames=0;record_path=None
    last=time.perf_counter();fps=0
    try:
        cv2.namedWindow(TITLE,cv2.WINDOW_AUTOSIZE)
        while True:
            ok,raw=cap.read()
            if not ok:
                if a.video:break
                raise RuntimeError('Kamera berhenti mengirim gambar.')
            raw=fit_image(raw);now=time.perf_counter();dt=now-last;last=now
            fps=(.9*fps+.1/max(dt,.001)) if fps else 1/max(dt,.001)
            detections=stabilizer.update(detector.detect(raw),now)
            display=screen(raw,detections,fps,writer is not None);cv2.imshow(TITLE,display)
            if writer:
                # Isi frame mengikuti elapsed time: durasi file mendekati durasi nyata.
                expected=int((now-record_start)*20)+1
                for _ in range(min(40,max(0,expected-record_frames))):writer.write(display);record_frames+=1
            key=cv2.waitKey(1)&255
            if key in (ord('q'),27):break
            if cv2.getWindowProperty(TITLE,cv2.WND_PROP_VISIBLE)<1:break
            if key==ord('s'):
                folder=BASE/'hasil';stem=str(time.time_ns());write_image(folder/(stem+'_input.png'),raw);write_image(folder/(stem+'_output.png'),display)
                (folder/(stem+'.json')).write_text(json.dumps({'version':'automatic-v3','detections':serializable(detections),'fps_display':fps},indent=2),encoding='utf-8');print('Foto tersimpan:',folder)
            if key==ord('r'):
                if writer:writer.release();writer=None;print('Rekaman selesai:',record_path)
                else:
                    folder=BASE/'hasil';folder.mkdir(exist_ok=True);record_path=folder/f'demo_{time.time_ns()}.mp4'
                    writer=cv2.VideoWriter(str(record_path),cv2.VideoWriter_fourcc(*'mp4v'),20,(display.shape[1],display.shape[0]))
                    if not writer.isOpened():writer.release();writer=None;print('Encoder MP4 tidak tersedia; gunakan perekam layar.')
                    else:record_start=now;record_frames=0;print('Rekaman dimulai, tanpa suara.')
    finally:
        if writer:writer.release()
        cap.release();cv2.destroyAllWindows()
if __name__=='__main__':
    try:main()
    except (RuntimeError,cv2.error,OSError) as exc:
        print('\nProgram berhenti:',exc);sys.exit(1)
