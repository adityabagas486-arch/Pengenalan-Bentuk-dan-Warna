"""Deteksi bentuk otomatis melalui beberapa mask dan tepi; bukan model terlatih."""
from collections import Counter,deque
import cv2
import numpy as np


def classify_shape(contour):
    area=cv2.contourArea(contour)
    hull=cv2.convexHull(contour);ha=cv2.contourArea(hull)
    if ha<1 or area/ha<.88:return None
    perimeter=cv2.arcLength(hull,True)
    poly=cv2.approxPolyDP(hull,.022*perimeter,True)
    pts=poly[:,0,:].astype(float);n=len(pts)
    if n==3:return 'Segitiga',poly,area/ha
    if n==4:
        edges=np.roll(pts,-1,axis=0)-pts;lens=np.linalg.norm(edges,axis=1)
        if lens.min()<8:return None
        u=edges/lens[:,None]
        right=max(abs(np.dot(u[i],u[(i+1)%4])) for i in range(4))<.20
        balanced=max(lens[0],lens[2])/min(lens[0],lens[2])<1.20 and max(lens[1],lens[3])/min(lens[1],lens[3])<1.20
        if right and balanced:
            a=(lens[0]+lens[2])/2;b=(lens[1]+lens[3])/2
            return ('Persegi' if max(a,b)/min(a,b)<1.15 else 'Persegi Panjang'),poly,area/ha
        par=lambda a,b:abs(a[0]*b[1]-a[1]*b[0])<.16
        p1=par(u[0],u[2]);p2=par(u[1],u[3])
        if p1 and p2:return 'Jajar Genjang',poly,area/ha
        if p1!=p2:return 'Trapesium',poly,area/ha
        return None
    (_, _),radius=cv2.minEnclosingCircle(hull)
    if n>=7 and 4*np.pi*ha/perimeter**2>.83 and ha/(np.pi*radius**2)>.83:
        return 'Lingkaran',hull,area/ha
    return None


def pixel_colors(pixels):
    h,s,v=pixels.T.astype(float)
    ids=np.full(len(h),9,np.uint8)
    # 0..8 target; 9 ambiguous/out-of-target. Pale blue/white inherently ambiguous.
    ids[v<60]=4
    neutral=(s<80)&(v>=110)
    ids[neutral]=0
    chrom=(s>=80)&(v>=60)
    ids[chrom&(h>=90)&(h<130)]=1
    ids[chrom&(h>=22)&(h<36)]=2
    ids[chrom&((h<10)|(h>=175))]=3
    ids[chrom&(h>=36)&(h<90)]=5
    ids[(s>=65)&(v>=60)&(v<185)&(h<22)]=6
    ids[chrom&(h>=130)&(h<175)]=7
    ids[(v>=145)&(s>=35)&(s<160)&((h>=155)|(h<10))]=8
    return ids

NAMES=['Putih','Biru','Kuning','Merah','Hitam','Hijau','Coklat','Ungu','Pink','Warna Belum Pasti']


def color_inside(frame,poly):
    mask=np.zeros(frame.shape[:2],np.uint8);cv2.drawContours(mask,[poly],-1,255,-1)
    x,y,w,h=cv2.boundingRect(poly);k=max(3,int(min(w,h)*.08)|1)
    mask=cv2.erode(mask,np.ones((k,k),np.uint8))
    pix=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)[mask>0]
    if not len(pix):return 'Warna Belum Pasti',False
    ids=pixel_colors(pix);counts=np.bincount(ids,minlength=10);idx=int(counts.argmax())
    fraction=counts[idx]/len(ids)
    if fraction<.45:return 'Multicolor',False
    # Mark low-light/colored-cast white estimate; don't silently claim exact physical color.
    uncertain=idx==0 and (np.median(pix[:,2])<175 or np.median(pix[:,1])>45)
    return NAMES[idx],bool(uncertain)


def masks_for(frame):
    smooth=cv2.GaussianBlur(frame,(5,5),0);hsv=cv2.cvtColor(smooth,cv2.COLOR_BGR2HSV);h,s,v=cv2.split(hsv)
    candidates=[('netral',(s<80)&(v>105)),('gelap',v<65)]
    chrom=(s>=65)&(v>=55)
    for name,cond in [('merah',(h<12)|(h>=170)),('kuning',(h>=12)&(h<36)),('hijau',(h>=36)&(h<90)),('biru',(h>=90)&(h<130)),('ungu',(h>=130)&(h<160)),('pink',(h>=150)|(h<10))]:
        candidates.append((name,chrom&cond))
    for name,cond in candidates:
        mask=cond.astype(np.uint8)*255
        mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
        yield name,mask,cv2.RETR_EXTERNAL
    gray=cv2.cvtColor(smooth,cv2.COLOR_BGR2GRAY)
    for low,high in [(35,100),(70,180)]:
        edges=cv2.Canny(gray,low,high)
        edges=cv2.morphologyEx(edges,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        yield 'tepi',edges,cv2.RETR_LIST


def overlap(a,b):
    x,y,w,h=a;xx,yy,ww,hh=b
    inter=max(0,min(x+w,xx+ww)-max(x,xx))*max(0,min(y+h,yy+hh)-max(y,yy))
    return inter/max(1,w*h+ww*hh-inter),inter/max(1,min(w*h,ww*hh))


class Detector:
    def __init__(self,max_objects=1,min_area_ratio=.006):
        self.max_objects=max_objects;self.min_area_ratio=min_area_ratio
    def detect(self,frame):
        H,W=frame.shape[:2];minimum=max(250,H*W*self.min_area_ratio);items=[]
        for source,mask,mode in masks_for(frame):
            cs,_=cv2.findContours(mask,mode,cv2.CHAIN_APPROX_SIMPLE)
            for c in cs:
                area=cv2.contourArea(c)
                if area<minimum or area>H*W*.85:continue
                x,y,w,h=cv2.boundingRect(c)
                if min(w,h)<20 or x<=1 or y<=1 or x+w>=W-1 or y+h>=H-1:continue
                result=classify_shape(c)
                if result is None:continue
                shape,poly,solidity=result
                # Thin background strips and lamps are not useful teaching objects.
                if max(w,h)/max(1,min(w,h))>5:continue
                center_dist=((x+w/2-W/2)/W)**2+((y+h/2-H/2)/H)**2
                score=area*solidity*(1-.5*center_dist)*(1 if source!='tepi' else .92)
                items.append({'shape':shape,'bbox':[x,y,w,h],'polygon':poly,'area':area,'score':score,'source':source})
        selected=[]
        for d in sorted(items,key=lambda d:d['score'],reverse=True):
            if any(overlap(d['bbox'],s['bbox'])[0]>.40 or overlap(d['bbox'],s['bbox'])[1]>.85 for s in selected):continue
            d['color'],d['uncertain_color']=color_inside(frame,d['polygon']);selected.append(d)
            if len(selected)>=self.max_objects:break
        return selected


class Stabilizer:
    """Match per frame. Hide missing detections immediately; expire tracks after 0.35s."""
    def __init__(self):self.tracks=[];self.next_id=1
    def update(self,detections,now):
        self.tracks=[t for t in self.tracks if now-t['last']<.35];used=set();visible=[]
        for d in detections:
            candidates=[(overlap(t['bbox'],d['bbox'])[0],i,t) for i,t in enumerate(self.tracks) if i not in used]
            best=max(candidates,key=lambda x:x[0]) if candidates else None
            if best and best[0]>.15:
                _,i,t=best;used.add(i)
                # Sudden color replacement must not keep an old label.
                if t['last_color']!=d['color']:t['colors'].clear()
            else:
                t={'id':self.next_id,'bbox':d['bbox'],'shapes':deque(maxlen=5),'colors':deque(maxlen=3),'last_color':d['color']};self.next_id+=1
                self.tracks.append(t);used.add(len(self.tracks)-1)
            t['shapes'].append(d['shape']);t['colors'].append(d['color']);t['last_color']=d['color'];t['last']=now;t['bbox']=d['bbox']
            current=dict(d);current['id']=t['id']
            current['shape']=Counter(t['shapes']).most_common(1)[0][0];current['color']=Counter(t['colors']).most_common(1)[0][0]
            visible.append(current)
        return visible


def draw(frame,detections):
    out=frame.copy()
    for d in detections:
        x,y,w,h=map(int,d['bbox']);cv2.rectangle(out,(x,y),(x+w,y+h),(40,210,90),2)
        label=d['shape']+' '+d['color']+(' (?)' if d['uncertain_color'] else '')
        scale=min(.65,max(.35,out.shape[1]/1000));(tw,th),_=cv2.getTextSize(label,0,scale,2)
        if tw>out.shape[1]-12:scale*= (out.shape[1]-12)/tw;(tw,th),_=cv2.getTextSize(label,0,scale,2)
        tx=max(0,min(x,out.shape[1]-tw-9));ty=max(th+9,y-7)
        cv2.rectangle(out,(tx,ty-th-7),(tx+tw+8,ty+5),(25,35,45),-1)
        cv2.putText(out,label,(tx+4,ty),0,scale,(255,255,255),2,cv2.LINE_AA)
    return out


def serializable(items):
    return [{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in d.items()} for d in items]
