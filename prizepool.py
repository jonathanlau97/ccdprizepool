import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# --- Page Configuration ---
st.set_page_config(page_title="Flight Crew Prize Pool", layout="centered")

## Define the URL to your CSV file on GitHub
CSV_URL = 'https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/main/flights_sales.csv'

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
        
        /* Main content wrapper */
        .main-wrapper {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        /* Section titles */
        .section-title {{
            color: #FFFFFF;
            font-size: 1.8rem;
            font-weight: bold;
            text-align: center;
            margin: 2rem 0 1rem 0;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        /* Scorecard styling */
        .scorecard {{
            background-color: rgba(255, 255, 255, 0.15);
            border: 2px solid #00ff41;
            border-radius:15px;
            padding:1.5rem;
            text-align:center;
            height:100%;
            display:flex;
            flex-direction:column;
            justify-content:center;
            gap:0.5rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            margin-bottom: 1rem;
        }}
        .scorecard-rank{{
            font-size:2.5rem;
            font-weight:bold;
            margin-bottom:0.25rem;
            color:#FFFFFF;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
        }}
        .scorecard-name{{
            color:#FFFFFF;
            font-size:1.4rem;
            font-weight:bold;
            word-wrap:break-word;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
        }}
        .scorecard-sales{{
            color:#00ff41;
            font-size:2rem;
            font-weight:bold;
            line-height:1;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
        }}
        .scorecard-label{{
            color:rgba(255, 255, 255, 0.9);
            font-size:0.9rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        }}
        
        /* Top 10 list container */
        .top-10-list {{
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        /* Top 10 individual rows */
        .top-10-row {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 0.8rem;
            margin: 0.5rem 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .position-number {{
            color: #00ff41;
            font-weight: bold;
            font-size: 1.2rem;
            min-width: 40px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        }}
        
        .crew-name {{
            color: #FFFFFF;
            font-weight: 600;
            flex: 1;
            margin: 0 1rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        }}
        
        .bottles-count {{
            color: #00ff41;
            font-weight: bold;
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
        required_cols = ['Flight_ID', 'Flight_Date', 'Crew_ID', 'Crew_Name', 'Bottles_Sold_on_Flight']
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
        return 0.00, pd.DataFrame(), pd.DataFrame()
        
    unique_flights_df = _df.drop_duplicates(subset=['Flight_ID'])
    total_bottles = unique_flights_df['Bottles_Sold_on_Flight'].sum()
    prize_pool = total_bottles * 5.00
    
    # AK leaderboard
    ak_crew = _df[_df['Airline_Code'] == 'AK'].groupby(['Crew_ID', 'Crew_Name'])['Bottles_Sold_on_Flight'] \
                 .sum() \
                 .reset_index(name='Total Bottles Credited') \
                 .sort_values(by='Total Bottles Credited', ascending=False) \
                 .head(10)
                 
    # D7 leaderboard
    d7_crew = _df[_df['Airline_Code'] == 'D7'].groupby(['Crew_ID', 'Crew_Name'])['Bottles_Sold_on_Flight'] \
                 .sum() \
                 .reset_index(name='Total Bottles Credited') \
                 .sort_values(by='Total Bottles Credited', ascending=False) \
                 .head(10)
            
    return prize_pool, ak_crew, d7_crew

# --- Prize Pool Component ---
def PrizePoolComponent(amount):
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
        }}
    </style>
    </head>
    <body>
        <div class="prize-pool-container">
            <div class="prize-pool-label">Current Prize Pool</div>
            <div id="prize-pool-counter" class="prize-pool-value"></div>
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
    components.html(html_string, height=230)

# --- Create Leaderboard Section ---
def create_leaderboard_section(crew_data, title):
    """Create a complete leaderboard section with top 3 cards and remaining list."""
    if crew_data.empty:
        st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
        st.info("No data available")
        return
    
    # Section title
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    
    # Top 3 cards
    if len(crew_data) >= 1:
        cols = st.columns(min(3, len(crew_data)))
        ranks = ["🥇", "🥈", "🥉"]
        
        for i, (_, row) in enumerate(crew_data.head(3).iterrows()):
            with cols[i]:
                st.markdown(f"""
                <div class="scorecard">
                    <div class="scorecard-rank">{ranks[i]}</div>
                    <div class="scorecard-name">{row['Crew_Name']}</div>
                    <div>
                        <div class="scorecard-sales">{row['Total Bottles Credited']}</div>
                        <div class="scorecard-label">Bottles Credited</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Remaining positions (4-10) in a styled list
    if len(crew_data) > 3:
        remaining_crew = crew_data.iloc[3:10]
        remaining_html = '<div class="top-10-list">'
        
        for idx, (_, row) in enumerate(remaining_crew.iterrows()):
            position = idx + 4  # This correctly gives us positions 4, 5, 6, 7, 8, 9, 10
            crew_name = str(row['Crew_Name']).replace('"', '&quot;').replace("'", "&#x27;")
            bottles = int(row['Total Bottles Credited'])
            
            remaining_html += f'''
            <div class="top-10-row">
                <div class="position-number">#{position}</div>
                <div class="crew-name">{crew_name}</div>
                <div class="bottles-count">{bottles} bottles</div>
            </div>
            '''
        
        remaining_html += '</div>'
        st.markdown(remaining_html, unsafe_allow_html=True)

# --- Main App ---
st_autorefresh(interval=30 * 1000, key="data_refresher")

# Apply background
desktop_image_url = "https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/main/suntory-desktop.jpg"
mobile_image_url = "https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/main/suntory-mobile.jpg"
apply_background_css(desktop_image_url, mobile_image_url)

# Wrap everything in a main container
st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

df = load_data(CSV_URL)

if df is not None and not df.empty:
    prize_pool, ak_crew, d7_crew = calculate_flight_metrics(df)
    
    # Prize Pool
    PrizePoolComponent(prize_pool)
    
    # AirAsia Leaderboard
    create_leaderboard_section(ak_crew, "🛩️ AirAsia Top Performers")
    
    # AirAsia X Leaderboard
    create_leaderboard_section(d7_crew, "✈️ AirAsia X Top Performers")
    
else:
    st.warning("Could not load data from the GitHub URL.")

st.markdown('</div>', unsafe_allow_html=True)
