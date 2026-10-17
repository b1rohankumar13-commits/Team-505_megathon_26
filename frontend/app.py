import os
import json
import html
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='GreenPath · Customer insights',page_icon='🌿',layout='wide',initial_sidebar_state='expanded')
API=os.environ.get('GREENPATH_API','http://127.0.0.1:8000').rstrip('/')
GREEN='#117654'
COLORS=['#117654','#70A889','#ADCFA5','#D2DCCB','#D5AE64','#87A5AB','#527770','#B3BEB8']
st.markdown('''<style>

html,body,[class*="css"], [data-testid="stApp"] {font-family:'DM Sans',sans-serif;}
.block-container {padding-top:2.1rem;padding-bottom:3rem;max-width:1500px;}
h1 {font-size:2.35rem!important;letter-spacing:-1.2px;font-weight:700!important;} h2 {letter-spacing:-.6px;} h3 {font-size:1.15rem!important;}
[data-testid="stSidebar"]{border-right:1px solid #e0e8de;}
[data-testid="stSidebar"] .block-container{padding-top:2rem;}
[data-testid="stMetric"]{background:white;border:1px solid #e1e8df;border-radius:14px;padding:19px 21px;}
[data-testid="stMetricLabel"]{color:#62736a;font-size:13px;}
[data-testid="stMetricValue"]{font-size:1.9rem;font-weight:600;}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:16px;}
.hero{padding:29px 32px;border-radius:19px;background:#123f31;color:#fff;margin:8px 0 23px;position:relative;overflow:hidden;}
.hero h2{font-size:30px!important;color:white;margin:0 0 10px;max-width:780px;}
.hero p{color:#d3e2d2;max-width:770px;font-size:15px;margin:0;line-height:1.6;}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:1.8px;color:#8ba497;text-transform:uppercase;margin-bottom:9px;}
.brand{font-size:28px;font-weight:700;letter-spacing:-1px;color:#153f32;margin-bottom:0;}
.brand-sub{font-size:11px;color:#758779;letter-spacing:2px;margin:0 0 30px;}
.tag{display:inline-block;background:#e5f0e2;border:1px solid #d5e4d3;color:#266644;padding:4px 11px;border-radius:20px;font-size:11px;font-weight:600;}
.muted{color:#758279;font-size:13px;}.product-title{font-size:22px;font-weight:600;margin-top:11px;margin-bottom:5px;}
.rule{height:1px;background:#e2e8de;margin:18px 0;}
.score{font-size:31px;font-weight:700;color:#123f31;}.tiny{font-size:12px;color:#607468;}
</style>''',unsafe_allow_html=True)

def api(path,body=None):
    try:
        r=requests.get(API+path,timeout=15) if body is None else requests.post(API+path,json=body,timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        detail=''
        if getattr(e,'response',None) is not None:
            try: detail=e.response.json().get('detail','')
            except ValueError: pass
        st.error(f'API request failed. {detail} Ensure the FastAPI server is running at {API}.')
        st.code('python run.py')
        st.stop()


def chart(fig,height=330):
    fig.update_layout(height=height,margin=dict(l=5,r=5,t=30,b=5),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='DM Sans, sans-serif',color='#385047'),legend_title_text='')
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#e7ece3')
    st.plotly_chart(fig,width='stretch',config={'displayModeBar':False})


def hero(eyebrow,title,description):
    st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h2>{title}</h2><p>{description}</p></div>',unsafe_allow_html=True)


def jump(page,cid=None,pid=None):
    st.session_state['page']=page
    if cid: st.session_state['selected_customer']=cid
    if pid: st.session_state['selected_product']=pid

customers=api('/customers')
names={c['customer_id']:f"{c['name']} · {c['customer_id']}" for c in customers}
with st.sidebar:
    st.markdown('<div class="brand">◈ GreenPath</div><div class="brand-sub">CUSTOMER INSIGHTS</div>',unsafe_allow_html=True)
    page=st.radio('Workspace',['Overview','Customer 360','Scenario lab','Evidence & data'],key='page')
    st.divider()
    st.markdown('**Your workspace**')
    st.caption('Lloyds PS1 · Prototype\n\nUK customer cohort · GBP')
    st.markdown('<span class="tag">● LOCAL DEMO</span>',unsafe_allow_html=True)
    st.caption('100 fictional customers. No personal banking data.')
    st.divider()
    st.caption('Data cutoff\n\n30 June 2026')
    st.caption('Streamlit → FastAPI → SQLite')

left,right=st.columns([4,1])
with left: st.caption('GREEN CUSTOMER INSIGHTS  /  '+page.upper())
with right: st.markdown('<span class="tag">● API connected</span>',unsafe_allow_html=True)

if page=='Overview':
    st.title('A clearer path to greener banking.')
    st.caption('Find relevant opportunities. Understand the evidence. Help customers take the next step.')
    hero('PORTFOLIO AT A GLANCE','Small changes. Meaningful possibilities.','Explore four green product journeys across your customer portfolio, with transparent evidence behind every opportunity.')
    data=pd.DataFrame(api('/opportunities'))
    f1,f2,f3=st.columns([1.3,1.3,2])
    region=f1.selectbox('Region',['All regions']+sorted(data.region.unique().tolist()))
    product=f2.selectbox('Product',['All products']+data['product'].unique().tolist())
    threshold=f3.slider('Minimum demo ranking score',0,100,50,help='Illustrative ranking only. This is not an adoption probability.')/100
    filtered=data.copy()
    if region!='All regions': filtered=filtered[filtered.region==region]
    if product!='All products': filtered=filtered[filtered['product']==product]
    candidates=filtered[(filtered.suitability=='candidate') & (filtered.demo_score>=threshold)]
    cols=st.columns(4)
    cols[0].metric('Customers in selection',filtered.customer_id.nunique())
    cols[1].metric('Candidate opportunities',len(candidates))
    cols[2].metric('Customers with a candidate',candidates.customer_id.nunique())
    cols[3].metric('Carbon estimate','Unavailable')
    st.caption('Synthetic demo • Rankings are heuristic scores, not trained propensity • Financial eligibility is not assessed')
    a,b=st.columns([1.15,1])
    with a,st.container(border=True):
        st.subheader('Opportunities by product')
        counts=candidates.groupby('product').size().reset_index(name='Candidates')
        if counts.empty: st.info('No candidates match these filters.')
        else: chart(px.bar(counts,x='Candidates',y='product',orientation='h',color_discrete_sequence=[GREEN],labels={'product':''},text='Candidates'))
    with b,st.container(border=True):
        st.subheader('Where the opportunities are')
        counts=candidates.groupby('region').size().reset_index(name='Candidates')
        if not counts.empty: chart(px.bar(counts,x='region',y='Candidates',color_discrete_sequence=['#86AE8E'],labels={'region':''}))
        else: st.info('Adjust your filters to explore regional opportunities.')
    st.subheader('Your opportunity shortlist')
    st.caption('Select a customer below to see suitability, evidence and the next available action.')
    table=candidates.sort_values('demo_score',ascending=False)[['name','customer_id','region','product','demo_score','data_completeness']].copy()
    table['demo_score']=(table.demo_score*100).round().astype(int)
    table['data_completeness']=(table.data_completeness*100).round().astype(int)
    st.dataframe(table,width='stretch',hide_index=True,column_config={'demo_score':st.column_config.ProgressColumn('Demo score / 100',min_value=0,max_value=100,format='%d'),'data_completeness':st.column_config.NumberColumn('Inputs present',format='%d%%'),'name':'Customer','customer_id':'Customer ID','region':'Region','product':'Opportunity'})
    if not table.empty:
        c1,c2=st.columns([3,1]); selected=c1.selectbox('Open customer',table.customer_id.drop_duplicates().tolist(),format_func=lambda x:names[x])
        c2.write('');c2.button('View customer →',on_click=jump,args=('Customer 360',selected),type='primary',width='stretch')
    st.download_button('↓ Export filtered opportunities',candidates.to_csv(index=False),'greenpath-opportunities.csv','text/csv')
    with st.expander('Activity estimates and reporting boundaries'):
        st.write('The Scenario lab reports gas savings, reduced grid imports, EV electricity demand and paper sheets separately. Portfolio carbon totals are unavailable because verified factors were not supplied. No conversion trend is claimed from the synthetic transaction history.')

elif page=='Customer 360':
    st.title('Meet the person behind the opportunity.')
    cid=st.selectbox('Customer',list(names),format_func=lambda x:names[x],key='selected_customer')
    response=api('/customers/'+cid); c=response['customer']; ops=response['opportunities']
    hero('CUSTOMER PROFILE',html.escape(c['name']),f"{html.escape(c['region'])} &nbsp; · &nbsp; {c['customer_id']} &nbsp; · &nbsp; Fictional profile &nbsp; · &nbsp; Updated {c['data_timestamp']}")
    cols=st.columns(4)
    cols[0].metric('Monthly fuel spend',f"£{c['fuel_monthly_gbp']:,}")
    cols[1].metric('Electricity / year',f"{c['electricity_kwh']:,} kWh" if c['electricity_kwh'] is not None else 'Missing')
    cols[2].metric('Digital usage',f"{c['digital_usage']:.0%}")
    cols[3].metric('Paper statements / year',c['paper_statements'])
    tabs=st.tabs(['Green opportunities','Transactions & profile','Saved activity'])
    with tabs[0]:
        st.caption('Scores below are demo rankings out of 100. Model propensity and confidence are not available. Actions record local preferences only.')
        for row in range(2):
            columns=st.columns(2)
            for col,op in zip(columns,ops[row*2:row*2+2]):
                with col,st.container(border=True):
                    candidate=op['suitability']=='candidate'
                    st.markdown(f'<span class="tag">{op["product_id"]} · {op["suitability"].replace("_"," ").upper()}</span><div class="product-title">{op["product"]}</div>',unsafe_allow_html=True)
                    st.write(op['explanation'])
                    x,y=st.columns(2)
                    x.markdown(f'<div class="score">{op["demo_score"]*100:.0f}<span class="tiny"> / 100</span></div><div class="tiny">Demo ranking score</div>',unsafe_allow_html=True)
                    y.markdown(f'<div class="score">{op["data_completeness"]:.0%}</div><div class="tiny">Required inputs present</div>',unsafe_allow_html=True)
                    st.progress(op['demo_score'])
                    with st.expander('Why this opportunity?'):
                        for evidence in op['evidence']: st.write('• '+evidence)
                        st.code(' · '.join(op['reason_codes']))
                        st.caption('Completeness = present product inputs / required product inputs. It is not statistical confidence.')
                        st.caption('Eligibility: not assessed · Carbon impact: unavailable · Explanation: evidence template')
                        st.caption('Data timestamp: '+op['data_timestamp'])
                    b1,b2=st.columns(2)
                    b1.button('Explore scenario →',key='scenario-'+op['product_id'],disabled=not candidate,on_click=jump,args=('Scenario lab',cid,op['product_id']),width='stretch')
                    if b2.button('I’m interested',key='interest-'+op['product_id'],disabled=not candidate,width='stretch',type='primary'):
                        api(f'/customers/{cid}/actions',{'product_id':op['product_id'],'action':'interested'})
                        st.success('Interest saved locally. No application submitted.')
                    if st.button('Dismiss',key='dismiss-'+op['product_id']):
                        api(f'/customers/{cid}/actions',{'product_id':op['product_id'],'action':'dismissed'})
                        st.success('Response saved. Scores and rules are unchanged.')
        st.download_button('↓ Download evidence record',json.dumps(response['opportunities'],indent=2),f'{cid}-evidence.json','application/json')
    with tabs[1]:
        a,b=st.columns([1,2])
        with a,st.container(border=True):
            st.subheader('Customer snapshot')
            st.write('**Home:** '+('Owner' if c['home_owner'] else 'Non-owner'))
            st.write('**Vehicle:** '+c['fuel_type'])
            st.write('**Annual distance:** '+(f"{c['annual_km']:,} km" if c['annual_km'] is not None else 'Missing'))
            st.write('**Income band:** '+c['income_band'])
            st.write('**Products:** '+', '.join(c['existing_products']))
            st.write('**Green products:** '+(', '.join(c['existing_green_products']) or 'None'))
        tx=pd.DataFrame(response['transactions'])
        with b,st.container(border=True):
            st.subheader('Six-month spending mix')
            mix=tx.groupby('category').amount.sum().reset_index()
            chart(px.bar(mix,x='amount',y='category',orientation='h',color_discrete_sequence=[GREEN],labels={'amount':'Spend (£)','category':''}))
        trend=tx.groupby(['date','category']).amount.sum().reset_index()
        chart(px.line(trend,x='date',y='amount',color='category',color_discrete_sequence=COLORS,labels={'date':'Month','amount':'Monthly spend (£)'}))
        st.caption('Fictional transaction activity, January–June 2026. No observed adoption or savings outcomes.')
        category=st.multiselect('Filter transaction categories',sorted(tx.category.unique()),default=[])
        if category: tx=tx[tx.category.isin(category)]
        st.dataframe(tx[['date','merchant_description','category','amount']],hide_index=True,width='stretch')
    with tabs[2]:
        hist=api(f'/customers/{cid}/history')
        st.subheader('Your recorded responses')
        if hist['actions']: st.dataframe(pd.DataFrame(hist['actions']),hide_index=True,width='stretch')
        else: st.info('No responses yet. Explore a product and record your interest.')
        st.subheader('Saved scenarios')
        for s in hist['scenarios']:
            with st.expander(f"Scenario #{s['id']} · {s['payload']['result']['product_id']} · {s['created_at'][:16]}"): st.json(s['payload'])
        if not hist['scenarios']: st.caption('Saved scenario estimates will appear here.')

elif page=='Scenario lab':
    st.title('Explore the difference a change could make.')
    st.caption('Adjust an assumption and compare annual activity. Every result is conditional, not a measured benefit.')
    cid=st.selectbox('Customer',list(names),format_func=lambda x:names[x],key='selected_customer')
    catalogue=api('/catalogue'); products={p['product_id']:p['name'] for p in catalogue}
    pid=st.selectbox('Product journey',list(products),format_func=lambda x:products[x],key='selected_product')
    a,b=st.columns([1,1.7])
    body={'product_id':pid}
    with a,st.container(border=True):
        st.subheader('Your assumptions')
        st.caption(next(p['use_case'] for p in catalogue if p['product_id']==pid))
        if pid=='GP01': body['efficiency']=st.slider('EV electricity use (kWh/km)',.05,.60,.18,.01)
        elif pid=='GP02': body['reduction']=st.slider('Gas-demand reduction (%)',0,80,20)/100
        elif pid=='GP03':
            body['generation']=st.number_input('Solar generation (kWh/year)',0,30000,3500,100)
            body['self_consumption']=st.slider('Solar self-consumption (%)',0,100,60)/100
        else: body['sheets']=st.number_input('Sheets per statement',1,20,2)
        st.caption('All inputs above are editable scenario assumptions, not externally verified specifications.')
    result=api(f'/customers/{cid}/scenario',body)
    with b,st.container(border=True):
        st.subheader('Annual activity estimate')
        if result['status']=='not_calculated': st.warning('This product is '+result['suitability'].replace('_',' ')+'. No impact estimate has been calculated.')
        else:
            for key,value in result['metrics'].items():
                unit='sheets' if 'sheets' in key else 'kWh'
                st.metric(key.replace('_kwh','').replace('_',' ').capitalize(),f'{value:,.0f} {unit}')
            if pid in ['GP02','GP03']:
                baseline=next(iter(result['baseline'].values())); remaining=result['metrics']['remaining_gas_kwh' if pid=='GP02' else 'remaining_grid_import_kwh']
                chart(px.bar(x=['Current annual activity','Scenario annual activity'],y=[baseline,remaining],color_discrete_sequence=[GREEN],labels={'x':'','y':'kWh/year'}),250)
        st.info(result['carbon_status'])
    with st.expander('Method, baseline and assumptions',expanded=True):
        st.write('**Horizon:** '+result['horizon'])
        st.json(result['baseline'])
        for assumption in result['assumptions']: st.write('• '+assumption)
        st.caption(result['boundary'])
        formulas={'GP01':'EV electricity = annual km × proposed kWh/km','GP02':'Gas savings = baseline gas kWh × assumed reduction','GP03':'Grid import reduction = min(baseline imports, solar generation × self-consumption)','GP04':'Sheets avoided = annual paper statements × sheets per statement'}
        st.code(formulas[pid])
    a,b=st.columns([1,3])
    if a.button('Save scenario',type='primary',disabled=result['status']!='estimated'):
        saved=api(f'/customers/{cid}/scenarios',body); st.success(f"Scenario #{saved['id']} saved. Find it under Customer 360 → Saved activity.")
    b.download_button('↓ Download estimate',json.dumps({'inputs':body,'result':result},indent=2),'scenario.json','application/json')

else:
    st.title('Every insight has a paper trail.')
    hero('TRANSPARENCY BY DESIGN','Know what is real. Know what is assumed.','Inspect the data, scoring methods and calculation boundaries that support this prototype.')
    m=api('/methodology')
    tabs=st.tabs(['Data & provenance','Methods & limitations','Product catalogue','API & architecture'])
    with tabs[0]:
        st.info(m['data'])
        st.dataframe(pd.DataFrame(m['source_status']),hide_index=True,width='stretch')
        st.subheader('Eight exclusive transaction categories')
        st.write(' · '.join(m['categories']))
        st.write(m['boundaries'])
        st.caption('Input cutoff: '+m['cutoff']+' · Outcome window: '+m['outcome_window'])
        st.subheader('Try the edge cases')
        for cid,label in [('C10002','EV owner and already paperless'),('C10003','Non-homeowner'),('C10004','Missing electricity and mileage')]:
            st.button(label+' →',key='edge-'+cid,on_click=jump,args=('Customer 360',cid))
    with tabs[1]:
        for heading,key in [('Demo scores','scores'),('ML readiness','models'),('Customer explanations','explanations'),('Impact boundaries','impact'),('Financial eligibility','eligibility')]:
            with st.container(border=True): st.subheader(heading);st.write(m[key])
        st.warning('This is a functional UI and API prototype, not a complete competition ML submission. No trained models, adoption labels, evaluation report, verified carbon factors or LLM integration are included.')
    with tabs[2]: st.dataframe(pd.DataFrame(api('/catalogue')).drop(columns=['icon']),hide_index=True,width='stretch')
    with tabs[3]:
        st.code('Streamlit frontend\n    ↓ HTTP / JSON\nFastAPI backend\n    ├─ Suitability rules + demo scoring\n    ├─ Deterministic activity scenarios\n    ├─ Grounded explanation templates\n    └─ SQLite: customers, transactions, actions, scenarios',language='text')
        st.link_button('Open interactive API docs',API+'/docs')
        st.caption('Local-only default. No authentication or multi-tenant controls. Use fictional data; do not expose this prototype publicly.')
        st.json(m)

st.divider()
st.caption('GreenPath · Independent hackathon prototype based on Lloyds PS1 · Synthetic data · Estimates are conditional · No financial eligibility assessment')
