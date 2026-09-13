"""Independent, deliberately narrow acyclic SMILES/stereo comparator.

Supports the small H/C/N/O/Br fixtures, single/double bonds, disconnected
components and a noninitial tetrahedral C with one bracket H. Rings, aromatic
atoms, unspecified stereo, and other stereochemical classes fail closed.
Neighbour order and virtual H follow Daylight Theory section 3.3.3:
https://www.daylight.com/dayhtml/doc/theory/theory.smiles.html
This tests preservation of input chirality, not an absolute CIP assignment.
"""
import re


def parse(text):
    text=text.strip();tokens=re.findall(r'\[[^\]]+\]|Br|[HCNO]|[().=\-]',text)
    if ''.join(tokens)!=text:raise ValueError('SMILES outside the independent acyclic checker scope')
    atoms=[];edges={};stack=[];current=None;order=1
    for token in tokens:
        if token=='(':
            if current is None:raise ValueError('Invalid branch')
            stack.append(current);continue
        if token==')':current=stack.pop();continue
        if token=='.':current=None;continue
        if token in ('=','-'):order=2 if token=='=' else 1;continue
        if token.startswith('['):
            match=re.fullmatch(r'(?P<isotope>\d*)(?P<element>Br|[HCNO])(?P<stereo>@@|@)?(?P<h>H\d*)?(?P<charge>[+-]\d*)?(?::\d+)?',token[1:-1])
            if not match:raise ValueError('Unsupported bracket atom')
            values=match.groupdict();h=values['h'];h=(int(h[1:] or 1) if h else 0);charge=values['charge'];charge=(int(charge[1:] or 1)*(1 if charge[0]=='+' else -1)) if charge else 0
            atom={'element':values['element'],'h':h,'charge':charge,'isotope':int(values['isotope'] or 0),'stereo':values['stereo'],'neighbours':[]}
        else:atom={'element':token,'h':None,'charge':0,'isotope':0,'stereo':None,'neighbours':[]}
        i=len(atoms);atoms.append(atom)
        if current is not None:
            atoms[current]['neighbours'].append(i);atom['neighbours'].append(current);edges[frozenset((current,i))]=order
        if atom['stereo']:
            if current is None or atom['element']!='C' or atom['h']!=1:raise ValueError('Unsupported tetrahedral SMILES representation')
            atom['neighbours'].append('H')
        current=i;order=1
    if stack:raise ValueError('Unclosed SMILES branch')
    for i,atom in enumerate(atoms):
        if atom['h'] is None:atom['h']={'H':1,'C':4,'N':3,'O':2,'Br':1}[atom['element']]-sum(v for e,v in edges.items() if i in e)
        if atom['h']<0 or atom['stereo'] and len(atom['neighbours'])!=4:raise ValueError('Invalid atom valence/stereo')
    return atoms,edges


def same_stereo(left,right):
    a,ae=parse(left);b,be=parse(right)
    if len(a)!=len(b) or len(ae)!=len(be):return False
    properties=lambda x:tuple(x[k] for k in ('element','h','charge','isotope'))
    candidates={i:[j for j,y in enumerate(b) if properties(x)==properties(y)] for i,x in enumerate(a)}
    order=sorted(candidates,key=lambda i:len(candidates[i]));matches=[]
    def search(mapping):
        if len(mapping)==len(a):matches.append(dict(mapping));return
        i=order[len(mapping)]
        for j in candidates[i]:
            if j in mapping.values() or any(ae.get(frozenset((i,k)))!=be.get(frozenset((j,v))) for k,v in mapping.items()):continue
            mapping[i]=j;search(mapping);del mapping[i]
    search({})
    for mapping in matches:
        valid=True
        for i,x in enumerate(a):
            y=b[mapping[i]]
            if bool(x['stereo'])!=bool(y['stereo']):valid=False;break
            if not x['stereo']:continue
            target=[mapping[k] if k!='H' else 'H' for k in x['neighbours']];actual=y['neighbours']
            permutation=[actual.index(k) for k in target];odd=sum(permutation[j]>permutation[k] for j in range(4) for k in range(j+1,4))%2
            if (x['stereo']!=y['stereo'])!=bool(odd):valid=False;break
        if valid:return True
    return False
