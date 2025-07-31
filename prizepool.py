import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(page_title="Flight Crew Prize Pool", layout="centered")

# --- Custom CSS with Pulse Animation ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');
@keyframes pulse-glow {
  0% { box-shadow: 0 0 30px rgba(0, 255, 65, 0.4); }
  50% { box-shadow: 0 0 55px rgba(0, 255, 65, 0.9); }
  100% { box-shadow: 0 0 30px rgba(0, 255, 65, 0.4); }
}
.prize-pool-container{background-color:#000;border:5px solid #444;border-radius:20px;padding:2rem;text-align:center;margin-bottom:2rem;animation:pulse-glow 3s infinite ease-in-out}.prize-pool-label{color:#ccc;font-size:1.5rem;text-transform:uppercase;letter-spacing:2px}.prize-pool-value{font-family:'Orbitron',sans-serif;color:#00ff41;font-size:clamp(3rem,10vw,6rem);font-weight:700;text-shadow:0 0 20px #00ff41;line-height:1.1}.scorecard{background-color:#1a1a1a;border:2px solid #555;border-radius:15px;padding:1.5rem;text-align:center;height:100%;display:flex;flex-direction:column;justify-content:center}.scorecard-rank{font-size:2.5rem;font-weight:bold;margin-bottom:.5rem}.scorecard-name{font-size:1.4rem;font-weight:bold;color:#fff;word-wrap:break-word}.scorecard-id{font-size:1rem;color:#aaa;margin-bottom:1rem}.scorecard-sales{font-size:2rem;font-weight:bold;color:#00ff41}.scorecard-label{font-size:.9rem;color:#aaa}
</style>
""", unsafe_allow_html=True)


# --- Cached Data Functions for Performance ---

@st.cache_data
def load_data(uploaded_file):
    """Reads, cleans, and caches the uploaded CSV data."""
    try:
        temp_df = pd.read_csv(uploaded_file)
        required_cols = ['Flight_ID', 'Flight_Date', 'Crew_ID', 'Crew_Name', 'Bottles_Sold_on_Flight']
        if all(col in temp_df.columns for col in required_cols):
            temp_df['Flight_Date'] = pd.to_datetime(temp_df['Flight_Date'], errors='coerce')
            temp_df.dropna(subset=['Flight_Date'], inplace=True)
            return temp_df
        else:
            st.error(f"CSV is missing one or more required columns: {required_cols}")
            return None
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

@st.cache_data
def calculate_flight_metrics(df):
    """Calculates prize pool and top crew from a dataframe."""
    if df.empty:
        return 0.00, pd.DataFrame()
    unique_flights_df = df.drop_duplicates(subset=['Flight_ID'])
    total_bottles = unique_flights_df['Bottles_Sold_on_Flight'].sum()
    prize_pool = total_bottles * 5.00
    top_crew = df.groupby(['Crew_ID', 'Crew_Name'])['Bottles_Sold_on_Flight'] \
                 .sum() \
                 .reset_index(name='Total Bottles Credited') \
                 .sort_values(by='Total Bottles Credited', ascending=False) \
                 .head(3)
    return prize_pool, top_crew


# --- Main Component with CORRECTED JavaScript ---

def PrizePoolComponent(amount):
    """Renders the animated prize pool component."""
    html_string = f"""
    <div class="prize-pool-container">
        <div class="prize-pool-label">Prize Pool for Selected Period</div>
        <div id="prize-pool-counter" class="prize-pool-value"></div>
    </div>

    <script type="module">
      // Import the CountUp class directly from the CDN URL
      import {{ CountUp }} from 'https://cdn.jsdelivr.net/npm/countup.js@2.0.7/dist/countUp.min.js';

      const options = {{
        prefix: 'RM ',
        decimalPlaces: 2,
        duration: 2.5,
        separator: ',',
        useEasing: true,
      }};
      
      const countUp = new CountUp('prize-pool-counter', {amount}, options);
      if (!countUp.error) {{
        countUp.start();
      }} else {{
        console.error(countUp.error);
      }}
    </script>
    """
    components.html(html_string, height=220)


# --- Streamlit App Layout ---

st.title("✈️ Flight Crew Prize Pool")

with st.expander("⚙️ Upload Flight Roster CSV"):
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

df = None
if uploaded_file:
    df = load_data(uploaded_file)

if df is not None and not df.empty:
    min_date = df['Flight_Date'].min().date()
    max_date = df['Flight_Date'].max().date()
    
    selected_date_range = st.date_input(
        "Select a date range for flights",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY"
    )

    if len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        mask = (df['Flight_Date'].dt.date >= start_date) & (df['Flight_Date'].dt.date <= end_date)
        filtered_df = df.loc[mask]

        prize_pool, top_crew = calculate_flight_metrics(filtered_df)
        
        PrizePoolComponent(prize_pool)

        st.header("🏆 Top Performing Crew")
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
                            <div class="scorecard-sales">{row['Total Bottles Credited']}</div>
                            <div class="scorecard-label">Total Bottles Credited</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("No flight data available for the selected date range.")
else:
    st.info("Upload a flight roster CSV to begin.")
