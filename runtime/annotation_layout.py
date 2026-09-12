"""Reaction-independent fixed-scale row packing and relative electron ports."""
import math


def pack_row(canvas_width,widths,margin,gap):
    if any(w<0 or not math.isfinite(w) for w in widths):raise ValueError('Invalid measured width')
    total=sum(widths)+max(0,len(widths)-1)*gap
    if total>canvas_width-2*margin:raise ValueError('Measured annotation row exceeds fixed canvas')
    x=(canvas_width-total)/2;positions=[]
    for width in widths:positions.append(x);x+=width+gap
    return positions


def annotation_gap(B,head_extension):
    # The control endpoint precedes the visible target by the measured head
    # extension plus B/6; also reserve .22 B curve-to-caption clearance.
    return max(B*.5,head_extension+B*(1/6+.22+.02))


def displacement_curves(donor,acceptor,leaving,leaving_box,B,head_extension=0,obstacles=()):
    """Paired attack/departure geometry relative to a leaving-bond direction.

    The incoming tangent is opposite the leaving substituent, with the two
    curves allocated to opposite sides. No atom ID or molecule name is read.
    """
    dx,dy=leaving[0]-acceptor[0],leaving[1]-acceptor[1];length=math.hypot(dx,dy)
    if length==0:raise ValueError('Degenerate leaving bond')
    u=(dx/length,dy/length);n=(-u[1],u[0])
    add=lambda p,q:(p[0]+q[0],p[1]+q[1]);mul=lambda p,s:(p[0]*s,p[1]*s)
    end=add(acceptor,mul(u,-B/6-head_extension));delta=(end[0]-donor[0],end[1]-donor[1])
    candidates=[]
    for bend in (.8,1.2,1.6,2.0):
        for tangent in (.85,.55,.35):
            curve=[donor,add(add(donor,mul(delta,.25)),mul(n,-B*bend)),add(end,mul(u,-B*tangent)),end]
            minimum=float('inf')
            for step in range(101):
                t=step/100;s=1-t;p=tuple(s**3*curve[0][k]+3*s*s*t*curve[1][k]+3*s*t*t*curve[2][k]+t**3*curve[3][k] for k in (0,1))
                for box in obstacles:minimum=min(minimum,math.hypot(max(box[0]-p[0],0,p[0]-box[2]),max(box[1]-p[1],0,p[1]-box[3])))
            if minimum>=B*.22:candidates.append((bend+tangent*.05,curve))
    if not candidates:raise ValueError('No backside attack route clears measured annotations')
    attack=min(candidates,key=lambda c:c[0])[1]
    middle=((acceptor[0]+leaving[0])/2,(acceptor[1]+leaving[1])/2)
    # Intersection of the leaving-atom glyph box with the outgoing normal,
    # followed by the shared glyph clearance. The box is relative to its atom.
    distances=[]
    for k in (0,1):
        if abs(n[k])>1e-9:distances.append((leaving_box[k+2] if n[k]>0 else leaving_box[k])/n[k])
    radius=min(v for v in distances if v>=0)+B*.12
    target=add(leaving,mul(n,radius+head_extension))
    departure=[middle,add(middle,mul(n,B*.95+head_extension)),add(leaving,mul(n,B*.95+head_extension)),target]
    return attack,departure
