from collections import defaultdict, deque

def propagate_failures(nodes:list[dict],edges:list[dict],failed_ids:list[str])->dict:
    graph=defaultdict(list)
    for e in edges:
        graph[e["from"]].append((e["to"],float(e.get("coupling",1.0))))
    impact={x:1.0 for x in failed_ids};q=deque(failed_ids)
    while q:
        u=q.popleft()
        for v,c in graph[u]:
            candidate=impact[u]*max(0,min(c,1))
            if candidate>impact.get(v,0)+0.01:
                impact[v]=candidate;q.append(v)
    ranked=sorted(({"id":n["id"],"impact":round(impact.get(n["id"],0),3),"criticality":n.get("criticality",0)} for n in nodes),key=lambda x:x["impact"]*x["criticality"],reverse=True)
    return {"affected":ranked,"model":"directed dependency propagation","status":"screening"}
