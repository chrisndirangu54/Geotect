#!/usr/bin/env python3
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"apps"/"api"))
from verification_campaigns import wave_propagation_benchmark,phase_field_energy_convergence,write_campaign_result
def main():
    root="verification-campaign-results"
    write_campaign_result(root,"wave_propagation",wave_propagation_benchmark())
    write_campaign_result(root,"phase_field_energy",phase_field_energy_convergence())
    print(json.dumps({"output":root}))
if __name__=="__main__":main()
