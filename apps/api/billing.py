PLANS={
 "free":{"compute_jobs_month":20,"storage_gb":2,"members":3},
 "pro":{"compute_jobs_month":1000,"storage_gb":100,"members":25},
 "enterprise":{"compute_jobs_month":1000000,"storage_gb":10000,"members":10000}
}
def quota(plan:str,usage:dict)->dict:
    limits=PLANS.get(plan,PLANS["free"]);state={}
    for k,limit in limits.items():
        used=float(usage.get(k,0));state[k]={"used":used,"limit":limit,"remaining":max(limit-used,0),"exceeded":used>limit}
    return {"plan":plan,"quota":state,"allowed":not any(x["exceeded"] for x in state.values())}
