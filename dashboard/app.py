"""Run from the repository root: streamlit run dashboard/app.py."""
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from src.streamlit_ui import apply_product_styles, hero, kpi_grid, section_heading, sidebar_brand, status_banner
from utils.data_loader import DATA_DIR, DataError, MODEL_NAMES, WINDOWS, load_data, preferred_model, route_view

st.set_page_config(page_title='Urban Flow | Operational intelligence', page_icon=':material/analytics:', layout='wide')
apply_product_styles()
TEAL, AMBER, INK = '#087F8C', '#D18B28', '#183444'
SECTIONS = ['Executive Overview', 'Demand and Hotspots', 'OD and Time Patterns', 'Forecasting', 'Recommendations']
SECTION_DESCRIPTIONS = {
    'Executive Overview': 'A concise view of the verified operating picture.',
    'Demand and Hotspots': 'Explore where and when retained pickup demand concentrates.',
    'OD and Time Patterns': 'Review directed trip flows across zones, boroughs, and operating windows.',
    'Forecasting': 'Compare validated methods and inspect saved forecast paths by horizon.',
    'Recommendations': 'Review evidence-linked actions and their interpretation limits.',
}


@st.cache_data(show_spinner=False)
def get_data():
    return load_data()


def chart(fig, key):
    fig.update_layout(template='plotly_white', font={'family':'Arial', 'size':13, 'color':INK},
                      margin={'l':15,'r':25,'t':65,'b':30}, title_font_size=18,
                      legend_title_text='', paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='#FFFFFF', hoverlabel={'font_size':12})
    with st.container(border=True, key=f'chart_card_{key}'):
        st.plotly_chart(fig, width='stretch', key=key,
                        config={'displaylogo':False, 'responsive':True})


def bar(frame, label, count, title, unit='Retained trips', n=10, color=TEAL):
    selected = frame.dropna(subset=[label]).sort_values([count,label], ascending=[False,True]).head(n).copy()
    fig = px.bar(selected, y=label, x=count, orientation='h', title=title, text=count,
                 labels={label:'',count:unit}, color_discrete_sequence=[color])
    number_format = ',.2f' if 'nominal hour' in unit else ',.0f'
    fig.update_traces(texttemplate='%{x:'+number_format+'}', textposition='outside', cliponaxis=False,
                      hovertemplate='%{y}<br>%{x:'+number_format+'} '+unit+'<extra></extra>')
    fig.update_layout(yaxis={'categoryorder':'array','categoryarray':selected[label].tolist()[::-1]},
                      xaxis={'range':[0, selected[count].max()*1.25] if len(selected) else [0,1]},
                      height=max(340, min(n, len(selected))*32+120))
    return fig


def history_caption():
    st.caption('HISTORICAL ANALYSIS · April 1, 2025–March 31, 2026 · Retained trips, not all real-world demand')


def executive(d):
    section_heading('Put demand at the center of fleet planning',
                    'A decision-ready summary of demand concentration, time intensity, and forecast performance.')
    history_caption()
    top_pu = d['pickups'].sort_values('pickup_count',ascending=False).iloc[0]
    top_do = d['destinations'].sort_values('dropoff_count',ascending=False).iloc[0]
    manhattan = d['borough_od'].loc[lambda x: x.pickup_borough_name.eq('Manhattan') & x.dropoff_borough_name.eq('Manhattan'), 'trip_count'].sum()
    route = d['od'].sort_values('trip_count',ascending=False).iloc[0]
    m24 = d['test_metrics'].loc[lambda x:x.horizon_hours.eq(24)].iloc[0]
    summary = d['time_summary'].copy()
    evening = summary.loc[summary.time_bucket.eq('evening_peak'), 'mean_pickups_per_nominal_hour'].iloc[0]
    morning = summary.loc[summary.time_bucket.eq('morning_peak'), 'mean_pickups_per_nominal_hour'].iloc[0]
    kpi_grid([
        {'label':'Processed trips', 'value':f"{d['total']:,}", 'context':'Retained analytical records'},
        {'label':'Top pickup zone', 'value':top_pu.pickup_zone_name, 'context':f'{top_pu.pickup_count:,} pickups'},
        {'label':'Manhattan → Manhattan', 'value':f"{manhattan/d['total']:.2%}", 'context':f'{manhattan:,} retained trips'},
        {'label':'Evening vs morning', 'value':f'{evening/morning:.2f}×', 'context':'Normalized demand intensity'},
        {'label':'Best 24h forecast', 'value':MODEL_NAMES[preferred_model(m24)], 'context':f'Test MAE {m24.improved_mae:.4f}'},
    ])
    a,b = st.columns(2)
    with a.container(border=True):
        st.caption('LEADING PICKUP HOTSPOT · OPERATING FOCUS')
        st.subheader(top_pu.pickup_zone_name)
        st.write(f'**{top_pu.pickup_count:,}** retained pickups. Review staging capacity alongside observed queues and utilization.')
    with b.container(border=True):
        st.caption('LEADING DESTINATION · ARRIVAL CONCENTRATION')
        st.subheader(top_do.dropoff_zone_name)
        st.write(f'**{top_do.dropoff_count:,}** retained dropoffs. Use destination concentration as context for repositioning review.')
    st.info(f'**Strongest directed route:** {route.pickup_zone_name} → {route.dropoff_zone_name} · {route.trip_count:,} trips', icon=':material/route:')
    a,b = st.columns([1.45,1])
    summary['Window'] = summary.time_bucket.map(WINDOWS)
    with a:
        chart(bar(summary,'Window','mean_pickups_per_nominal_hour','Evening has the highest demand intensity',
                  unit='Pickups per nominal hour',n=4), 'overview_intensity')
        st.caption('Counts ÷ (365 days × window hours). Unequal time windows are normalized for comparison.')
    with b:
        st.subheader('Evidence → decision')
        st.markdown('**Position:** Focus staging reviews on the leading Manhattan and airport hotspots.\n\n'
                    '**Schedule:** Use demand intensity, not window totals alone, when comparing staffing needs.\n\n'
                    '**Reposition:** Review both directions of occupied-trip flows before moving empty vehicles.\n\n'
                    '**Plan:** Use the lower-error method for each forecast horizon.')
        with st.expander('What the data can explain'):
            st.write('The evidence shows where trips concentrate and how clock-time patterns differ. It does not establish why riders travel, prove a vehicle shortage, or measure idle driving. Employment, airport schedules and supply constraints would require additional evidence.')


def demand(d):
    section_heading('Demand and hotspots', 'Explore pickup concentration, destinations, boroughs, and time-of-day demand.')
    history_caption()
    top_n = st.selectbox('Zones to show', [10,15,20], key='hotspot_count')
    chart(bar(d['pickups'],'pickup_zone_name','pickup_count','Pickup hotspots',n=top_n), 'pickup_hotspots')
    chart(bar(d['destinations'],'dropoff_zone_name','dropoff_count','Destination hotspots',n=top_n,color='#6554A4'), 'destination_hotspots')
    st.caption('Rankings use readable labels; missing-label records remain in overall totals.')
    a,b = st.columns(2)
    boroughs = d['boroughs'].copy().fillna({'pickup_borough_name':'(Missing label)'})
    with a: chart(bar(boroughs,'pickup_borough_name','pickup_count','Pickup demand by borough label',n=8), 'borough_demand')
    with b:
        hours = d['hours'].copy()
        hours['Mean pickups per day'] = hours.pickup_count/365
        fig = px.bar(hours,x='hour_of_day',y='Mean pickups per day',title='Demand by pickup clock hour',
                     labels={'hour_of_day':'Pickup hour'},color_discrete_sequence=[TEAL],custom_data=['pickup_count'])
        fig.update_traces(hovertemplate='Hour %{x}:00<br>%{y:,.2f} per calendar day<br>%{customdata[0]:,} annual pickups<extra></extra>')
        fig.update_xaxes(dtick=2)
        chart(fig,'hourly_demand')
        st.caption('365-day denominator; the documented absent hour on March 8, 2026 remains zero. Clock times are timezone-naive.')
    st.subheader('Inspect a pickup zone by operating window')
    zone = st.selectbox('Pickup zone',sorted(d['pickups'].pickup_zone_name.dropna().unique()),
                        index=sorted(d['pickups'].pickup_zone_name.dropna().unique()).index('Upper East Side South'),key='demand_zone')
    zone_data = d['zone_time'].loc[lambda x:x.pickup_zone_name.eq(zone)].copy()
    zone_data['Window'] = zone_data.time_bucket.map(WINDOWS)
    chart(bar(zone_data,'Window','mean_pickups_per_nominal_hour',f'{zone} · pickup intensity',unit='Pickups per nominal hour',n=4),'zone_windows')
    with st.expander('Weekday volume · all zones'):
        weekdays = d['weekdays'].sort_values('iso_weekday')
        chart(px.bar(weekdays,x='weekday',y='pickup_count',title='Total pickups by weekday',
                     labels={'weekday':'Weekday','pickup_count':'Retained pickups'},color_discrete_sequence=[TEAL]),'weekday_demand')
        st.caption('Volume totals, not average pickups per occurrence of each weekday.')


def od_patterns(d):
    section_heading('OD and time patterns', 'Inspect directed route volume and borough movement by operating window.')
    history_caption()
    bucket = st.selectbox('Operating window',['All day',*WINDOWS],format_func=lambda x:WINDOWS.get(x,x),key='od_window')
    routes, scope = route_view(d,bucket)
    st.caption(scope+'. Only the strongest 10 are shown below; an absent pair does not mean zero trips.')
    routes['Route'] = routes.pickup_zone_name+' → '+routes.dropoff_zone_name
    chart(bar(routes,'Route','trip_count','Leading directed routes',n=10),'directed_routes')
    st.caption('Directions are pickup → destination. Same-zone trips do not imply the same physical location.')
    if bucket != 'All day':
        row = d['time_summary'].loc[lambda x:x.time_bucket.eq(bucket)].iloc[0]
        a,b,c = st.columns(3)
        a.metric('All trips in this window',f'{row.trip_count:,}')
        b.metric('Mean pickups per nominal hour',f'{row.mean_pickups_per_nominal_hour:,.2f}')
        c.metric('Window hours per day',str(int(row.window_hours_per_day)))
    boroughs = (d['borough_od'].copy() if bucket=='All day' else
                d['borough_time_od'].loc[lambda x:x.time_bucket.eq(bucket)].copy())
    boroughs = boroughs.fillna({'pickup_borough_name':'(Missing label)','dropoff_borough_name':'(Missing label)'})
    origin = st.selectbox('Pickup borough for destination mix',['All boroughs',*sorted(boroughs.pickup_borough_name.unique())],key='od_borough')
    selected = boroughs if origin=='All boroughs' else boroughs.loc[boroughs.pickup_borough_name.eq(origin)]
    destinations = selected.groupby('dropoff_borough_name',as_index=False).trip_count.sum()
    chart(bar(destinations,'dropoff_borough_name','trip_count',f'Destination mix from {origin.lower() if origin=="All boroughs" else origin}',n=8),'borough_destination_mix')
    st.caption('This borough view uses complete aggregate counts. The borough selector affects this chart only; zone labels have no inferred borough mapping.')
    total = int(selected.trip_count.sum())
    within = int(selected.loc[selected.pickup_borough_name.eq(selected.dropoff_borough_name),'trip_count'].sum())
    st.write(f'**Selected borough flow:** {total:,} trips; {within/total:.2%} have matching pickup/dropoff borough labels.' if total else 'No recorded flows for this selection.')
    with st.expander('Compare all operating windows'):
        view = d['time_summary'].assign(Window=lambda x:x.time_bucket.map(WINDOWS))
        st.dataframe(view[['Window','trip_count','mean_pickups_per_nominal_hour']].rename(columns={'trip_count':'Trips','mean_pickups_per_nominal_hour':'Pickups / nominal hour'}),hide_index=True,width='stretch')


def forecasts(d):
    section_heading('Forecasting', 'Select a planning horizon, compare validated errors, and inspect archived forecast paths.')
    st.caption('SAVED FORECASTS · April 1–3, 2026 · These are archived outputs, not a live forecast')
    with st.container(border=True):
        a,b = st.columns([1,2])
        horizon = a.selectbox('Forecast horizon',[24,48,72],format_func=lambda h:f'{h} hours',key='forecast_horizon')
        data = d[f'forecast_{horizon}']
        zone = b.selectbox('Forecast zone',['All 10 forecast zones',*sorted(data.pickup_zone_name.unique())],key='forecast_zone')
    metric = d['test_metrics'].loc[lambda x:x.horizon_hours.eq(horizon)].iloc[0]
    method = preferred_model(metric)
    status_banner(f'{horizon}h recommended reference: {MODEL_NAMES[method]}',
                  'Lower held-out test MAE. ' + ('Use as a next-day tactical dispatch reference.' if horizon==24 else 'Use as a staffing and planning reference.'))
    st.subheader('Held-out evaluation · historical test period')
    a,b,c = st.columns(3)
    a.metric('Seasonal baseline MAE',f'{metric.baseline_mae:.4f}')
    b.metric('Gradient boosting MAE',f'{metric.improved_mae:.4f}')
    c.metric('Test forecast origins',str(int(metric.n_origins)))
    st.caption('MAE is pickups per zone-hour across the fixed 10-zone cohort. These metrics do not change with the zone selector; zone-specific errors are not in the reporting snapshot.')
    scored = d['test_metrics'][['horizon_hours','baseline_mae','improved_mae','baseline_rmse','improved_rmse']].copy()
    scored['Lower-MAE method'] = [MODEL_NAMES[preferred_model(r)] for r in d['test_metrics'].itertuples()]
    with st.expander('Compare all horizons · MAE and RMSE',expanded=True):
        st.dataframe(scored.rename(columns={'horizon_hours':'Horizon (h)','baseline_mae':'Baseline MAE','improved_mae':'Gradient boosting MAE','baseline_rmse':'Baseline RMSE','improved_rmse':'Gradient boosting RMSE'}),hide_index=True,width='stretch')
    st.subheader(f'Saved {horizon}-hour forecast path')
    selection = data if zone=='All 10 forecast zones' else data.loc[data.pickup_zone_name.eq(zone)]
    series = selection.groupby('pickup_hour',as_index=False)[['baseline_forecast','improved_forecast']].sum()
    series = series.rename(columns={'baseline_forecast':'Seasonal baseline','improved_forecast':'Gradient boosting'})
    long = series.melt(id_vars='pickup_hour',var_name='Method',value_name='Expected pickups')
    fig = px.line(long,x='pickup_hour',y='Expected pickups',color='Method',title=zone,
                  labels={'pickup_hour':'Saved target hour'},color_discrete_map={'Seasonal baseline':AMBER,'Gradient boosting':TEAL})
    fig.update_layout(hovermode='x unified')
    chart(fig,'forecast_path')
    st.caption(f"Forecast origin: {data.forecast_origin.iloc[0]:%Y-%m-%d %H:%M}. Path ends {data.pickup_hour.max():%Y-%m-%d %H:%M}. Expected counts may be fractional. No actual outcomes are bundled for these dates.")
    st.download_button(f'Download original {horizon}h forecast CSV',(DATA_DIR/f'forecast_{horizon}h.csv').read_bytes(),
                       file_name=f'forecast_{horizon}h.csv',mime='text/csv')
    st.caption('Download includes all 10 zones, unchanged from Member 3.')
    with st.expander('How to interpret the evaluation'):
        st.write('Training ends December 10, 2025; validation runs December 11–February 4. The test period is February 5–March 31, 2026. Scores pool the first H hourly predictions across 53 daily origins. Recursive forecasts use predicted future lags, not observed future demand. Windows overlap. Zones were selected retrospectively, and the missing hour remains zero. April forecast outputs were fitted using all observations through March 31; they are separate from test evaluation.')


def recommendations(d):
    section_heading('Recommendations', 'Five evidence-linked actions for operational review and planning.')
    st.info('Validate vehicle availability and queue conditions before changing deployment.', icon=':material/info:')
    titles = ['Review hotspot staging','Emphasize evening dispatch','Maintain late-night coverage','Check both route directions','Choose forecasts by horizon']
    for index,(title,text) in enumerate(zip(titles,d['recommendations']),1):
        with st.container(border=True):
            st.caption(f'RECOMMENDATION {index} · VERIFIED EVIDENCE')
            st.subheader(title)
            st.markdown(text)
    st.caption('Recommendation wording is read directly from the bundled findings report. Evidence filenames refer to that original analysis; interactive equivalents appear in the preceding sections.')
    st.download_button('Download original findings report',d['report'],file_name='demand_spatial_findings.md',mime='text/markdown')
    st.info('No financial savings, idle-driving reduction or service improvement has been measured. These recommendations identify decisions to investigate, not proven business outcomes.')


with st.sidebar:
    sidebar_brand('Urban Flow Analytics', 'Operational intelligence for fleet and city planning.')
    section = st.radio('Management view', SECTIONS, key='section')
    st.caption(SECTION_DESCRIPTIONS[section])
    st.markdown('##### Coverage')
    st.caption('Historical: Apr 2025–Mar 2026  \nSaved forecasts: Apr 1–3, 2026')

hero('Urban Flow Analytics', 'Operational intelligence dashboard',
     'Verified demand, route, forecast, and spatial evidence for practical fleet planning.')
try:
    data = get_data()
except (DataError, OSError, ValueError, KeyError, IndexError) as exc:
    st.error(f'Dashboard reporting inputs could not be loaded. {exc}')
    st.info('See dashboard/README.md for restoring the small pinned snapshot. The dashboard never rebuilds raw trip data.')
    st.stop()
{'Executive Overview':executive,'Demand and Hotspots':demand,'OD and Time Patterns':od_patterns,
 'Forecasting':forecasts,'Recommendations':recommendations}[section](data)
st.caption('Bonus Track 6 · Turning Taxi Data into Business Decisions · Source: verified Member 3 reporting snapshot')
