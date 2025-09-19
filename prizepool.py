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
        
        /* Scorecard styling - glass effect on background */
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
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }}
        .scorecard-rank{{font-size:2.5rem;font-weight:bold;margin-bottom:0.25rem;color:#FFFFFF;text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);}}
        .scorecard-name{{color:#FFFFFF;font-size:1.4rem;font-weight:bold;word-wrap:break-word;text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);}}
        .scorecard-sales{{color:#00ff41;font-size:2rem;font-weight:bold;line-height:1;text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);}}
        .scorecard-label{{color:rgba(255, 255, 255, 0.8);font-size:0.9rem;}}
        
        /* Top 10 list styling */
        .top-10-container {{
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 15px;
            padding: 1.5rem;
            margin-top: 1rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }}
        .top-10-title {{
            color: #FFFFFF;
            font-size: 1.2rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }}
        .crew-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.8rem;
            margin-bottom: 0.5rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            backdrop-filter: blur(5px);
            opacity: 0.7;
            transition: all 0.3s ease;
        }}
        .crew-row:hover {{
            opacity: 1;
            transform: translateX(5px);
        }}
        .crew-position {{
            color: rgba(255, 255, 255, 0.9);
            font-weight: bold;
            font-size: 1.1rem;
            width: 2.5rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }}
        .crew-name-small {{
            color: #FFFFFF;
            font-weight: 600;
            flex: 1;
            margin-left: 1rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }}
        .crew-bottles-small {{
            color: #00ff41;
            font-weight: bold;
            font-size: 1.1rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }}
    </style>
    """, unsafe_allow_html=True)

# --- Cached Data Functions for Performance ---
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
            st.error(f"CSV from URL is missing one or more required columns: {required_cols}")
            return None
    except Exception as e:
        st.error(f"Error reading data from the GitHub URL: {e}")
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

# --- Function to create top 10 list ---
def create_top_10_list(crew_data, title):
    """Create a top 10 list showing positions 4-10"""
    if len(crew_data) <= 3:
        return ""
    
    remaining_crew = crew_data.iloc[3:10]  # Get positions 4-10
    
    html = f"""
    <div class="top-10-container">
        <div class="top-10-title">{title} - Positions 4-10</div>
    """
    
    for i, (_, row) in enumerate(remaining_crew.iterrows(), start=4):
        html += f"""
        <div class="crew-row">
            <div class="crew-position">#{i}</div>
            <div class="crew-name-small">{row['Crew_Name']}</div>
            <div class="crew-bottles-small">{row['Total Bottles Credited']} bottles</div>
        </div>
        """
    
    html += "</div>"
    return html
def PrizePoolComponent(amount):
    """Renders the animated prize pool component."""
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
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }}
        .prize-pool-label{{color:rgba(255, 255, 255, 0.9);font-size:1.5rem;text-transform:uppercase;letter-spacing:2px;text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);}}
        .prize-pool-value{{
            font-family:'Orbitron',sans-serif;
            color: #00ff41;
            font-size:clamp(3rem,10vw,5rem);
            font-weight:700;
            text-shadow: 0 0 20px rgba(0, 255, 65, 0.8), 2px 2px 4px rgba(0, 0, 0, 0.5);
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

# --- Streamlit App Layout ---
st_autorefresh(interval=30 * 1000, key="data_refresher")

# Apply background images
desktop_image_url = "https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/main/suntory-desktop.jpg"
mobile_image_url = "https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/main/suntory-mobile.jpg"
apply_background_css(desktop_image_url, mobile_image_url)

df = load_data(CSV_URL)

if df is not None and not df.empty:
    prize_pool, ak_crew, d7_crew = calculate_flight_metrics(df)
    
    # Prize Pool Component
    PrizePoolComponent(prize_pool)
    
    # AirAsia Leaderboard
    st.markdown("### 🛩️ AirAsia Top Performers", unsafe_allow_html=True)
    if not ak_crew.empty:
        # Top 3 cards
        cols = st.columns(min(3, len(ak_crew)))
        ranks = ["🥇", "🥈", "🥉"]
        
        for i, (index, row) in enumerate(ak_crew.head(3).iterrows()):
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="scorecard">
                        <div class="scorecard-rank">{ranks[i]}</div>
                        <div class="scorecard-name">{row['Crew_Name']}</div>
                        <div>
                            <div class="scorecard-sales">{row['Total Bottles Credited']}</div>
                            <div class="scorecard-label">Bottles Credited</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Top 10 list (positions 4-10)
        if len(ak_crew) > 3:
            st.markdown(create_top_10_list(ak_crew, "AirAsia"), unsafe_allow_html=True)
    
    # AirAsia X Leaderboard  
    st.markdown("### ✈️ AirAsia X Top Performers", unsafe_allow_html=True)
    if not d7_crew.empty:
        # Top 3 cards
        cols = st.columns(min(3, len(d7_crew)))
        ranks = ["🥇", "🥈", "🥉"]
        
        for i, (index, row) in enumerate(d7_crew.head(3).iterrows()):
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="scorecard">
                        <div class="scorecard-rank">{ranks[i]}</div>
                        <div class="scorecard-name">{row['Crew_Name']}</div>
                        <div>
                            <div class="scorecard-sales">{row['Total Bottles Credited']}</div>
                            <div class="scorecard-label">Bottles Credited</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Top 10 list (positions 4-10)
        if len(d7_crew) > 3:
            st.markdown(create_top_10_list(d7_crew, "AirAsia X"), unsafe_allow_html=True)
else:
    st.warning("Could not load data from the specified GitHub URL. Please check the URL and ensure the repository is public.")
