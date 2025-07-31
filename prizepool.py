import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# --- Page Configuration ---
st.set_page_config(page_title="Flight Crew Prize Pool", layout="centered")

# --- Custom CSS with NEW Pulse Animation ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');

/* ADDED: Keyframes for the pulsing glow effect */
@keyframes pulse-glow {
  0% { box-shadow: 0 0 30px rgba(0, 255, 65, 0.4); }
  50% { box-shadow: 0 0 55px rgba(0, 255, 65, 0.9); }
  100% { box-shadow: 0 0 30px rgba(0, 255, 65, 0.4); }
}

.prize-pool-container {
    background-color: #000;
    border: 5px solid #444;
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 2rem;
    /* APPLIED: The new animation */
    animation: pulse-glow 3s infinite ease-in-out;
}
.prize-pool-label {
    color: #ccc;
    font-size: 1.5rem;
    text-transform: uppercase;
    letter-spacing: 2px;
}
.prize-pool-value {
    font-family: 'Orbitron', sans-serif;
    color: #00ff41;
    font-size: clamp(3rem, 10vw, 6rem);
    font-weight: 700;
    text-shadow: 0 0 20px #00ff41;
    line-height: 1.1;
}

/* Scorecard styles (unchanged) */
.scorecard{background-color:#1a1a1a;border:2px solid #555;border-radius:15px;padding:1.5rem;text-align:center;height:100%;display:flex;flex-direction:column;justify-content:center}.scorecard-rank{font-size:2.5rem;font-weight:bold;margin-bottom:.5rem}.scorecard-name{font-size:1.4rem;font-weight:bold;color:#fff;word-wrap:break-word}.scorecard-id{font-size:1rem;color:#aaa;margin-bottom:1rem}.scorecard-sales{font-size:2rem;font-weight:bold;color:#00ff41}.scorecard-label{font-size:.9rem;color:#aaa}
</style>
""", unsafe_allow_html=True)

# --- Data Processing Function (unchanged) ---
def calculate_flight_metrics(df):
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

# --- Prize Pool HTML Component with Count-Up JS ---
def PrizePoolComponent(amount):
    # This HTML block now includes the CountUp.js library and the script to run it
    html_string = f"""
    <div class="prize-pool-container">
        <div class="prize-pool-label">Prize Pool for Selected Period</div>
        <div id="prize-pool-counter" class="prize-pool-value"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/countup.js@2.0.7/dist/countUp.min.js"></script>
    <script>
      // Wait for the document to be fully loaded
      document.addEventListener('DOMContentLoaded', function() {{
        const options = {{
          prefix: 'RM ', // Add currency prefix
          decimalPlaces: 2,
          duration: 2.5, // Animation duration in seconds
          separator: ',',
          useEasing: true,
        }};
        // Create a new CountUp instance
        let countUp = new CountUp('prize-pool-counter', {amount}, options);
        if (!countUp.error) {{
          // Start the animation
          countUp.start();
        }} else {{
          console.error(countUp.error);
        }}
      }});
    </script>
    """
    # Use the components.html function to render it
    components.html(html_string, height=220)


# --- Streamlit App Layout ---
st.title("✈️ Flight Crew Prize Pool")

# Initialize session state
if 'full_df' not in st.session_state:
    st.session_state.full_df = pd.DataFrame()

with st.expander("⚙️ Upload Flight Roster CSV"):
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
    if uploaded_file:
        try:
            temp_df = pd.read_csv(uploaded_file)
            required_cols = ['Flight_ID', 'Flight_Date', 'Crew_ID', 'Crew_Name', 'Bottles_Sold_on_Flight']
            if all(col in temp_df.columns for col in required_cols):
                temp_df['Flight_Date'] = pd.to_datetime(temp_df['Flight_Date'], errors='coerce')
                temp_df.dropna(subset=['Flight_Date'], inplace=True)
                st.session_state.full_df = temp_df
                st.success(f"Successfully loaded {len(st.session_state.full_df)} roster records.")
            else:
                st.error(f"CSV is missing one or more required columns: {required_cols}")
        except Exception as e:
            st.error(f"Error processing file: {e}")

# --- Main App Body ---
if not st.session_state.full_df.empty:
    df = st.session_state.full_df

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
        
        # --- REPLACED: Call the new HTML component ---
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
        st.warning("Please select a valid start and end date.")
else:
    st.info("Upload a flight roster CSV to begin.")