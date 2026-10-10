#!/usr/bin/env bash
# Re-run every evaluation on the cached data and rebuild figures, IDF-B and PDF.
set -e
cd "$(dirname "$0")"
export USGS_OFFLINE=1
python coupling.py
python probe_daily.py daily
Y_MODE=realtime python probe_daily.py daily_rt
Y_MODE=interp python probe_daily.py daily_ip
Y_MODE=rtfinal python probe_daily.py daily_rtf
IV_MODE=1 python probe_daily.py daily_iv
# sensitivity runs for e9 (window length, steadiness threshold)
WIN_D=14 python probe_daily.py daily_w14
WIN_D=28 python probe_daily.py daily_w28
STEADY_FT=0.15 python probe_daily.py daily_s15
STEADY_FT=0.35 python probe_daily.py daily_s35
python experiments.py > /dev/null
python e6_timing.py
python e7_iv.py > /dev/null
python e8_india.py > /dev/null
python e9_bootstrap.py > /dev/null
python make_figs.py
python make_idfb.py
powershell -NoProfile -Command '$src = "C:\adi\patents\06_stage_offset\patent\IDF-B_Stage_Offset_Neighbour_Gauge.docx"; $dst = "C:\adi\patents\06_stage_offset\patent\IDF-B_Stage_Offset_Neighbour_Gauge.pdf"; $w = New-Object -ComObject Word.Application; $w.Visible = $false; $d = $w.Documents.Open($src, $false, $true); $d.SaveAs([ref]$dst, [ref]17); $n = $d.ComputeStatistics(2); $d.Close([ref]0); $w.Quit(); "pages: $n"'
