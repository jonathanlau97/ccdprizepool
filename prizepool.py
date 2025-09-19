import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# --- Page Configuration ---
st.set_page_config(page_title="Flight Crew Prize Pool", layout="centered")

## Define the URL to your CSV file on GitHub
CSV_URL = 'https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/blob/main/flights_sales.csv'

# --- Main CSS (with Background Images) ---
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
                background-attachment: scroll; /* Better for mobile */
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
        
        /* Content overlay removed - no more white background */
        .main-content {{
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem;
        }}
        
        /* Leaderboard styling */
        .leaderboard-container {{
            display: flex;
            gap: 2rem;
            margin-top: 2rem;
        }}
        
        .leaderboard {{
            flex: 1;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }}
        
        .leaderboard-title {{
            color: #FFFFFF;
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1.5rem;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }}
        
        .crew-row {{
            display: flex;
            align-items: center;
            padding: 0.8rem;
            margin-bottom: 0.5rem;
            background: rgba(255, 255, 255, 0.25);
            border-radius: 10px;
            backdrop-filter: blur(5px);
            transition: all 0.3s ease;
        }}
        
        .crew-row.faded {{
            opacity: 0.4;
            background: rgba(255, 255, 255, 0.1);
        }}
        
        .crew-row:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}
        
        .crew-rank {{
            font-size: 1.5rem;
            font-weight: bold;
            width: 3rem;
            text-align: center;
            color: #FFFFFF;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }}
        
        .crew-info {{
            flex: 1;
            margin-left: 1rem;
        }}
        
        .crew-name {{
            color: #FFFFFF;
            font-size: 1.2rem;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
            margin-bottom: 0.2rem;
        }}
        
        .crew-bottles {{
            color: #00ff41;
            font-size: 1.4rem;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }}
        
        .crew-bottles-label {{
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
            margin-left: 0.5rem;
        }}
        
        /* Scorecard styling */
        
        /* Scorecard styling - removed white background */
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
        .prize-share-value{{color:#ff8800;font-size:1.5rem;font-weight:bold;line-height:1;text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);}}
        .prize-share-label{{color:rgba(255, 255, 255, 0.8);font-size:0.8rem;text-transform:uppercase;}}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            .leaderboard-container {{
                flex-direction: column;
                gap: 1rem;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)


# --- Function to wrap content in overlay ---
def create_content_wrapper():
    """Create a content wrapper without white background"""
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

def close_content_wrapper():
    """Close the content wrapper"""
    st.markdown('</div>', unsafe_allow_html=True)

# --- Function to create leaderboard ---
def create_leaderboard(crew_data, airline_name, airline_code):
    """Create a leaderboard for specific airline"""
    if crew_data.empty:
        return f"""
        <div class="leaderboard">
            <div class="leaderboard-title">{airline_name}</div>
            <div style="color: rgba(255, 255, 255, 0.8); text-align: center; padding: 2rem;">
                No data available
            </div>
        </div>
        """
    
    html = f"""
    <div class="leaderboard">
        <div class="leaderboard-title">{airline_name}</div>
    """
    
    ranks = ["🥇", "🥈", "🥉"]
    
    for i, (_, row) in enumerate(crew_data.iterrows()):
        rank_display = ranks[i] if i < 3 else f"#{i+1}"
        faded_class = "faded" if i >= 3 else ""
        
        html += f"""
        <div class="crew-row {faded_class}">
            <div class="crew-rank">{rank_display}</div>
            <div class="crew-info">
                <div class="crew-name">{row['Crew_Name']}</div>
                <div class="crew-bottles">{row['Total Bottles Credited']}<span class="crew-bottles-label">bottles</span></div>
            </div>
        </div>
        """
    
    html += "</div>"
    return html


# --- Cached Data Functions for Performance ---
@st.cache_data
def load_data(url):
    """Reads, cleans, and caches the CSV data from a URL."""
    try:
        df = pd.read_csv(url)
        required_cols = ['Flight_ID', 'Flight_Date', 'Crew_ID', 'Crew_Name', 'Bottles_Sold_on_Flight', 'Airline_Code']
        if all(col in df.columns for col in required_cols):
            df['Flight_Date'] = pd.to_datetime(df['Flight_Date'], errors='coerce')
            df.dropna(subset=['Flight_Date'], inplace=True)
            return df
        else:
            st.error(f"CSV from URL is missing one or more required columns: {required_cols}")
            return None
    except Exception as e:
        st.error(f"Error reading data from the GitHub URL: {e}")
        return None

@st.cache_data
def calculate_flight_metrics(_df):
    """Calculates prize pool and airline leaderboards from a dataframe."""
    if _df.empty:
        return 0.00, pd.DataFrame(), pd.DataFrame()
        
    unique_flights_df = _df.drop_duplicates(subset=['Flight_ID'])
    total_bottles = unique_flights_df['Bottles_Sold_on_Flight'].sum()
    prize_pool = total_bottles * 5.00
    
    # Create leaderboards by airline
    ak_crew = _df[_df['Airline_Code'] == 'AK'].groupby(['Crew_ID', 'Crew_Name'])['Bottles_Sold_on_Flight'] \
                 .sum() \
                 .reset_index(name='Total Bottles Credited') \
                 .sort_values(by='Total Bottles Credited', ascending=False) \
                 .head(10)
                 
    d7_crew = _df[_df['Airline_Code'] == 'D7'].groupby(['Crew_ID', 'Crew_Name'])['Bottles_Sold_on_Flight'] \
                 .sum() \
                 .reset_index(name='Total Bottles Credited') \
                 .sort_values(by='Total Bottles Credited', ascending=False) \
                 .head(10)
            
    return prize_pool, ak_crew, d7_crew


# --- Self-Contained Prize Pool Component with Embedded Styles ---
def PrizePoolComponent(amount):
    """Renders the animated prize pool component with all its styles included."""
    html_string = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        /* ## CHANGED: White Theme for Prize Pool Component */
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
    
    # Prize Pool Component (no white background overlay)
    PrizePoolComponent(prize_pool)
    
    # Create side-by-side leaderboards
    st.markdown("""
    <div class="leaderboard-container">
    """ + create_leaderboard(ak_crew, "AirAsia", "AK") + 
    create_leaderboard(d7_crew, "AirAsia X", "D7") + """
    </div>
    """, unsafe_allow_html=True)
    
else:
    st.warning("Could not load data from the specified GitHub URL. Please check the URL and ensure the repository is public.")

