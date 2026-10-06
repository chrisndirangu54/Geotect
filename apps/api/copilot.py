from __future__ import annotations
import re,math
def interpret_command(text:str,context:dict|None=None)->dict:
    t=text.strip();low=t.lower();ctx=context or {}
    actions=[]
    def nums(): return [float(x) for x in re.findall(r"[-+]?\d*\.?\d+",t)]
    n=nums()
    if "section" in low and ("borehole" in low or "bh-" in low):
        ids=re.findall(r"BH[-_ ]?\d+",t,re.I);actions.append({"tool":"create_section","args":{"borehole_ids":ids}})
    if "tunnel" in low:
        depth=next((x for x in n if x>0),40);actions.append({"tool":"draw_tunnel","args":{"depth_below_terrain_m":depth,"follow_selected_alignment":True}})
    if "retaining wall" in low or "retaining-wall" in low:
        actions.append({"tool":"design_retaining_wall","args":{"use_selected_alignment":True}})
    if "excavat" in low:
        ratio_match=re.search(r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)",low)
        ratio=[float(ratio_match.group(1)),float(ratio_match.group(2))] if ratio_match else [1,2]
        actions.append({"tool":"create_excavation","args":{"slope_ratio":ratio,"around_selected_polygon":True}})
    if "show" in low and ("uncertain" in low or "low confidence" in low):
        actions.append({"tool":"filter_layers","args":{"confidence_lte":float(ctx.get("confidence_threshold",.5))}})
    if "next borehole" in low or "where" in low and "borehole" in low:
        actions.append({"tool":"recommend_investigation","args":{"method":"borehole"}})
    if "risk" in low and ("why" in low or "increase" in low):
        actions.append({"tool":"explain_risk_change","args":{}})
    if not actions: actions.append({"tool":"search_project","args":{"query":t}})
    return {"command":t,"actions":actions,"requires_confirmation":any(a["tool"].startswith(("draw_","create_","design_")) for a in actions),
            "mode":"deterministic_command_parser","note":"LLM provider may enrich this plan, but execution remains tool/permission gated."}

def explain_risk(current:dict,previous:dict)->dict:
    changes=[]
    for k,v in current.items():
        if isinstance(v,(int,float)) and isinstance(previous.get(k),(int,float)):
            d=v-previous[k]
            if abs(d)>1e-9:changes.append({"metric":k,"change":d,"direction":"up" if d>0 else "down"})
    changes.sort(key=lambda x:abs(x["change"]),reverse=True)
    return {"drivers":changes[:10],"summary":"; ".join(f'{x["metric"]} {x["direction"]} by {abs(x["change"]):.3g}' for x in changes[:5])}
