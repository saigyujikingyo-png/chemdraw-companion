"""Geometry-only radial ports around measured, potentially asymmetric glyphs."""
import math


def atom_ports(center,box,B,extension=0):
    for degrees in range(0,360,30):
        angle=math.radians(degrees);outward=(math.cos(angle),math.sin(angle))
        if box is None:radius=B/6
        else:
            # The centre is an atom anchor, not necessarily the glyph centre.
            # Slab intersection gives the far boundary of the actual label.
            near=-float('inf');far=float('inf')
            for k in (0,1):
                if abs(outward[k])<1e-10:
                    if not box[k]<=center[k]<=box[k+2]:far=-1;break
                else:
                    bounds=sorted(((box[k]-center[k])/outward[k],(box[k+2]-center[k])/outward[k]));near=max(near,bounds[0]);far=min(far,bounds[1])
            if far<max(0,near):continue
            radius=far+B*.14
        visible=tuple(center[k]+radius*outward[k] for k in (0,1))
        endpoint=tuple(visible[k]+extension*outward[k] for k in (0,1))
        yield endpoint,outward,visible
