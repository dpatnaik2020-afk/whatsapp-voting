import datetime
import pandas as pd
import streamlit as st
from zoneinfo import ZoneInfo
from streamlit_gsheets import GSheetsConnection

# ==================== CONFIGURATION ====================
ELECTION_TITLE = "Class / Group Voting System"
CANDIDATES = ["ANEESH SAHU", "DARSHIL PATNAIK", "DIPAK KUMAR PRADHAN","SAHIL SAMBHAV SWAIN"]

# Set your deadline year, month, day, hour, minute
DEADLINE = datetime.datetime(2026, 7, 30, 19, 25, 7, tzinfo=ZoneInfo("Asia/Kolkata"))

# =======================================================

st.set_page_config(page_title=ELECTION_TITLE, page_icon="🗳️", layout="centered")

st.title(f"🗳️ {ELECTION_TITLE}")
st.write(
    "Cast your vote securely. Everyone will be able to audit who voted for whom"
    " *after* the deadline passes."
)

# Initialize Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Read existing votes from the Google Sheet (ttl=0 ensures it fetches live data)
try:
    existing_data = conn.read(worksheet="Sheet1", ttl=0)
    if existing_data.empty or list(existing_data.columns) != ["Voter Name", "Candidate", "Timestamp"]:
        st.session_state.votes = pd.DataFrame(columns=["Voter Name", "Candidate", "Timestamp"])
    else:
        st.session_state.votes = existing_data.dropna(subset=["Voter Name"])
except Exception:
    st.session_state.votes = pd.DataFrame(columns=["Voter Name", "Candidate", "Timestamp"])

now = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))

st.info(f"⏳ **Deadline:** {DEADLINE.strftime('%B %d, %Y - %I:%M %p')}")

if now > DEADLINE:
    st.error("🚨 **Voting has officially CLOSED!** Here is the final public audit:")

    if st.session_state.votes.empty:
        st.warning("No votes were cast.")
    else:
        st.dataframe(st.session_state.votes, use_container_width=True)
        st.subheader("📊 Final Tally")
        tally = st.session_state.votes["Candidate"].value_counts().reset_index()
        tally.columns = ["Candidate", "Total Votes"]
        st.bar_chart(tally.set_index("Candidate"))

else:
    st.subheader("Cast Your Vote")
    with st.form("voting_form"):
        voter_name = st.text_input(
            "Your Full Name (Required for public transparency)"
        )
        chosen_candidate = st.selectbox("Select Candidate", CANDIDATES)
        submit_button = st.form_submit_button("Submit Vote")

        if submit_button:
            if not voter_name.strip():
                st.warning("⚠️ Please enter your name to cast a vote.")
            elif voter_name.strip() in st.session_state.votes["Voter Name"].values:
                st.error(
                    "❌ You have already cast a vote! Multiple voting is not"
                    " permitted."
                )
            else:
                new_vote = pd.DataFrame(
                    [{
                        "Voter Name": voter_name.strip(),
                        "Candidate": chosen_candidate,
                        "Timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    }]
                )
                
               # Append to current session state dataframe
                updated_votes = pd.concat(
                    [st.session_state.votes, new_vote], ignore_index=True
                )
                
                # Update Google Sheet using the native connection update method
                conn.update(worksheet="Sheet1", data=updated_votes)
                
                st.session_state.votes = updated_votes
                
                st.success(
                    f"✅ Thank you, {voter_name}! Your vote for **{chosen_candidate}**"
                    " has been recorded."
                )
                st.rerun()

    st.markdown("---")
    st.write(f"👥 **Total votes cast so far:** {len(st.session_state.votes)}")
    if not st.session_state.votes.empty:
        voted_list = st.session_state.votes[["Voter Name", "Timestamp"]].copy()
        voted_list["Status"] = "Voted ✅"
        st.table(voted_list)
