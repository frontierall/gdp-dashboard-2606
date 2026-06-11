import streamlit as st
import pandas as pd
import math
from pathlib import Path
import plotly.express as px

st.set_page_config(
    page_title='GDP dashboard',
    page_icon=':earth_americas:',
    layout='wide',
)

# ---------------------------------------------------------------------------
# Region mapping
REGION_MAP = {
    'Asia': ['CHN', 'JPN', 'KOR', 'IND', 'IDN', 'THA', 'VNM', 'MYS', 'PHL', 'SGP',
             'BGD', 'PAK', 'LKA', 'MMR', 'KHM', 'NPL', 'MNG', 'LAO', 'BTN', 'MDV',
             'TJK', 'KGZ', 'TKM', 'UZB', 'KAZ', 'AZE', 'ARM', 'GEO'],
    'Europe': ['DEU', 'FRA', 'GBR', 'ITA', 'ESP', 'NLD', 'BEL', 'SWE', 'NOR', 'DNK',
               'FIN', 'POL', 'AUT', 'CHE', 'PRT', 'CZE', 'HUN', 'ROU', 'GRC', 'SVK',
               'BGR', 'HRV', 'SVN', 'LTU', 'LVA', 'EST', 'IRL', 'LUX', 'MLT', 'CYP',
               'ISL', 'ALB', 'MKD', 'BIH', 'MNE', 'SRB', 'MDA', 'BLR', 'UKR', 'RUS'],
    'Americas': ['USA', 'CAN', 'MEX', 'BRA', 'ARG', 'COL', 'CHL', 'PER', 'VEN', 'ECU',
                 'BOL', 'PRY', 'URY', 'GTM', 'CUB', 'HND', 'SLV', 'NIC', 'CRI', 'PAN',
                 'DOM', 'HTI', 'JAM', 'TTO', 'BLZ', 'GUY', 'SUR'],
    'Africa': ['NGA', 'ZAF', 'EGY', 'DZA', 'ETH', 'KEN', 'TZA', 'GHA', 'UGA', 'MOZ',
               'CIV', 'CMR', 'MDG', 'AGO', 'ZMB', 'SEN', 'ZWE', 'MLI', 'BFA', 'MWI',
               'NER', 'TCD', 'SOM', 'RWA', 'BEN', 'TUN', 'MAR', 'LBY', 'SDN', 'SSD',
               'COD', 'COG', 'GAB', 'GNQ', 'BWA', 'NAM', 'LSO', 'SWZ', 'MUS', 'CPV'],
    'Middle East': ['SAU', 'IRN', 'ARE', 'IRQ', 'ISR', 'QAT', 'KWT', 'OMN', 'BHR', 'JOR',
                    'LBN', 'YEM', 'SYR'],
    'Oceania': ['AUS', 'NZL', 'PNG', 'FJI', 'SLB', 'VUT', 'WSM', 'TON', 'KIR', 'FSM'],
}

# ---------------------------------------------------------------------------

@st.cache_data
def get_gdp_data():
    DATA_FILENAME = Path(__file__).parent / 'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    gdp_df = raw_gdp_df.melt(
        ['Country Name', 'Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])
    gdp_df['GDP'] = pd.to_numeric(gdp_df['GDP'], errors='coerce')

    return gdp_df


gdp_df = get_gdp_data()

code_to_name = (
    gdp_df[['Country Code', 'Country Name']]
    .drop_duplicates()
    .set_index('Country Code')['Country Name']
    .to_dict()
)
all_codes = sorted(gdp_df['Country Code'].unique())

# ---------------------------------------------------------------------------
# Page header
'''
# :earth_americas: GDP dashboard

Browse GDP data from the [World Bank Open Data](https://data.worldbank.org/) website.
'''

''

# ---------------------------------------------------------------------------
# Sidebar controls
with st.sidebar:
    st.header('Filters')

    st.subheader('Region')
    region_options = ['All'] + list(REGION_MAP.keys())
    selected_region = st.selectbox('Select a region', region_options)

    if selected_region == 'All':
        region_codes = all_codes
    else:
        region_codes = [c for c in REGION_MAP[selected_region] if c in set(all_codes)]

    st.subheader('Countries')
    default_codes = ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN']
    default_in_region = [c for c in default_codes if c in set(region_codes)]
    if not default_in_region:
        default_in_region = region_codes[:3]

    country_options = {code_to_name.get(c, c): c for c in region_codes}
    default_names = [code_to_name.get(c, c) for c in default_in_region]

    selected_names = st.multiselect(
        'Select countries',
        options=list(country_options.keys()),
        default=default_names,
    )
    selected_countries = [country_options[n] for n in selected_names]

    st.subheader('Year range')
    min_year = int(gdp_df['Year'].min())
    max_year = int(gdp_df['Year'].max())
    from_year, to_year = st.slider(
        'Years',
        min_value=min_year,
        max_value=max_year,
        value=[min_year, max_year],
    )

    st.subheader('GDP unit')
    unit_label = st.radio('Display unit', ['Trillion ($T)', 'Billion ($B)', 'Million ($M)'])
    unit_map = {'Trillion ($T)': (1e12, 'T'), 'Billion ($B)': (1e9, 'B'), 'Million ($M)': (1e6, 'M')}
    unit_divisor, unit_suffix = unit_map[unit_label]

# ---------------------------------------------------------------------------
if not selected_countries:
    st.warning('Select at least one country in the sidebar.')
    st.stop()

# ---------------------------------------------------------------------------
# Filter data
filtered_df = gdp_df[
    gdp_df['Country Code'].isin(selected_countries)
    & gdp_df['Year'].between(from_year, to_year)
].copy()

filtered_df['GDP_display'] = filtered_df['GDP'] / unit_divisor
filtered_df['Country'] = filtered_df['Country Code'].map(
    lambda c: f"{code_to_name.get(c, c)} ({c})"
)

# ---------------------------------------------------------------------------
# Section 1: GDP over time — tabbed charts
st.header('GDP over time', divider='gray')

tab_line, tab_bar, tab_pie, tab_yoy = st.tabs(
    ['📈 선 그래프', '📊 막대 그래프', '🥧 파이 차트', '📉 YoY 성장률']
)

with tab_line:
    if filtered_df['GDP_display'].isna().all():
        st.info('No GDP data available for the selected filters.')
    else:
        fig = px.line(
            filtered_df.dropna(subset=['GDP_display']),
            x='Year', y='GDP_display', color='Country',
            labels={'GDP_display': f'GDP ({unit_suffix})', 'Year': 'Year'},
        )
        fig.update_layout(legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0))
        st.plotly_chart(fig, use_container_width=True)

with tab_bar:
    bar_df = (
        filtered_df[filtered_df['Year'] == to_year][['Country', 'GDP_display']]
        .dropna()
        .sort_values('GDP_display', ascending=True)
    )
    if bar_df.empty:
        st.info(f'{to_year}년 데이터가 없습니다.')
    else:
        fig = px.bar(
            bar_df, x='GDP_display', y='Country', orientation='h',
            labels={'GDP_display': f'GDP ({unit_suffix})', 'Country': ''},
            title=f'{to_year}년 GDP 비교',
            color='Country',
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with tab_pie:
    pie_df = (
        filtered_df[filtered_df['Year'] == to_year][['Country', 'GDP_display']]
        .dropna()
    )
    if pie_df.empty:
        st.info(f'{to_year}년 데이터가 없습니다.')
    else:
        fig = px.pie(
            pie_df, names='Country', values='GDP_display',
            title=f'{to_year}년 GDP 비율',
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

with tab_yoy:
    yoy_df = (
        filtered_df.sort_values(['Country', 'Year'])
        .assign(YoY=lambda df: df.groupby('Country')['GDP'].pct_change() * 100)
        .dropna(subset=['YoY'])
    )
    if yoy_df.empty:
        st.info('YoY 성장률을 계산할 데이터가 충분하지 않습니다.')
    else:
        fig = px.line(
            yoy_df, x='Year', y='YoY', color='Country',
            labels={'YoY': 'YoY 성장률 (%)', 'Year': 'Year'},
        )
        fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.5)
        fig.update_layout(legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0))
        st.plotly_chart(fig, use_container_width=True)

''

# ---------------------------------------------------------------------------
# Section 2: GDP metric cards
st.header(f'GDP in {to_year}', divider='gray')
''

first_year_df = gdp_df[gdp_df['Year'] == from_year]
last_year_df = gdp_df[gdp_df['Year'] == to_year]

cols = st.columns(4)

for i, country_code in enumerate(selected_countries):
    col = cols[i % len(cols)]
    country_name = code_to_name.get(country_code, country_code)

    first_row = first_year_df[first_year_df['Country Code'] == country_code]['GDP']
    last_row = last_year_df[last_year_df['Country Code'] == country_code]['GDP']

    first_gdp = first_row.iat[0] if len(first_row) else float('nan')
    last_gdp = last_row.iat[0] if len(last_row) else float('nan')

    first_display = first_gdp / unit_divisor if not math.isnan(first_gdp) else float('nan')
    last_display = last_gdp / unit_divisor if not math.isnan(last_gdp) else float('nan')

    if math.isnan(last_display):
        value_str = 'N/A'
        growth = 'N/A'
        delta_color = 'off'
    else:
        value_str = f'{last_display:,.2f}{unit_suffix}'
        if math.isnan(first_display) or first_display == 0:
            growth = 'N/A'
            delta_color = 'off'
        else:
            growth = f'{last_display / first_display:,.2f}x'
            delta_color = 'normal'

    with col:
        st.metric(label=country_name, value=value_str, delta=growth, delta_color=delta_color)

''
''

# ---------------------------------------------------------------------------
# Section 3: Top N countries ranking
st.header('상위 국가 GDP 순위', divider='gray')
''

ctrl_col, chart_col = st.columns([1, 3])

with ctrl_col:
    rank_year = st.number_input(
        '기준 연도', min_value=min_year, max_value=max_year, value=to_year, step=1
    )
    top_n = st.slider('상위 N개국', min_value=5, max_value=30, value=10)

with chart_col:
    rank_df = (
        gdp_df[gdp_df['Year'] == rank_year][['Country Name', 'Country Code', 'GDP']]
        .dropna(subset=['GDP'])
        .copy()
    )
    rank_df['GDP_display'] = rank_df['GDP'] / unit_divisor
    rank_df['Country'] = rank_df['Country Name'] + ' (' + rank_df['Country Code'] + ')'
    rank_df = rank_df.nlargest(top_n, 'GDP_display').sort_values('GDP_display', ascending=True)

    if rank_df.empty:
        st.info(f'{rank_year}년 데이터가 없습니다.')
    else:
        fig = px.bar(
            rank_df, x='GDP_display', y='Country', orientation='h',
            labels={'GDP_display': f'GDP ({unit_suffix})', 'Country': ''},
            title=f'{rank_year}년 GDP 상위 {top_n}개국',
            color='GDP_display',
            color_continuous_scale='Blues',
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
