import streamlit as st
import pandas as pd
import plotly.express as px

# Browser tab parameters setup
st.set_page_config(page_title="Global & Mauritania Job Market Radar", page_icon="📊", layout="centered")

# --- VISUAL ENHANCEMENT: APPEALING TITLE & AUTHOR TAG ---
st.title("🚀 Global & Mauritania Job Market Intelligence Radar")
st.caption("Developed by **Mohsin Aboubekrine** | Freelance Data Analyst")

st.markdown("""
---
### 📈 Real-Time Data Insights Hub
Automated intelligence engine tracking employment vacancies across **LinkedIn (Worldwide)** and local Mauritanian portals (*Emploi Mauritanie, Novojob, Beta Conseils, and Techghil*).
""")

# Reads the dataset file produced locally by your scraper script
CSV_FILE = "mauritania_all_data_jobs.csv"

try:
    df = pd.read_csv(CSV_FILE)
    
    if not df.empty and df['Job Count'].sum() > 0:
        
        # --- DRILL-DOWN OPTION A: SIDEBAR DROPDOWN SELECTOR ---
        st.sidebar.header("🔮 Navigation Control")
        
        # Explicitly list all platforms so they always appear in your UI dropdown
        platform_options = [
            "All Platforms",
            "Techghil",
            "Beta Conseils",
            "Novojob",
            "Emploi Mauritanie",
            "LinkedIn",
            "Rimtic",
            "Arbeitnow (Worldwide)"
        ]
        
        selected_platform = st.sidebar.selectbox("Isolate Job Board Target:", options=platform_options)
        
        if selected_platform != "All Platforms":
            filtered_df = df[df['Source Platform'] == selected_platform]
            if "LinkedIn" in selected_platform:
                chart_title = f"✨ Market Demand Distribution: {selected_platform} (Worldwide)"
            else:
                chart_title = f"✨ Market Demand Distribution: {selected_platform} (Mauritania)"
            color_slice = None
        else:
            filtered_df = df
            chart_title = "✨ Aggregated Market Demand Matrix (Local & Global)"
            color_slice = 'Source Platform'
            
        # Build horizontal visualization presentation
        fig = px.bar(
            filtered_df,
            x='Job Count',
            y='Job Category',
            orientation='h',
            color=color_slice,
            text='Job Count',
            title=chart_title,
            labels={'Job Count': 'Total Live Vacancies', 'Job Category': 'Standardized Industry Field'},
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            legend_title_text="Data Source",
            title_font_size=16,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # High-level aggregated metric readouts
        st.subheader("📊 Key Performance Indicators")
        m1, m2 = st.columns(2)
        m1.metric("Total Active Listings", int(filtered_df['Job Count'].sum()))
        m2.metric("Specialized Sectors Monitored", len(filtered_df['Job Category'].unique()))
        
    else:
        st.warning("⚠️ Data workspace frame initialized but empty. Re-verify scraper script pipelines.")

except Exception as e:
    st.info("💡 Data source file not found. Execute your 'python scraper.py' engine in the terminal to generate active analytics.")