import math
from typing import Iterable

def idw_with_uncertainty(samples: Iterable[tuple[float,float,float]],x:float,y:float,power:float=2.0)->dict:
    rows=list(samples)
    if not rows: return {"estimate":None,"uncertainty":1.0,"support":0}
    weighted=0.0;weight_sum=0.0;distances=[]
    for sx,sy,value in rows:
        d=max(math.hypot(x-sx,y-sy),1e-9);w=1/(d**power)
        weighted+=w*value;weight_sum+=w;distances.append(d)
    estimate=weighted/weight_sum
    spread=sum((v-estimate)**2 for _,_,v in rows)/len(rows)
    proximity=min(distances)
    uncertainty=min(1.0,(math.sqrt(spread)/(abs(estimate)+1e-9))*.6 + min(proximity/1000,1)*.4)
    return {"estimate":estimate,"uncertainty":uncertainty,"confidence":1-uncertainty,"support":len(rows),"method":"IDW screening"}
