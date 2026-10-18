#!/usr/bin/env python3
# d016_py_s5r3.py -- D016 public-API point family, Python frontend. Runs against the F4 build
# exported at $EV/trees/F4 (script argument --tree). Options are set at construction time only;
# no SetOptions after solve and no NumBasis change (P06/D004 is out of scope).
# usage: d016_py_s5r3.py --tree <dir> --mode main|ref --out <json>
import sys,os,json,math
def arg(name,default=None):
    if name in sys.argv:
        i=sys.argv.index(name)
        return sys.argv[i+1]
    return default
TREE=arg("--tree"); MODE=arg("--mode","main"); OUT=arg("--out")
if not TREE or not OUT:
    print("usage: d016_py_s5r3.py --tree <dir> --mode main|ref --out <json>"); sys.exit(2)
sys.path.insert(0,TREE)
import S4
FREQ=0.427
def build(basis,nb):
    S=S4.New(Lattice=((1,0),(0,1)),NumBasis=nb)
    opts={"PolarizationDecomposition":True}
    if basis=="Jones": opts["PolarizationBasis"]="Jones"
    elif basis=="NV": opts["PolarizationBasis"]="Normal"
    S.SetOptions(**opts)
    S.SetMaterial(Name="Glass",Epsilon=complex(4.0,0.0))
    S.SetMaterial(Name="Air",Epsilon=complex(1.0,0.0))
    S.AddLayer(Name="Air_above",Thickness=0.0,S4_Material="Air")
    S.AddLayer(Name="Slab",Thickness=0.5,S4_Material="Air")
    S.SetRegionCircle("Slab","Glass",(0.0,0.0),0.25)
    S.AddLayer(Name="Air_below",Thickness=0.0,S4_Material="Air")
    S.SetExcitationPlanewave(IncidenceAngles=(0.0,0.0),sAmplitude=complex(1.0,0.0),pAmplitude=complex(0.0,0.0),Order=0)
    S.SetFrequency(FREQ)
    return S
def call(S,layer="Air_above"):
    try:
        v=S.GetPowerFlux(layer)
        nums=[]
        for z in v: nums+=[z.real,z.imag]
        return {"status":"RETURNED","values":nums,"all_finite":all(math.isfinite(x) for x in nums)}
    except Exception as e:
        return {"status":"EXCEPTION","exc_type":type(e).__name__,"message":str(e)}
res={"S4_file":S4.__file__,"mode":MODE,"tree":TREE,"points":[]}
def add(tag,basis,nb,rec):
    rec.update({"tag":tag,"basis":basis,"NumBasis":nb})
    res["points"].append(rec)
if MODE=="main":
    for nb in (1,2,3,4):
        S=build("VL",nb)
        add("VL_NB%d"%nb,"VL",nb,call(S))
        add("VL_NB%d_RETRY"%nb,"VL",nb,call(S))
    for tag,basis,nb in (("VL_NB5","VL",5),("VL_NB9","VL",9),("Jones_NB1","Jones",1),("NV_NB1","NV",1)):
        add(tag,basis,nb,call(build(basis,nb)))
    add("VL_NB9_RECOVER","VL",9,call(build("VL",9)))
else:
    add("VL_NB9_REF","VL",9,call(build("VL",9)))
with open(OUT,"w") as fh: json.dump(res,fh,indent=1)
print("PY_WROTE",OUT)
print("S4.__file__",S4.__file__)
print("PY_MODE",MODE)
