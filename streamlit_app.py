import streamlit as st
import pandas as pd
import math
from pathlib import Path

st.set_page_config(
    page_title='GDP dashboard',
    page_icon=':earth_americas:',
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

    # Keep Country Name alongside Country Code
    gdp_df = raw_gdp_df.melt(
        ['Country Name', 'Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    # Empty strings → NaN
    gdp_df['GDP'] = pd.to_numeric(gdp_df['GDP'], errors='coerce')

    return gdp_df


gdp_df = get_gdp_data()

# Build code → name lookup
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
''

# ---------------------------------------------------------------------------
# Sidebar controls
with st.sidebar:
    st.header('Filters')

    # 1. Region filter
    st.subheader('Region')
    region_options = ['All'] + list(REGION_MAP.keys())
    selected_region = st.selectbox('Select a region', region_options)

    if selected_region == 'All':
        region_codes = all_codes
    else:
        region_codes = [c for c in REGION_MAP[selected_region] if c in set(all_codes)]

    # 2. Country selector (filtered by region)
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

    # 3. Year range
    st.subheader('Year range')
    min_year = int(gdp_df['Year'].min())
    max_year = int(gdp_df['Year'].max())
    from_year, to_year = st.slider(
        'Years',
        min_value=min_year,
        max_value=max_year,
        value=[min_year, max_year],
    )

    # 4. GDP unit
    st.subheader('GDP unit')
    unit_label = st.radio('Display unit', ['Trillion ($T)', 'Billion ($B)', 'Million ($M)'])
    unit_map = {'Trillion ($T)': (1e12, 'T'), 'Billion ($B)': (1e9, 'B'), 'Million ($M)': (1e6, 'M')}
    unit_divisor, unit_suffix = unit_map[unit_label]

# ---------------------------------------------------------------------------
# Validation
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

# Use "Country Name (Code)" as the chart color label
filtered_df['Country'] = filtered_df['Country Code'].map(
    lambda c: f"{code_to_name.get(c, c)} ({c})"
)

# ---------------------------------------------------------------------------
st.header('GDP over time', divider='gray')
''

if filtered_df['GDP_display'].isna().all():
    st.info('No GDP data available for the selected filters.')
else:
    st.line_chart(
        filtered_df,
        x='Year',
        y='GDP_display',
        color='Country',
    )

''
''

# ---------------------------------------------------------------------------
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
        st.metric(
            label=f'{country_name}',
            value=value_str,
            delta=growth,
            delta_color=delta_color,
        )
