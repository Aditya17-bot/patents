#!/usr/bin/env bash
# Re-run every analysis on the cached AGC data and rebuild figures, IDF-B and PDF.
set -e
cd "$(dirname "$0")"
python data_check.py
python pulse_gain.py
python uptake_balance.py
python offset_anchor.py
python rolling_anchor.py
python dripper_ratio.py
python scale_offset.py
python dryback.py
python control_replay.py
python experiments.py
python e6_commissioning.py
python e7_delivery.py
python e8_drain_cup.py
python e9_dripper_fault.py
python e10_litres_to_drain.py
python e11_p2_anchor.py
python figs.py
python make_idfb.py
powershell -NoProfile -Command '$src = "C:\adi\patents\09_substrate_wc\patent\IDF-B_Substrate_WC_Drain_Onset_Recalibration.docx"; $dst = "C:\adi\patents\09_substrate_wc\patent\IDF-B_Substrate_WC_Drain_Onset_Recalibration.pdf"; $w = New-Object -ComObject Word.Application; $w.Visible = $false; $d = $w.Documents.Open($src, $false, $true); $d.SaveAs([ref]$dst, [ref]17); $n = $d.ComputeStatistics(2); $d.Close([ref]0); $w.Quit(); "pages: $n"'
