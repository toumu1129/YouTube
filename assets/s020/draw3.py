from PIL import Image, ImageDraw, ImageFilter
import math
W,H,S = 1080,1920,2
BG=(27,67,50); BG2=(19,48,36); ACC=(255,214,10); CREAM=(241,245,242)
METAL=(176,186,181); METAL_D=(108,120,114); DARK=(46,54,50); GRASS=(52,110,78)

def canvas():
    im=Image.new("RGB",(W*S,H*S),BG); d=ImageDraw.Draw(im)
    for i in range(240):
        a=i/240; c=tuple(int(BG[k]+(BG2[k]-BG[k])*a) for k in range(3))
        d.rectangle([0,(H*S)-i*3,W*S,(H*S)-i*3+3],fill=c); d.rectangle([0,i*3,W*S,i*3+3],fill=c)
    return im,d
def fin(im,n):
    im.resize((W,H),Image.LANCZOS).save(n,quality=94); print("wrote",n)
def P(*xy): return [(x*S,y*S) for x,y in xy]
def E(d,cx,cy,rx,ry,**k): d.ellipse([(cx-rx)*S,(cy-ry)*S,(cx+rx)*S,(cy+ry)*S],**k)
def bar(d,cx,cy,L,R,ang=0):
    a=math.radians(ang); dx,dy=math.cos(a)*L/2,math.sin(a)*L/2; px,py=-math.sin(a)*R,math.cos(a)*R
    x1,y1,x2,y2=cx-dx,cy-dy,cx+dx,cy+dy
    d.polygon(P((x1+px,y1+py),(x2+px,y2+py),(x2-px,y2-py),(x1-px,y1-py)),fill=METAL_D)
    d.polygon(P((x1+px*.5,y1+py*.5),(x2+px*.5,y2+py*.5),(x2-px*.1,y2-py*.1),(x1-px*.1,y1-py*.1)),fill=METAL)
    E(d,x2,y2,R,R,fill=METAL); E(d,x1,y1,R,R,fill=METAL_D)
def nail(d,x,y,ln,ang,w,col):
    a=math.radians(ang); d.line(P((x,y),(x+math.cos(a)*ln,y+math.sin(a)*ln)),fill=col,width=int(w*S))
    E(d,x,y,w*1.6,w*1.6,fill=col)
def wire(d,pts,w,col): d.line(P(*pts),fill=col,width=int(w*S),joint="curve")

# ══════════════ ③ 草ごと金属を飲み込む
im,d=canvas()
GY=1210
d.rectangle([0,GY*S,W*S,H*S],fill=(22,56,41))
for i in range(0,W*S,24*S):
    d.line([(i,GY*S),(i+6*S,GY*S-(24*S+(i%52)*S))],fill=GRASS,width=6*S)
# 脚（胴より先に描く）
for lx in (455,545,715,805):
    d.rounded_rectangle([(lx-24)*S,950*S,(lx+24)*S,GY*S],radius=22*S,fill=CREAM)
# 尾
wire(d,[(872,748),(910,860),(886,960)],11,CREAM); E(d,886,972,20,26,fill=CREAM)
# 胴
E(d,630,870,278,190,fill=CREAM)
# 首（胴から左下へ）
d.polygon(P((400,772),(488,746),(344,1098),(258,1048)),fill=CREAM)
# 頭＋鼻づら
E(d,242,1088,110,76,fill=CREAM); E(d,168,1140,60,53,fill=CREAM)
E(d,151,1144,14,11,fill=(198,208,201)); E(d,184,1158,14,11,fill=(198,208,201))  # 鼻孔
E(d,278,1046,18,15,fill=DARK)                                                    # 目
E(d,310,1012,46,30,fill=CREAM)                                                   # 耳
wire(d,[(292,1008),(316,952)],13,CREAM)                                         # 角
# ブチ
E(d,700,832,98,70,fill=(212,222,214)); E(d,556,920,68,49,fill=(212,222,214))
# 草に混ざった金属（黄）
nail(d,146,1190,94,-74,11,METAL); wire(d,[(212,1198),(240,1118),(288,1168)],12,METAL)
nail(d,304,1194,78,-102,10,METAL)
# 口→胴 へ落ちる経路
wire(d,[(186,1164),(296,1062),(388,930),(572,872)],15,ACC)
d.polygon(P((630,868),(566,830),(572,912)),fill=ACC)
fin(im,"03_swallow.jpg")

# ══════════════ ④ 第二胃に磁石が留まる
im,d=canvas()
CX,CY=560,900
# 牛の輪郭（ここが体内だと分かるように薄く）
# 4つの胃（すべて先に描く）
CH=[(-268,30,215,184),(-10,72,252,224),(262,-14,206,184),(410,186,162,146)]
for ox,oy,rx,ry in CH:
    E(d,CX+ox,CY+oy,rx,ry,fill=CREAM,outline=(206,216,208),width=5*S)
# 第二胃を強調（枠のみ。塗りは上書きしない）
E(d,CX-10,CY+72,252,224,outline=ACC,width=13*S)
# 磁石と金属は最後に、必ず前面へ
mx,my=CX-10,CY+82
bar(d,mx,my,330,50,ang=-9)
for x,y,l,a in ((-132,-64,100,112),(18,-72,92,80),(154,-50,86,58)):
    nail(d,mx+x,my+y,l,a,8,DARK)
wire(d,[(mx+64,my+66),(mx+118,my+128),(mx+192,my+82)],11,DARK)
fin(im,"04_stomach.jpg")
