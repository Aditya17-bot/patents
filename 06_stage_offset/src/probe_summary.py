import json, sys, numpy as np
d=json.load(open('../results/probe.json'))
allrows=[]
for r in d['results']:
    rows=r.get('rows',[])
    if not rows: continue
    qm=np.array([w['q_meas'] for w in rows])
    e=lambda q: np.nanmedian(np.abs(np.array([w[q] for w in rows],float)/qm-1))*100
    sm=np.array([w['s_meas'] for w in rows]); sp=np.array([w['s_prev'] for w in rows]); sd=np.array([w['s_delta'] for w in rows])
    print(r['x'],r['y'],'lag',r['lag_h'],'dc %.3f'%r['daily_corr'],'n',len(rows),
      'MAE s: carry %.3f delta %.3f abs %.3f'%(np.median(abs(sp-sm)),np.nanmedian(abs(sd-sm)),np.nanmedian(abs(np.array([w['s_abs'] for w in rows])-sm))),
      '| Q%%: base %.1f carry %.1f transfer %.1f ratio %.1f abs %.1f delta %.1f'%(e('q_base'),e('q_carry'),e('q_transfer'),e('q_ratio'),e('q_abs'),e('q_delta')))
    for w in rows: w['pair']=(r['x'],r['y']); w['dcorr']=r['daily_corr']
    allrows+=rows
