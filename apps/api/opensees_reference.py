from __future__ import annotations
import json,os,shutil,subprocess,tempfile
from pathlib import Path

def _binary():
    return os.getenv("OPENSEES_BIN") or shutil.which("OpenSees") or shutil.which("OpenSeesSP") or shutil.which("OpenSeesMP")

def available()->dict:
    b=_binary();return {"available":bool(b),"binary":b}

def _run(script:str,timeout:int=120)->dict:
    b=_binary()
    if not b:raise RuntimeError("OpenSees executable not found. Set OPENSEES_BIN or install OpenSees.")
    root=tempfile.mkdtemp(prefix="geotect-opensees-");path=Path(root)/"model.tcl";path.write_text(script,encoding="utf-8")
    p=subprocess.run([b,str(path)],cwd=root,capture_output=True,text=True,timeout=timeout)
    files={}
    for f in Path(root).glob("*.out"):
        try:files[f.name]=f.read_text(encoding="utf-8").strip().splitlines()
        except Exception:pass
    return {"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr,"outputs":files,"script":script}

def pm4sand_simple_shear(params:dict,strain_history:list[float],dt:float=.01)->dict:
    """Exact OpenSees PM4Sand reference adapter using SSPquadUP.

    This does not reimplement PM4Sand; it delegates to the OpenSees reference material.
    """
    Dr=float(params["Dr"]);G0=float(params["G0"]);hpo=float(params["hpo"]);Den=float(params.get("Den",1.8))
    patm=float(params.get("patm",101.3));phic=float(params.get("phic",33.0));nu=float(params.get("nu",.3))
    times=" ".join(str(i*dt) for i in range(len(strain_history)))
    vals=" ".join(str(float(x)) for x in strain_history)
    # unit square plane-strain u-p cell; top horizontal displacement imposes shear strain.
    script=f"""
wipe
model basic -ndm 2 -ndf 3
node 1 0 0; node 2 1 0; node 3 1 1; node 4 0 1
fix 1 1 1 0; fix 2 1 1 0; fix 4 0 0 0
nDMaterial PM4Sand 1 {Dr} {G0} {hpo} {Den} {patm} -1 -1 -1 -1 -1 -1 -1 -1 -1 {phic} {nu}
element SSPquadUP 1 1 2 3 4 1 1.0 2.2e6 1.0 1e-8 1e-8 0.6 1e-6
setParameter -value 0 -ele 1 FirstCall 1
updateMaterialStage -material 1 -stage 1
recorder Element -ele 1 -time -file stress.out stress
recorder Element -ele 1 -time -file strain.out strain
pattern Plain 1 "Path -time {{{times}}} -values {{{vals}}} -factor 1.0" {{
    sp 3 1 1.0
}}
constraints Penalty 1e16 1e16
test NormDispIncr 1e-8 50 0
algorithm Newton
numberer RCM
system BandGeneral
integrator LoadControl 1.0
analysis Static
analyze {max(len(strain_history)-1,1)}
wipe
"""
    out=_run(script)
    out["model"]="OpenSees PM4Sand";out["reference_engine"]=True
    return out

def manzari_dafalias_brick(params:dict,accel:list[float]|None=None,dt:float=.01)->dict:
    """OpenSees 3D Manzari-Dafalias reference adapter using SSPbrickUP."""
    p={**{"G0":125,"nu":.05,"e_init":.72,"Mc":1.25,"c":.712,"lambda_c":.019,"e0":.934,"ksi":.7,
          "P_atm":100,"m":.01,"h0":7.05,"ch":.968,"nb":1.1,"A0":.704,"nd":3.5,"z_max":4,"cz":600,"Den":1.8},**params}
    hist=accel or [0.0,0.01,0.0,-0.01,0.0];times=" ".join(str(i*dt) for i in range(len(hist)));vals=" ".join(map(str,hist))
    args=" ".join(str(p[k]) for k in ["G0","nu","e_init","Mc","c","lambda_c","e0","ksi","P_atm","m","h0","ch","nb","A0","nd","z_max","cz","Den"])
    script=f"""
wipe
model basic -ndm 3 -ndf 4
node 1 0 0 0;node 2 1 0 0;node 3 1 1 0;node 4 0 1 0
node 5 0 0 1;node 6 1 0 1;node 7 1 1 1;node 8 0 1 1
foreach n {{1 2 3 4}} {{fix $n 1 1 1 0}}
nDMaterial ManzariDafalias 1 {args}
element SSPbrickUP 1 1 2 3 4 5 6 7 8 1 2.2e6 1.0 1e-8 1e-8 1e-8 {p["e_init"]} 1.5e-9
updateMaterialStage -material 1 -stage 1
recorder Element -ele 1 -time -file stress.out stress
recorder Element -ele 1 -time -file strain.out strain
recorder Node -node 8 -dof 4 -time -file pressure.out vel
pattern UniformExcitation 1 1 -accel "Series -time {{{times}}} -values {{{vals}}} -factor 1.0"
constraints Penalty 1e16 1e16
test NormDispIncr 1e-7 40 0
algorithm Newton
numberer RCM
system BandGeneral
integrator Newmark 0.5 0.25
analysis Transient
analyze {max(len(hist)-1,1)} {dt}
wipe
"""
    out=_run(script);out["model"]="OpenSees ManzariDafalias";out["reference_engine"]=True;return out

def sanisand_ms_brick(params:dict,accel:list[float]|None=None,dt:float=.01)->dict:
    p={**{"G0":100,"nu":.05,"e_init":.72,"Mc":1.27,"c":.712,"lambda_c":.049,"e0":.845,"ksi":.27,"P_atm":101.3,
          "m":.01,"h0":5.95,"ch":1.01,"nb":2.0,"A0":1.06,"nd":1.17,"zeta":.0005,"mu0":260,"beta":1,"Den":1.584,
          "fabric_flag":1,"flow_flag":1,"intScheme":3,"TanType":1,"JacoType":1,"TolF":1e-6,"TolR":1e-6},**params}
    keys=["G0","nu","e_init","Mc","c","lambda_c","e0","ksi","P_atm","m","h0","ch","nb","A0","nd","zeta","mu0","beta","Den","fabric_flag","flow_flag","intScheme","TanType","JacoType","TolF","TolR"]
    args=" ".join(str(p[k]) for k in keys);hist=accel or [0,.01,0,-.01,0];times=" ".join(str(i*dt) for i in range(len(hist)));vals=" ".join(map(str,hist))
    script=f"""
wipe
model basic -ndm 3 -ndf 4
node 1 0 0 0;node 2 1 0 0;node 3 1 1 0;node 4 0 1 0
node 5 0 0 1;node 6 1 0 1;node 7 1 1 1;node 8 0 1 1
foreach n {{1 2 3 4}} {{fix $n 1 1 1 0}}
nDMaterial SAniSandMS 1 {args}
element SSPbrickUP 1 1 2 3 4 5 6 7 8 1 2.2e6 1.0 1e-8 1e-8 1e-8 {p["e_init"]} 1.5e-9
recorder Element -ele 1 -time -file stress.out stress
recorder Element -ele 1 -time -file strain.out strain
pattern UniformExcitation 1 1 -accel "Series -time {{{times}}} -values {{{vals}}} -factor 1.0"
constraints Penalty 1e16 1e16
test NormDispIncr 1e-7 40 0
algorithm Newton
numberer RCM
system BandGeneral
integrator Newmark 0.5 0.25
analysis Transient
analyze {max(len(hist)-1,1)} {dt}
wipe
"""
    out=_run(script);out["model"]="OpenSees SAniSandMS";out["reference_engine"]=True;return out
