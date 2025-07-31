import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# --- Page Configuration ---
st.set_page_config(page_title="Flight Crew Prize Pool", layout="centered")

## Define the URL to your CSV file on GitHub
CSV_URL = 'https://raw.githubusercontent.com/jonathanlau97/ccdprizepool/main/flights_sales.csv'

# --- Main CSS (with Bento Layout adjustments) ---
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a1a;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.75rem;
    }
    .stApp > header {
        display: none;
    }
    .scorecard{background-color:#222;border:2px solid #444;border-radius:15px;padding:1.5rem;text-align:center;height:100%;display:flex;flex-direction:column;justify-content:center;gap:0.5rem;}
    .scorecard-rank{font-size:2.5rem;font-weight:bold;margin-bottom:0.25rem}
    .scorecard-name{font-size:1.4rem;font-weight:bold;color:#fff;word-wrap:break-word}
    .scorecard-id{font-size:1rem;color:#aaa;}
    .scorecard-sales{font-size:2rem;font-weight:bold;color:#00ff41;line-height:1;}
    .scorecard-label{font-size:0.9rem;color:#aaa;}
    .prize-share-value{font-size:1.5rem;font-weight:bold;color:#f0ad4e;line-height:1;}
    .prize-share-label{font-size:0.8rem;color:#aaa;text-transform:uppercase;}
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
            return df
        else:
            st.error(f"CSV from URL is missing one or more required columns: {required_cols}")
            return None
    except Exception as e:
        st.error(f"Error reading data from the GitHub URL: {e}")
        return None

@st.cache_data
def calculate_flight_metrics(_df):
    """Calculates prize pool and top crew from a dataframe."""
    if _df.empty:
        return 0.00, pd.DataFrame()
        
    unique_flights_df = _df.drop_duplicates(subset=['Flight_ID'])
    total_bottles = unique_flights_df['Bottles_Sold_on_Flight'].sum()
    prize_pool = total_bottles * 5.00
    
    top_crew = _df.groupby(['Crew_ID', 'Crew_Name'])['Bottles_Sold_on_Flight'] \
                 .sum() \
                 .reset_index(name='Total Bottles Credited') \
                 .sort_values(by='Total Bottles Credited', ascending=False) \
                 .head(3)

    if not top_crew.empty:
        total_top_crew_bottles = top_crew['Total Bottles Credited'].sum()
        if total_top_crew_bottles > 0:
            top_crew['Prize Share'] = (top_crew['Total Bottles Credited'] / total_top_crew_bottles) * prize_pool
        else:
            top_crew['Prize Share'] = 0.0
            
    return prize_pool, top_crew


# --- Self-Contained Prize Pool Component with Embedded Styles ---
def PrizePoolComponent(amount):
    """Renders the animated prize pool component with all its styles included."""
    html_string = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');
        @keyframes pulse-glow {{
          0% {{ box-shadow: 0 0 15px rgba(0, 255, 65, 0.5); }}
          50% {{ box-shadow: 0 0 30px rgba(0, 255, 65, 0.8); }}
          100% {{ box-shadow: 0 0 15px rgba(0, 255, 65, 0.5); }}
        }}
        body{{margin:0;padding:0;}}
        .prize-pool-container{{
            background-color:#000;
            border: 2px solid #333;
            border-radius: 0;
            padding:2rem;
            text-align:center;
            animation: pulse-glow 2.5s infinite ease-in-out;
        }}
        .prize-pool-label{{color:#ccc;font-size:1.5rem;text-transform:uppercase;letter-spacing:2px;}}
        .prize-pool-value{{font-family:'Orbitron',sans-serif;color:#00ff41;font-size:clamp(3rem,10vw,5rem);font-weight:700;text-shadow:0 0 20px #00ff41;line-height:1.1;}}
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

# The st.title has been removed

df = load_data(CSV_URL)

if df is not None and not df.empty:
    prize_pool, top_crew = calculate_flight_metrics(df)
    
    PrizePoolComponent(prize_pool)

    # Use markdown for a white header
    st.markdown("<h2 style='text-align: center; color: white;'>🏆 Top Performing Crew</h2>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    ranks = ["🥇", "🥈", "🥉"]

    if not top_crew.empty:
        for i, (index, row) in enumerate(top_crew.iterrows()):
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="scorecard">
                        <div class="scorecard-rank">{ranks[i]}</div>
                        <div class="scorecard-name">{row['Crew_Name']}</div>
                        <div class="scorecard-id">ID: {row['Crew_ID']}</div>
                        <div>
                            <div class="scorecard-sales">{row['Total Bottles Credited']}</div>
                            <div class="scorecard-label">Bottles Credited</div>
                        </div>
                        <div>
                            <div class="prize-share-value">RM {row.get('Prize Share', 0):,.2f}</div>
                            <div class="prize-share-label">Prize Share</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No flight data available to display.")
else:
    st.warning("Could not load data from the specified GitHub URL. Please check the URL and ensure the repository is public.")
