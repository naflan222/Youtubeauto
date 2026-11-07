"""Original vector-like drawings. Logical canvas 540x960; FFmpeg scales to 1080p."""
import math
from PIL import Image, ImageDraw, ImageFont

INK = '#213c50'
TEAL = '#157f79'
PAPER = '#fffdf5'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def font(size, bold=True):
    return ImageFont.truetype(FONT if bold else REGULAR, size)


def lines_for(text, size=25, max_width=410):
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    lines, line = [], ''
    for word in text.split():
        proposed = (line + ' ' + word).strip()
        if draw.textlength(proposed, font=font(size)) > max_width:
            if not line:
                raise ValueError('Unbreakable caption word')
            lines.append(line)
            line = word
        else:
            line = proposed
    if line:
        lines.append(line)
    return lines


def caption_layout(text):
    for size in range(25, 19, -1):
        lines = lines_for(text, size)
        if len(lines) <= 3:
            return lines, size
    raise ValueError('Caption exceeds three readable mobile lines')


def centered(draw, text, y, size, color=INK):
    draw.text((270, y), text, font=font(size), fill=color, anchor='mt')


def star_points(x, y, radius):
    return [(x + math.cos(-math.pi/2+i*math.pi/5)*radius*(1 if i%2==0 else .45), y + math.sin(-math.pi/2+i*math.pi/5)*radius*(1 if i%2==0 else .45)) for i in range(10)]


def character(draw, x, y, t, turtle=False, scale=1):
    def e(box, fill, outline=None, width=2):
        box = [x + box[0]*scale, y + box[1]*scale, x + box[2]*scale, y + box[3]*scale]
        draw.ellipse(box, fill=fill, outline=outline, width=width)
    if turtle:
        e((-43,-5,43,60), '#6ca77c', INK)
        e((-34,4,34,52), '#c8df92', INK)
        for dx in [-18, 15]:
            draw.line((x+dx*scale,y+10*scale,x+(dx+8)*scale,y+44*scale), fill='#6ca77c',width=3)
        e((-38,43,-9,67), '#5eaa91', INK)
        e((12,43,43,67), '#5eaa91', INK)
        e((-31,-47,31,12), '#7cc8a8', INK)
    else:
        e((-40,-86,-11,-15), '#f7e5cf', INK)
        e((9,-91,37,-15), '#f7e5cf', INK)
        e((-32,-74,-19,-29), '#e9a9b1')
        e((17,-80,29,-29), '#e9a9b1')
        e((-38,-1,38,61), '#f7e5cf', INK)
        e((-28,8,28,53), '#fff8eb')
        e((-43,-52,43,15), '#f7e5cf', INK)
        e((-46,44,-4,65), '#f7e5cf', INK)
        e((6,44,48,65), '#f7e5cf', INK)
        e((26,0,51,23), '#f7e5cf', INK)
        draw.rounded_rectangle((x-24*scale,y+3*scale,x+24*scale,y+17*scale),radius=4,fill='#ea855f')
    blink = math.sin(t * 2.1) > .99
    for dx in [-13,13]:
        if blink:
            draw.line((x+(dx-4)*scale,y-23*scale,x+(dx+4)*scale,y-23*scale),fill=INK,width=2)
        else:
            e((dx-3,-28,dx+3,-19),INK)
    e((-28,-17,-17,-10),'#e9a9b1')
    e((17,-17,28,-10),'#e9a9b1')
    draw.arc((x-9*scale,y-22*scale,x+9*scale,y-4*scale),0,180,fill=INK,width=2)


def prop(draw, kind, x, y, size=65, t=0, color=None):
    s=size
    def ellipse(box, fill, outline=None, width=2):
        draw.ellipse((x+box[0]*s,y+box[1]*s,x+box[2]*s,y+box[3]*s),fill=fill,outline=outline,width=width)
    def poly(points, fill, outline=INK):
        draw.polygon([(x+a*s,y+b*s) for a,b in points],fill=fill)
        if outline: draw.line([(x+a*s,y+b*s) for a,b in points+[points[0]]],fill=outline,width=2)
    if kind == 'star':
        draw.polygon(star_points(x,y,s*.78),fill=color or '#f4c759',outline=INK,width=2)
    elif kind in ['circle','pebble','apple','seed','eggs']:
        c = color or {'circle':'#65b5cd','pebble':'#a2b4b5','apple':'#ec756e','seed':'#b07d50','eggs':'#e6efba'}[kind]
        ellipse((-.65,-.65,.65,.65),c,INK)
        if kind=='apple':
            draw.line((x,y-s*.62,x+s*.1,y-s*.95),fill='#7c5a3b',width=5)
            ellipse((.05,-.95,.5,-.7),'#78ac76')
    elif kind == 'square':
        draw.rounded_rectangle((x-.65*s,y-.65*s,x+.65*s,y+.65*s),radius=3,fill=color or '#e9a0a5',outline=INK,width=2)
    elif kind=='triangle':
        poly([(0,-.75),(.8,.65),(-.8,.65)],color or '#e9b355')
    elif kind in ['flower','flowers']:
        draw.line((x,y,x,y+s),fill='#559e70',width=5)
        ellipse((-.65,.35,-.05,.65),'#7aaf77')
        for angle in range(0,360,72):
            cx=x+math.cos(math.radians(angle))*s*.4; cy=y+math.sin(math.radians(angle))*s*.4
            draw.ellipse((cx-s*.32,cy-s*.32,cx+s*.32,cy+s*.32),fill=color or '#edaaa4',outline=INK,width=2)
        ellipse((-.24,-.24,.24,.24),'#f7cb55',INK)
    elif kind=='carrot':
        poly([(-.4,-.5),(.4,-.5),(0,.85)],'#ed9752')
        for dx in [-.4,0,.4]:
            draw.line((x,y-.45*s,x+dx*s,y-.95*s),fill='#60a877',width=6)
        draw.line((x-.16*s,y-.1*s,x+.12*s,y-.05*s),fill='#b96832',width=2)
    elif kind in ['leaf','sprout','roots','soil','water']:
        if kind in ['soil','sprout','roots']:
            draw.rounded_rectangle((x-s,y+s*.3,x+s,y+s),radius=10,fill='#b58b67')
            for dx in [-.4,0,.4]:
                draw.line((x,y+s*.4,x+dx*s,y+s*.9),fill='#f5d59e',width=3)
        if kind in ['leaf','sprout','roots']:
            draw.line((x,y+s*.5,x,y-s*.5),fill='#45855e',width=6)
            ellipse((-.9,-.6,0,0),'#6cb981',INK)
            ellipse((0,-.8,.9,-.2),'#8acb8a',INK)
        if kind=='water':
            poly([(0,-1),(.6,.1),(.4,.7),(-.4,.7),(-.6,.1)],'#70b9d6')
    elif kind in ['tree','cloud','rain','rainbow','pond','picnic']:
        if kind=='tree':
            draw.rounded_rectangle((x-.15*s,y-.1*s,x+.15*s,y+s),radius=4,fill='#ac7954')
            ellipse((-1,-1,1,.35),'#68ad80',INK)
            ellipse((-.7,-1.4,.55,-.15),'#8cc493',INK)
        elif kind=='cloud' or kind=='rain':
            for dx,dy in [(-.55,0),(0,-.2),(.55,0)]: ellipse((dx-.55,dy-.45,dx+.55,dy+.45),'#fffdf5','#8bb0c6')
            if kind=='rain':
                for i in range(5):
                    dx=-.8+i*.4; yy=.6+((t*.5+i*.2)%.6)
                    draw.line((x+dx*s,y+yy*s,x+(dx-.08)*s,y+(yy+.2)*s),fill='#6bacc9',width=4)
        elif kind=='rainbow':
            for i,c in enumerate(['#e78983','#efaf6a','#edcf68','#87b58e','#70b4c9','#9d98c6']):
                r=s*(1.2-i*.11)
                draw.arc((x-r,y-r,x+r,y+r),180,360,fill=c,width=max(3,int(s*.11)))
        elif kind=='pond':
            ellipse((-1.6,-.5,1.6,.7),'#97cfdf','#4e9ebd')
            for i in range(3):
                draw.arc((x-s+i*14,y-s*.2+i*8,x+s-i*10,y+s*.4+i*8),0,160,fill='#d4edf0',width=2)
        else:
            poly([(-1,-.7),(.9,-.7),(1.3,.7),(-1.3,.7)],'#eb9e9b')
            for dx in [-.6,0,.6]:draw.line((x+dx*s,y-.6*s,x+(dx+.2)*s,y+.6*s),fill='#fff3d9',width=5)
            prop(draw,'apple',x-s*.45,y-s*.15,s*.35)
            prop(draw,'carrot',x+s*.4,y,s*.35)
    elif kind in ['sun','moon','earth']:
        ellipse((-.8,-.8,.8,.8),{'sun':'#f5ca5f','moon':'#f5e9bb','earth':'#71b7d1'}[kind],INK)
        if kind=='sun':
            for a in range(0,360,45):
                c=math.cos(math.radians(a));v=math.sin(math.radians(a))
                draw.line((x+c*s,y+v*s,x+c*s*1.2,y+v*s*1.2),fill='#e0ab3d',width=4)
        if kind=='moon':
            for dx,dy,r in [(-.3,-.2,.18),(.2,.3,.22),(.3,-.4,.12)]:ellipse((dx-r,dy-r,dx+r,dy+r),'#dfd5aa')
        if kind=='earth':
            poly([(-.5,-.5),(-.1,-.65),(.2,-.3),(-.1,.1),(-.45,0)],'#80b97c',None)
            poly([(.2,.15),(.65,.1),(.45,.6),(.05,.45)],'#80b97c',None)
    elif kind in ['butterfly','bee','bird','frog','tadpole','turtle']:
        if kind=='turtle':
            character(draw,x,y,t,turtle=True,scale=s/55)
        elif kind=='butterfly':
            for dx in [-.65,.65]:
                ellipse((dx-.5,-.9,dx+.5,.2),'#c3a6d5',INK)
                ellipse((dx-.4,-.05,dx+.4,.7),'#e8b1c0',INK)
            # Three legs on each side, deliberately visible in the educational drawing.
            for dy in [-.25,.1,.45]:
                for sign in [-1,1]:draw.line((x+sign*s*.1,y+dy*s,x+sign*s*.65,y+(dy+.2)*s),fill=INK,width=3)
            ellipse((-.17,-.75,.17,.65),'#6c685d',INK)
        elif kind=='bee':
            ellipse((-.5,-.9,.1,-.1),'#d6edf2',INK);ellipse((0,-.9,.6,-.1),'#d6edf2',INK)
            ellipse((-.9,-.4,.9,.5),'#f3cc61',INK)
            for dx in [-.3,.15,.5]:draw.line((x+dx*s,y-.3*s,x+dx*s,y+.4*s),fill=INK,width=5)
        elif kind=='bird':
            ellipse((-.75,-.6,.7,.65),'#73b4c8',INK)
            ellipse((-.6,-.1,.2,.4),'#408aab',INK)
            poly([(.6,-.4),(1,-.1),(.65,.05)],'#e8b45c')
            ellipse((.26,-.4,.37,-.28),INK)
        elif kind=='frog':
            ellipse((-.8,-.3,.8,.65),'#87bd83',INK)
            for dx in [-.45,.45]:
                ellipse((dx-.25,-.6,dx+.25,-.1),'#87bd83',INK)
                ellipse((dx-.08,-.43,dx+.08,-.27),INK)
            draw.arc((x-s*.35,y-s*.2,x+s*.35,y+s*.35),0,180,fill=INK,width=2)
        else:
            ellipse((-.75,-.4,.05,.4),'#728e87',INK)
            poly([(-.05,-.2),(1,.0),(-.05,.2)],'#728e87')
    else:
        raise ValueError(f'Unknown visual: {kind}')


def scene_props(draw, visual, t, progress=0):
    kind, _, count = visual.partition(':')
    if kind=='reveal-flowers':
        scene_props(draw,'flower:1' if progress<.5 else 'flower:5',t)
    elif count:
        n = int(count)
        if n == 0:
            if kind=='star':
                draw.rounded_rectangle((145,325,395,510),radius=18,fill='#dce8f0',outline=INK,width=2)
                prop(draw,'star',270,420,55,t)
            else:
                prop(draw,'picnic',270,435,110,t)
        else:
            positions = {1:[(270,415)],2:[(190,415),(350,415)],3:[(145,415),(270,415),(395,415)],4:[(190,355),(350,355),(190,490),(350,490)],5:[(145,355),(270,355),(395,355),(205,485),(335,485)]}[n]
            for i,(x,y) in enumerate(positions):
                prop(draw,kind,x,y+math.sin(t*1.6+i)*3,48 if n>=3 else 65,t)
            centered(draw,str(n),575,34,TEAL)
    elif kind in ['two-circle-sizes','two-square-sizes']:
        shape='circle' if 'circle' in kind else 'square'
        prop(draw,shape,180,420,85,t)
        prop(draw,shape,365,420,40,t)
    elif kind in ['circles-mixed','sorted-colors']:
        for i in range(6):
            if kind=='sorted-colors':
                x=175 if i<3 else 365; y=335+(i%3)*85
                color='#ed8e8c' if i<3 else '#6caacb'
            else:
                x=150+(i%3)*120; y=375+(i//3)*110
                color='#ed8e8c' if i%2==0 else '#6caacb'
            prop(draw,'circle',x,y,36,t,color)
    elif kind in ['mixed','puzzle-shapes','sorted','circles-red','circles-blue','sizes']:
        kinds = ['circle','square','triangle']
        if kind in ['circles-red','circles-blue','sizes']: kinds=['circle']*3
        for i,k in enumerate(kinds):
            c = ('#ed8e8c' if kind=='circles-red' else '#6caacb') if kind.startswith('circles-') else None
            prop(draw,k,145+i*125,420,35+i*20 if kind=='sizes' else 46,t,c)
    elif kind in ['pattern','pattern-question']:
        for i in range(5):
            if i==4 and kind=='pattern-question':draw.text((410,420),'?',font=font(42),fill=INK,anchor='mm')
            else:prop(draw,'circle' if i%2==0 else 'star',130+i*70,420,29,t)
    elif kind=='compare-flowers':
        for i in range(2):prop(draw,'flower',145+i*70,350,29,t)
        for i in range(4):prop(draw,'flower',135+i*90,485,29,t)
        centered(draw,'2     and     4',580,26,TEAL)
    elif kind.startswith('paint-'):
        colors={'paint-yellow':['#f4d365'],'paint-blue':['#73b5cf'],'paint-mix':['#f4d365','#73b5cf','#8cbd79']}[kind]
        for i,c in enumerate(colors):prop(draw,'circle',270+(i-(len(colors)-1)/2)*110,425,45,t,c)
    elif kind in ['sun-moon','sun-earth']:
        prop(draw,'sun',155,410,55,t)
        draw.line((225,410,320,410),fill='#d7b567',width=4)
        draw.polygon([(325,410),(311,401),(311,419)],fill='#d7b567')
        prop(draw,'moon' if kind=='sun-moon' else 'earth',390,410,60,t)
    else:
        prop(draw,kind,270,420+math.sin(t*1.5)*4,102,t)


def frame(script, timeline, t):
    index = next((i for i,c in enumerate(timeline) if t<c['end']),len(timeline)-1)
    current=timeline[index]
    image=Image.new('RGB',(540,960),'#e8f3f3'); draw=ImageDraw.Draw(image)
    draw.ellipse((-230,590,650,1050),fill='#d4e7cf')
    draw.ellipse((200,620,850,1100),fill='#c5ddbc')
    # Keep the entire content inside the central mobile safe area.
    centered(draw,'PIP & TILLY',66,15,TEAL)
    title=lines_for(script['title'],29,420)
    for i,line in enumerate(title): centered(draw,line,100+i*37,29)
    draw.rounded_rectangle((44,229,496,626),radius=34,fill=PAPER,outline='#c4dcd8',width=2)
    centered(draw,f"{script['theme'].upper()}  /  {index+1} OF {len(timeline)}",250,13,TEAL)
    # A short ease-in moves the artwork gently rather than flashing or cutting to black.
    local=t-current['start']
    scene_props(draw,current['visual'],local,local/(current['end']-current['start']))
    character(draw,145+math.sin(t*.65)*7,700+math.sin(t*1.8)*2,t,scale=.75)
    character(draw,390+math.sin(t*.55+1)*6,700+math.sin(t*1.4)*2,t,turtle=True,scale=.75)
    lines,size=caption_layout(current['text'])
    draw.rounded_rectangle((44,768,496,892),radius=22,fill=PAPER,outline='#c4dcd8',width=2)
    height=len(lines)*(size+7)
    top=830-height/2
    for i,line in enumerate(lines):centered(draw,line,top+i*(size+7),size)
    for i in range(len(timeline)):
        draw.ellipse((239+i*14,917,245+i*14,923),fill=TEAL if i<=index else '#a5c8bf')
    return image
