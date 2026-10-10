#!/usr/bin/env bash
# Re-run the evidence on the cached Environment Agency data and rebuild figures, IDF-B and PDF.
set -e
cd "$(dirname "$0")"
export EA_OFFLINE=1
python evidence.py > ../results/ev_log.txt
python figs_arch.py
python figs_data.py
python figs_claims.py
python make_idfb.py
powershell -NoProfile -Command '$src = "C:\adi\patents\08_ammonium_ise\patent\IDF-B_Ammonium_Sonde_Floor_Anchor.docx"; $dst = "C:\adi\patents\08_ammonium_ise\patent\IDF-B_Ammonium_Sonde_Floor_Anchor.pdf"; $w = New-Object -ComObject Word.Application; $w.Visible = $false; $d = $w.Documents.Open($src, $false, $true); $d.SaveAs([ref]$dst, [ref]17); $n = $d.ComputeStatistics(2); $d.Close([ref]0); $w.Quit(); "pages: $n"'
