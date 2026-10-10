"""Read existing run artifacts only; never import project code or execute native tools."""
import hashlib
import json
import math
from pathlib import Path

REPO = Path('/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver')
WORK = REPO / 'codex-review/P04-CLAUDE-RECOVERY-DIAGNOSTIC-CLOSEOUT-20261009T071842Z-d5f1a3'
RUN = WORK / 'package/object-RUN'
EV = RUN / 'evidence'

def read(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

cost = {it['id'] for it in read(EV / 'REGRESSION_COST_TABLE.json')['items']}
executed, passed, observed, positive = set(), set(), set(), set()
for p in EV.glob('PHASE_*.json'):
    d = read(p)
    executed.update(d['executed'])
    passed.update(d['scientific_pass'])
    observed.update(d['contract_probe_recorded'])
    positive.update(d['registered_expected_failure'])

summary = {'reconciliation': {
    'cost_items': len(cost), 'executed_items': len(executed),
    'scientific_pass': len(passed), 'contract_observation': len(observed),
    'positive_controls': sorted(positive),
    'missing_execution': sorted(cost-executed), 'extra_execution': sorted(executed-cost),
    'unclassified': sorted(cost-passed-observed-positive),
    'category_overlap': sorted((passed & observed) | (passed & positive) | (observed & positive))}}

controls = []
for item in sorted(positive):
    suffix = item.removeprefix('B-POS-')
    v = read(EV / ('pos_' + suffix + '.verify.json'))
    stderr = (RUN / 'logs' / (item + '.stderr')).read_text()
    controls.append({'id': item, 'exit': (RUN/'logs'/(item+'.exit')).read_text().strip(),
                     'signature': v['signature'], 'independent_signature_found': v['signature'] in stderr,
                     'verdict': v['verdict']})
summary['positive_controls'] = controls

freeze = read(EV / 'PRODUCT_FREEZE.json')['products']
summary['freeze'] = {'records': len(freeze), 'mismatches': [p for p,r in freeze.items()
    if not Path(p).is_file() or sha(Path(p)) != r['sha256'] or Path(p).stat().st_size != r['bytes']]}
producer = read(RUN/'logs/B-D002-MAKE-SHIM.attempt.json')
verifier = read(RUN/'logs/B-D002-MAKE-SHIM_verify.attempt.json')
sv = read(RUN/'d002_shim/SHIM_VERIFY.json')
shim = str((RUN/'d002_shim/SHIM.json').resolve())
summary['shim'] = {
    'producer_sha': producer['outputs_after'][shim]['sha256'],
    'first_freeze_sha': freeze[shim]['sha256'],
    'verifier_input_sha': sv['input']['sha256'], 'current_sha': sha(Path(shim)),
    'verifier_output_paths': list(verifier['outputs_after']),
    'verifier_input_unchanged': sv['input_unchanged'], 'verdict': sv['verdict'],
    'first_freeze_utc': freeze[shim]['frozen_utc']}

d002_bad = []
d002_count = 0
for p in EV.glob('case_*.json'):
    d = read(p)
    if 'attempt' not in d:
        continue
    d002_count += 1
    a = d['attempt']
    raw = Path(a['argv'][-1])
    if sha(Path(a['record'])) != a['sha256'] or sha(raw) != d['output_sha256']:
        d002_bad.append(p.name)
summary['d002_provenance'] = {'case_records': d002_count, 'raw_and_attempt_digest_mismatches': d002_bad,
                            'independent_numeric_recomputation': 'NOT_PERFORMED'}

# Independent lossless symmetric-film Airy calculation; no oracle/adapter import.
# Original first-matrix fixes air eps=1, film eps=4, film thickness=0.25.
# The raw case's frequency/angle/polarization are used; model_settings FREQUENCY
# is a default and is not necessarily the per-case frequency.
common = read(RUN/'pkg/cases/d001_first_matrix.json')['common']
summary['d001_common'] = common
assert common['ambient_epsilon'] == 1 and common['film_epsilon_scalar'] == 4
raw_results = []
for tag in ['P02-12', 'LUA-12', 'EXT-16', 'STAGE2']:
    manifest = read(RUN/'results/raw'/('MANIFEST_'+tag+'.json'))
    errs, integrity, keys = [], [], []
    for row in manifest['rows']:
        p = Path(row['raw'])
        d = read(p)
        if sha(p) != row['raw_sha256'] or d['case_key'] != row['case_key'] or row['exit'] != 0:
            integrity.append(row['case_key'])
        keys.append(row['case_key'])
        c = d['case']
        theta = math.radians(c.get('incidence_angle_deg', 0))
        ct = math.sqrt(1-(math.sin(theta)/2)**2)
        if c.get('polarization', 's') == 'p':
            q0, q1 = 1/math.cos(theta), 2/ct
        else:
            q0, q1 = math.cos(theta), 2*ct
        rho = ((q0-q1)/(q0+q1))**2
        delta = 2*math.pi*c['frequency']*2*0.25*ct
        tref = 1/(1+4*rho/(1-rho)**2*math.sin(delta)**2)
        flux = d['flux']['four_fluxes']
        inc = flux['AirTop_forward']['real']
        rval = -flux['AirTop_backward']['real']/inc
        tval = flux['AirBottom_forward']['real']/inc
        errs.append(max(abs(rval-(1-tref)), abs(tval-tref)))
    raw_results.append({'tag': tag, 'rows': len(keys), 'unique_keys': len(set(keys)),
                        'integrity_mismatches': integrity, 'max_abs_error': max(errs),
                        'above_1e_10': sum(e>1e-10 for e in errs)})
summary['d001_independent_raw_airy'] = raw_results
summary['integration'] = {k: read(EV/'INTEGRATION_FINAL.json')[k]
                          for k in ['verdict','counts','not_run','problems','mock_evidence_nodes']}
ledger = read(EV/'cc_budget.json')
summary['unified_cc_ledger'] = {k: ledger[k] for k in ['granted','caps','refused','not_executed']}
summary['production_source_comparison'] = [{
    'path': rel, 'source_equals_run': (WORK/'package/source'/rel).read_bytes() == (RUN/'candidate'/rel).read_bytes(),
    'source_equals_production': (WORK/'package/source'/rel).read_bytes() == (REPO/rel).read_bytes()}
    for rel in ['S4/RNP/Eigensystems.cpp','S4/S4.cpp','S4/rcwa.cpp','S4/main_python.c']]
Path(__file__).with_name('RAW_EVIDENCE_REPLAY.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2))
