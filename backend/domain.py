"""Pure, deterministic demo logic. No model or verified carbon factors supplied."""
import random
from datetime import datetime, timezone

CUTOFF = '2026-06-30'
CATEGORIES = ['Fuel', 'Electricity', 'Gas', 'Public Transport', 'Home Improvement', 'Automotive', 'Utilities', 'Other']
CATALOGUE = [
    {'product_id': 'GP01', 'name': 'EV Finance', 'icon': '↗', 'use_case': 'Replace a combustion vehicle with an electric vehicle.'},
    {'product_id': 'GP02', 'name': 'Green Home Loan', 'icon': '⌂', 'use_case': 'Improve home insulation and heating efficiency; excludes solar installation.'},
    {'product_id': 'GP03', 'name': 'Solar Finance', 'icon': '☀', 'use_case': 'Install rooftop solar to reduce electricity imported from the grid.'},
    {'product_id': 'GP04', 'name': 'Paperless Banking', 'icon': '▤', 'use_case': 'Replace existing paper statements with digital statements.'},
]


def seed_customers():
    rng = random.Random(42)
    first = ['Alex', 'Jamie', 'Sam', 'Morgan', 'Taylor', 'Riley', 'Jordan', 'Casey', 'Robin', 'Avery']
    last = ['Bennett', 'Patel', 'Clarke', 'Wilson', 'Reed', 'Shah', 'Brooks', 'Evans', 'Green', 'Singh']
    customers = []
    for i in range(100):
        c = dict(customer_id=f'C{10001+i}', name=f'{first[i%10]} {last[i//10]}', region=rng.choice(['London', 'Midlands', 'North West', 'Scotland', 'South West']),
                 age=rng.randint(25, 69), income_band=rng.choice(['£25–40k', '£40–65k', '£65–90k']),
                 home_owner=rng.random() < .73, roof_suitable=rng.random() < .85,
                 fuel_type=rng.choice(['Petrol', 'Diesel', 'Petrol', 'Electric']), vehicle_age=rng.randint(2, 15),
                 annual_km=rng.randint(5000, 23000), electricity_kwh=rng.randint(2000, 6500), gas_kwh=rng.randint(6000, 20000),
                 paper_statements=rng.choice([0, 12, 24, 36]), digital_usage=round(rng.uniform(.25, .98), 2),
                 fuel_monthly_gbp=rng.randint(60, 320), existing_products=['Current account'],
                 existing_green_products=[], replacement_use_case=False, data_timestamp=CUTOFF, provenance='synthetic')
        if c['home_owner']: c['existing_products'].append('Mortgage')
        if i%7==0: c['existing_products'].append('Vehicle loan')
        if i%13==0: c['existing_green_products']=['GP03']
        if i%17==0: c['electricity_kwh']=None
        customers.append(c)
    customers[0].update(home_owner=True, roof_suitable=True, fuel_type='Petrol', annual_km=18500, electricity_kwh=4800, gas_kwh=14200, paper_statements=24, digital_usage=.92, fuel_monthly_gbp=245, existing_green_products=[])
    customers[1].update(fuel_type='Electric', fuel_monthly_gbp=220, paper_statements=0)
    customers[2].update(home_owner=False, roof_suitable=False)
    customers[3].update(electricity_kwh=None, annual_km=None)
    return customers


def transactions(c):
    rng = random.Random(c['customer_id'])
    merchants = ['Shell · petrol purchase', 'Octopus · electricity only', 'British Gas · gas only', 'National Rail · fare', 'B&Q · insulation', 'Halfords · service', 'Water + broadband bundle', 'Everyday grocery']
    base = [c['fuel_monthly_gbp'], 110, 80, 55, 45, 65, 72, 260]
    rows=[]
    for month in range(1,7):
        for j,cat in enumerate(CATEGORIES):
            rows.append(dict(transaction_id=f"{c['customer_id']}-{month}-{j}", customer_id=c['customer_id'], date=f'2026-{month:02d}-15', merchant_description=merchants[j], category=cat, amount=round(base[j]*rng.uniform(.8,1.2),2), debit_credit='debit', provenance='synthetic', category_method='explicit synthetic merchant mapping'))
    return rows


def opportunities(c):
    out=[]
    for p in CATALOGUE:
        pid=p['product_id']; status='candidate'; reason=[]; evidence=[]
        fields = {'GP01':['annual_km','fuel_type','fuel_monthly_gbp'], 'GP02':['home_owner','gas_kwh'], 'GP03':['home_owner','roof_suitable','electricity_kwh'], 'GP04':['paper_statements','digital_usage']}[pid]
        completeness=sum(c.get(k) is not None for k in fields)/len(fields)
        if completeness < 1: status='insufficient_data'; reason.append('MISSING_INPUTS')
        if pid=='GP01':
            score=.15+.4*min(c['fuel_monthly_gbp']/300,1)+.25*min((c['annual_km'] or 0)/20000,1)
            evidence=[f"Fuel spend: £{c['fuel_monthly_gbp']}/month", f"Annual driving: {c['annual_km'] if c['annual_km'] is not None else 'unknown'} km"]
            if c['fuel_monthly_gbp']>=180: reason.append('HIGH_FUEL_SPEND')
            if (c['annual_km'] or 0)>=15000: reason.append('HIGH_ANNUAL_MILEAGE')
            if c['fuel_type']=='Electric' and not c['replacement_use_case']: status='suppressed'; reason.append('ALREADY_EV_OWNER')
        elif pid=='GP02':
            score=.2+.2*bool(c['home_owner'])+.4*min((c['gas_kwh'] or 0)/20000,1)
            evidence=[f"Homeowner: {c['home_owner']}", f"Annual gas: {c['gas_kwh']} kWh"]
            if c['home_owner']: reason.append('HOME_OWNER')
            if (c['gas_kwh'] or 0)>12000: reason.append('HIGH_GAS_USE')
            if c['home_owner'] is False: status='suppressed'; reason.append('NO_HOME_USE_CASE')
        elif pid=='GP03':
            score=.15+.2*bool(c['home_owner'])+.45*min((c['electricity_kwh'] or 0)/6000,1)
            evidence=[f"Annual electricity: {c['electricity_kwh'] if c['electricity_kwh'] is not None else 'unknown'} kWh", f"Roof suitability: {c['roof_suitable']}"]
            if (c['electricity_kwh'] or 0)>3500: reason.append('HIGH_ELECTRICITY_USE')
            if c['home_owner'] is False or c['roof_suitable'] is False: status='suppressed'; reason.append('NO_SUITABLE_PROPERTY')
        else:
            score=.15+.55*(c['digital_usage'] or 0)+.15*min((c['paper_statements'] or 0)/24,1)
            evidence=[f"Annual paper statements: {c['paper_statements']}", f"Digital usage: {c['digital_usage']:.0%}"]
            if c['digital_usage']>.7: reason.append('HIGH_DIGITAL_ACTIVITY')
            if c['paper_statements']==0: status='suppressed'; reason.append('ALREADY_PAPERLESS')
            else: reason.append('PAPER_STATEMENTS')
        if pid in c['existing_green_products']: status='suppressed'; reason.append('PRODUCT_ALREADY_HELD')
        if not reason: reason=['BASELINE_PROFILE']
        out.append(dict(customer_id=c['customer_id'],product_id=pid,product=p['name'],suitability=status,
            propensity=None, demo_score=round(score,3), score_method='illustrative heuristic, not adoption probability',
            confidence=None, data_completeness=round(completeness,3), eligibility='not_assessed',
            reason_codes=reason,evidence=evidence,data_timestamp=c['data_timestamp'],
            impact_status='unavailable_verified_factors_missing',impact_kgco2e=None,
            explanation=f"{p['name']} is a {status.replace('_',' ')} opportunity. " + '; '.join(evidence) + '. Financial eligibility has not been assessed.',
            explanation_method='deterministic evidence template',provenance='synthetic'))
    return out


def scenario(c, pid, efficiency=.18, reduction=.2, generation=3500, self_consumption=.6, sheets=2):
    op=next(x for x in opportunities(c) if x['product_id']==pid)
    result=dict(product_id=pid, horizon='annual', suitability=op['suitability'], metrics={}, carbon_kgco2e=None,
        carbon_status='Unavailable: verified, compatible emissions factors were not supplied.',
        assumptions=[], baseline={}, status='estimated', boundary='Activity-only comparison; not a lifecycle or financed-emissions calculation.')
    if op['suitability']!='candidate':
        result.update(status='not_calculated', assumptions=['Resolve the suitability or missing-data issue before estimating impact.']); return result
    if pid=='GP01':
        result['baseline']={'combustion_vehicle_km':c['annual_km']}
        result['metrics']={'ev_electricity_required_kwh':round(c['annual_km']*efficiency,1)}
        result['assumptions']=[f'Proposed EV consumption: {efficiency} kWh/km.', 'Driving distance unchanged; charging losses and vehicle manufacture excluded.', 'Electricity required is consumption, not energy saved.']
    elif pid=='GP02':
        result['baseline']={'gas_kwh':c['gas_kwh']}
        result['metrics']={'gas_saved_kwh':round(c['gas_kwh']*reduction,1),'remaining_gas_kwh':round(c['gas_kwh']*(1-reduction),1)}
        result['assumptions']=[f'User-selected gas-demand reduction: {reduction:.0%}; not a surveyed home-performance prediction.', 'No solar effects included.']
    elif pid=='GP03':
        saved=min(c['electricity_kwh'],generation*self_consumption)
        result['baseline']={'grid_import_kwh':c['electricity_kwh']}
        result['metrics']={'grid_import_reduced_kwh':round(saved,1),'remaining_grid_import_kwh':round(c['electricity_kwh']-saved,1)}
        result['assumptions']=[f'Solar generation: {generation} kWh/year; self-consumption: {self_consumption:.0%}.', 'Reduction capped at current annual imports. Export, storage and lifecycle effects excluded.']
    else:
        result['baseline']={'paper_statements':c['paper_statements']}
        result['metrics']={'sheets_avoided':c['paper_statements']*sheets}
        result['assumptions']=[f'{sheets} sheets per statement; all current paper statements replaced.', 'No net carbon claim; digital impacts have not been assessed.']
    return result
