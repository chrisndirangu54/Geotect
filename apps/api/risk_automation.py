from __future__ import annotations
def evaluate_rules(context:dict,rules:list[dict])->dict:
    fired=[]
    for rule in rules:
        conditions=rule.get("conditions",[])
        ok=True;details=[]
        for c in conditions:
            value=context.get(c["field"]);op=c.get("op",">");threshold=c.get("value")
            passed={"gt":value is not None and value>threshold,"gte":value is not None and value>=threshold,
                    "lt":value is not None and value<threshold,"lte":value is not None and value<=threshold,
                    "eq":value==threshold}.get(op,value is not None and value>threshold)
            details.append({"field":c["field"],"passed":passed,"actual":value,"threshold":threshold});ok=ok and passed
        if ok:fired.append({"id":rule.get("id"),"name":rule.get("name"),"severity":rule.get("severity","warning"),"actions":rule.get("actions",[]),"evidence":details})
    return {"fired":fired,"count":len(fired)}
