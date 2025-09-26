import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# --- Page Configuration ---
st.set_page_config(page_title="Flight Crew Prize Pool", layout="wide")

## Define the URL to your CSV file on GitHub
CSV_URL = 'https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/main/flight_sales.csv'

# --- Background CSS ---
def apply_background_css(desktop_bg_url, mobile_bg_url):
    st.markdown(f"""
    <style>
        /* Background Images */
        .stApp {{
            background-image: url('{desktop_bg_url}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            min-height: 100vh;
        }}
        
        /* Mobile Background */
        @media (max-width: 768px) {{
            .stApp {{
                background-image: url('{mobile_bg_url}');
                background-attachment: scroll;
            }}
        }}
        
        /* App Styling */
        body {{
            color: #333;
        }}
        
        div[data-testid="stVerticalBlock"] {{
            gap: 0.75rem;
        }}
        
        .stApp > header {{
            display: none;
        }}
        
        /* Header styling */
        .main-header {{
            color: #FFFFFF;
            font-size: 1.8rem;
            font-weight: bold;
            text-align: center;
            margin: 2rem 0 1.5rem 0;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            background: rgba(0, 0, 0, 0.4);
            padding: 1.5rem;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            line-height: 1.4;
        }}
        
        .toki-whisky {{
            color: #FF8C00;
            font-weight: bold;
        }}
        
        .roku-gin {{
            color: #FF8C00;
            font-weight: bold;
        }}
        
        /* Section titles */
        .section-title {{
            color: #FFFFFF;
            font-size: 1.5rem;
            font-weight: bold;
            text-align: center;
            margin: 1.5rem 0 1rem 0;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            background: rgba(0, 0, 0, 0.3);
            padding: 0.8rem;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        /* Scorecard styling */
        .scorecard {{
            background-color: rgba(255, 255, 255, 0.15);
            border: 2px solid #00ff41;
            border-radius:15px;
            padding:1rem;
            text-align:center;
            height:100%;
            display:flex;
            flex-direction:column;
            justify-content:center;
            gap:0.3rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            margin-bottom: 1rem;
        }}
        .scorecard-rank{{
            font-size:2rem;
            font-weight:bold;
            margin-bottom:0.25rem;
            color:#FFFFFF;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
        }}
        .scorecard-name{{
            color:#FFFFFF;
            font-size:1.1rem;
            font-weight:bold;
            word-wrap:break-word;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
            overflow-wrap: break-word;
            hyphens: auto;
        }}
        .scorecard-sales{{
            color:#00ff41;
            font-size:1.5rem;
            font-weight:bold;
            line-height:1;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
        }}
        .scorecard-label{{
            color:rgba(255, 255, 255, 0.9);
            font-size:0.8rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        }}
    </style>
    """, unsafe_allow_html=True)

# --- Cached Data Functions ---
@st.cache_data
def load_data(url):
    """Reads, cleans, and caches the CSV data from a URL."""
    try:
        df = pd.read_csv(url)
        required_cols = ['Flight_ID', 'Flight_Date', 'Crew_ID', 'Crew_Name', 'Bottles_Sold_on_Flight', 'crew_sold_quantity']
        if all(col in df.columns for col in required_cols):
            df['Flight_Date'] = pd.to_datetime(df['Flight_Date'], errors='coerce')
            df.dropna(subset=['Flight_Date'], inplace=True)
            
            # Add Airline_Code if not exists
            if 'Airline_Code' not in df.columns:
                df['Airline_Code'] = df['Flight_ID'].str.extract(r'^([A-Z0-9]{1,3})', expand=False)
                df['Airline_Code'] = df['Airline_Code'].fillna('AK')
                # Simple split: first half AK, second half D7
                half_point = len(df) // 2
                df.loc[half_point:, 'Airline_Code'] = 'D7'
                df.loc[:half_point-1, 'Airline_Code'] = 'AK'
            
            return df
        else:
            st.error(f"CSV from URL is missing required columns: {required_cols}")
            return None
    except Exception as e:
        st.error(f"Error reading data: {e}")
        return None

@st.cache_data
def calculate_flight_metrics(_df):
    """Calculates prize pool and leaderboards."""
    if _df.empty:
        return 0.00, pd.DataFrame(), pd.DataFrame(), 0
        
    import math
    
    # Sum by airline group first, then apply rounding
    ak_crew = _df[_df['Airline_Code'] == 'AK'].copy()
    d7_crew = _df[_df['Airline_Code'] == 'D7'].copy()
    
    # Calculate total bottles by summing all Bottles_Sold_on_Flight first, then round up
    total_bottles_raw = _df['Bottles_Sold_on_Flight'].sum()
    total_bottles = math.ceil(total_bottles_raw) if total_bottles_raw > 0 else 0
    prize_pool = total_bottles * 5.00
    
    # AK leaderboard - sum per crew, then round up individual totals - only top 3
    ak_leaderboard = ak_crew.groupby(['Crew_ID', 'Crew_Name'])['crew_sold_quantity'] \
                           .sum() \
                           .reset_index()
    # Round up the total for each crew member
    ak_leaderboard['Total Bottles Sold'] = ak_leaderboard['crew_sold_quantity'].apply(
        lambda x: math.ceil(x) if x > 0 else 0
    )
    ak_leaderboard = ak_leaderboard.drop('crew_sold_quantity', axis=1) \
                                   .sort_values(by='Total Bottles Sold', ascending=False) \
                                   .head(3)
                 
    # D7 leaderboard - sum per crew, then round down individual totals - only top 3
    d7_leaderboard = d7_crew.groupby(['Crew_ID', 'Crew_Name'])['crew_sold_quantity'] \
                           .sum() \
                           .reset_index()
    # Round down (floor) the total for each crew member
    d7_leaderboard['Total Bottles Sold'] = d7_leaderboard['crew_sold_quantity'].apply(
        lambda x: int(x)  # This floors the value
    )
    d7_leaderboard = d7_leaderboard.drop('crew_sold_quantity', axis=1) \
                                   .sort_values(by='Total Bottles Sold', ascending=False) \
                                   .head(3)
            
    return prize_pool, ak_leaderboard, d7_leaderboard, total_bottles

# --- Prize Pool Component ---
def PrizePoolComponent(amount, total_bottles):
    """Renders the prize pool component."""
    html_string = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');
        body{{margin:0;padding:0;}}
        .prize-pool-container{{
            background-color: rgba(255, 255, 255, 0.15);
            border: 3px solid #00ff41;
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        .prize-pool-label{{
            color:rgba(255, 255, 255, 0.9);
            font-size:1.5rem;
            text-transform:uppercase;
            letter-spacing:2px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        }}
        .prize-pool-value{{
            font-family:'Orbitron',sans-serif;
            color: #00ff41;
            font-size:clamp(3rem,10vw,5rem);
            font-weight:700;
            text-shadow: 0 0 20px rgba(0, 255, 65, 0.8), 2px 2px 4px rgba(0, 0, 0, 0.8);
            line-height:1.1;
            margin-bottom: 1rem;
        }}
        .bottles-total{{
            color:rgba(255, 255, 255, 0.9);
            font-size:1.2rem;
            font-weight:600;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        }}
        .bottles-number{{
            color: #00ff41;
            font-weight:700;
        }}
    </style>
    </head>
    <body>
        <div class="prize-pool-container">
            <div class="prize-pool-label">Prize Pool</div>
            <div id="prize-pool-counter" class="prize-pool-value"></div>
            <div class="bottles-total">
                Total Bottles Sold: <span class="bottles-number">{total_bottles:,}</span>
            </div>
        </div>
        <script type="module">
          import {{ CountUp }} from 'https://cdn.jsdelivr.net/npm/countup.js@2.0.7/dist/countUp.min.js';
          const options = {{prefix:'RM ',decimalPlaces:2,duration:1.5,separator:',',useEasing:true,}};
          const countUp = new CountUp('prize-pool-counter',{amount},options);
          if(!countUp.error){{countUp.start();}}else{{console.error(countUp.error);}}
        </script>
    </body>
    </html>
    """
    components.html(html_string, height=280)

# --- Create Leaderboard Section (Top 3 Only) ---
def create_leaderboard_section(crew_data, title):
    """Create a leaderboard section with only top 3 cards."""
    with st.container():
        if crew_data.empty:
            st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
            st.info("No data available")
            return
        
        # Section title
        st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
        
        # Top 3 cards only
        cols = st.columns(3)
        ranks = ["🥇", "🥈", "🥉"]
        
        for i in range(3):
            with cols[i]:
                if i < len(crew_data):
                    row = crew_data.iloc[i]
                    st.markdown(f"""
                    <div class="scorecard">
                        <div class="scorecard-rank">{ranks[i]}</div>
                        <div class="scorecard-name">{row['Crew_Name']}</div>
                        <div>
                            <div class="scorecard-sales">{row['Total Bottles Sold']}</div>
                            <div class="scorecard-label">Bottles Sold</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Empty placeholder to maintain layout
                    st.markdown(f"""
                    <div class="scorecard" style="opacity: 0.3; border-color: rgba(255,255,255,0.2);">
                        <div class="scorecard-rank">{ranks[i]}</div>
                        <div class="scorecard-name">No Data</div>
                        <div>
                            <div class="scorecard-sales">0</div>
                            <div class="scorecard-label">Bottles Sold</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# --- Main App ---
st_autorefresh(interval=30 * 1000, key="data_refresher")

# Apply background
desktop_image_url = "https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/main/suntory-desktop.jpg"
mobile_image_url = "https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/main/suntory-mobile.jpg"
apply_background_css(desktop_image_url, mobile_image_url)

# Wrap everything in a main container
st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

# Add header
st.markdown('''
<div class="main-header">
    SELL ANY <span class="toki-whisky">TOKI WHISKY</span> OR <span class="roku-gin">ROKU GIN</span> TO STAND A CHANCE TO WIN.
</div>
''', unsafe_allow_html=True)

df = load_data(CSV_URL)

if df is not None and not df.empty:
    prize_pool, ak_crew, d7_crew, total_bottles = calculate_flight_metrics(df)
    
    # Prize Pool
    PrizePoolComponent(prize_pool, total_bottles)
    
    # Side-by-side leaderboards for larger screens
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        create_leaderboard_section(ak_crew, "🛩️ AK Top Performers")
    
    with col2:
        create_leaderboard_section(d7_crew, "✈️ D7 Top Performers")
    
else:
    st.warning("Could not load data from the GitHub URL.")

st.markdown('</div>', unsafe_allow_html=True)
