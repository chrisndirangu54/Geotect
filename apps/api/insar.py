from statistics import mean
def analyze_displacement(series:list[dict])->dict:
    if len(series)<2:return {"velocity_mm_day":0.0,"acceleration_flag":False,"samples":len(series)}
    s=sorted(series,key=lambda x:x["day"])
    dt=max(float(s[-1]["day"])-float(s[0]["day"]),1e-9)
    velocity=(float(s[-1]["displacement_mm"])-float(s[0]["displacement_mm"]))/dt
    slopes=[]
    for a,b in zip(s,s[1:]):
        d=max(float(b["day"])-float(a["day"]),1e-9)
        slopes.append((float(b["displacement_mm"])-float(a["displacement_mm"]))/d)
    accel=len(slopes)>=2 and slopes[-1]>mean(slopes[:-1])*1.5 and slopes[-1]>0.5
    return {"velocity_mm_day":round(velocity,4),"recent_velocity_mm_day":round(slopes[-1],4),"acceleration_flag":accel,"samples":len(s)}
