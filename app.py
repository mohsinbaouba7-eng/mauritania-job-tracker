import streamlit as st
import pandas as pd
import os

# Browser tab parameters setup
st.set_page_config(page_title="Global & Mauritania Job Market Radar", page_icon="📊", layout="centered")

# --- VISUAL ENHANCEMENT: APPEALING TITLE & AUTHOR TAG ---
st.title("🚀 Global & Mauritania Job Market Intelligence Radar")
st.caption("Developed by **Mohsin Aboubekrine** | Freelance Data Analyst")

st.markdown("""
---
### 📊 Real-Time Data Insights Hub
Automated intelligence engine tracking employment vacancies across **LinkedIn (Worldwide)**, **Indeed**, and local Mauritanian portals (*Emploi Mauritanie*, *Novojob*, *Beta Conseils*, and *Techghil*).
""")

# Reads the dataset file produced locally by your scraper script
CSV_FILE = "mauritania_all_data_jobs.csv"

# Check if the file exists explicitly first
if not os.path.exists(CSV_FILE):
    st.error(f"❌ File **'{CSV_FILE}'** was not found in this folder. Please make sure your scraper runs and creates it here: {os.getcwd()}")
else:
    try:
        df = pd.read_csv(CSV_FILE)
        
        if df.empty:
            st.warning("⚠️ The CSV file was found, but it contains no rows of data.")
        else:
            # --- DYNAMIC COLUMN DETECTOR ---
            platform_col = next((c for c in df.columns if c.lower() in ['source platform', 'platform', 'source']), None)
            category_col = next((c for c in df.columns if c.lower() in ['job category', 'category', 'job field', 'job title', 'title']), None)
            count_col = next((c for c in df.columns if c.lower() in ['job count', 'count', 'jobs']), None)

            if not category_col or not count_col:
                st.error(f"❌ Missing required columns. Your CSV columns are: {list(df.columns)}")
            else:
                # --- SIDEBAR INTERFACE CONTROLS ---
                st.sidebar.header("🗺️ Navigation Control")

                # Core platform targets (Indeed cleanly matched to your grouping output)
                platform_options = [
                    "All Platforms", 
                    "Techghil", 
                    "Beta Conseils", 
                    "Novojob",
                    "Emploi Mauritanie", 
                    "LinkedIn", 
                    "Indeed",
                    "Rimtic", 
                    "Arbeitnow Worldwide"
                ]
                selected_platform = st.sidebar.selectbox("Isolate Job Board Target:", options=platform_options)

                # --- TARGETED JOB MULTILINGUAL DETECTOR ---
                def normalize_category(val):
                    if not isinstance(val, str):
                        return "Other"
                    val_lower = val.lower()
                    
                    if "bi " in val_lower or "business intelligence" in val_lower or "informatique décisionnelle" in val_lower:
                        return "BI Intelligence Analyst"
                    if "scientist" in val_lower or "science des données" in val_lower or "cientista de dados" in val_lower:
                        if "data" in val_lower or "donn" in val_lower:
                            return "Data Scientist"
                    if "engineer" in val_lower or "ingénieur" in val_lower or "engenheiro" in val_lower:
                        if "data" in val_lower or "donn" in val_lower:
                            return "Data Engineer"
                    if "analyst" in val_lower or "analyse" in val_lower or "analista" in val_lower:
                        if "donn" in val_lower or "data" in val_lower or "datos" in val_lower:
                            return "Data Analyst"
                    if "financ" in val_lower:
                        if "analyst" in val_lower or "analyse" in val_lower:
                            return "Financial Analyst"
                    if "assistant" in val_lower or "administrative" in val_lower or "admin" in val_lower:
                        return "Administrative Assistant"
                    if "secretaire" in val_lower or "secretary" in val_lower:
                        return "Secretary"
                    if "caissier" in val_lower or "cashier" in val_lower or "caisse" in val_lower:
                        return "Cashier"
                        
                    return "Other"

                # Process categories
                processed_df = df.copy()
                processed_df['Cleaned Category'] = processed_df[category_col].apply(normalize_category)
                processed_df = processed_df[processed_df['Cleaned Category'] != "Other"]

                # Job Position Filter Layout
                unique_jobs = sorted(processed_df['Cleaned Category'].unique().tolist())
                job_options = ["All Selected Positions"] + unique_jobs
                selected_job = st.sidebar.selectbox("Filter by Job Posting:", options=job_options)

                # --- APPLY FILTERS ---
                filtered_df = processed_df.copy()
                
                if selected_platform != "All Platforms" and platform_col:
                    filtered_df = filtered_df[filtered_df[platform_col].str.lower().str.contains(selected_platform.split()[0].lower(), na=False)]
                    
                if selected_job != "All Selected Positions":
                    filtered_df = filtered_df[filtered_df['Cleaned Category'] == selected_job]

                # --- MATHEMATICALLY ACCURATE SALARY ENGINE ---
                st.sidebar.markdown("---")
                st.sidebar.header("💰 Accurate Salary Insights")

                if 'Salary Amount' in filtered_df.columns:
                    
                    def render_precision_salaries(target_sub_df, reference_df):
                        valid_data = target_sub_df[(target_sub_df['Salary Amount'] > 0) & (target_sub_df[count_col] > 0)]
                        
                        if not valid_data.empty:
                            total_revenue_pool = (valid_data['Salary Amount'] * valid_data[count_col]).sum()
                            total_job_weight = valid_data[count_col].sum()
                            avg_mru_yearly = total_revenue_pool / total_job_weight
                            is_fallback = False
                        else:
                            backup_data = reference_df[(reference_df['Cleaned Category'] == selected_job) & (reference_df['Salary Amount'] > 0) & (reference_df[count_col] > 0)] if selected_job != "All Selected Positions" else pd.DataFrame()
                            
                            if backup_data.empty:
                                backup_data = reference_df[(reference_df['Salary Amount'] > 0) & (reference_df[count_col] > 0)]
                                
                            if not backup_data.empty:
                                avg_mru_yearly = (backup_data['Salary Amount'] * backup_data[count_col]).sum() / backup_data[count_col].sum()
                                total_job_weight = backup_data[count_col].sum()
                                is_fallback = True
                            else:
                                avg_mru_yearly = 0
                                total_job_weight = 0

                        if total_job_weight > 0 and avg_mru_yearly > 0:
                            # Extract Monthly split by dividing annual metrics by 12
                            avg_mru_monthly = avg_mru_yearly / 12.0
                            avg_usd_monthly = avg_mru_monthly / 40.0
                            
                            # Extract Hourly split based on standard calculation (2,080 billable hours per year)
                            avg_mru_hourly = avg_mru_yearly / 2080.0
                            avg_usd_hourly = avg_mru_hourly / 40.0
                            
                            monthly_title = "💵 EST. AVG MONTHLY SALARY" if is_fallback else "💵 AVG MONTHLY SALARY"
                            hourly_title = "⏳ EST. AVG HOURLY RATE" if is_fallback else "⏳ AVG HOURLY RATE"
                            border_color = "#F57C00" if is_fallback else "#2E7D32"

                            st.sidebar.markdown(f"""
                                <div style="margin-bottom: 15px; background-color: #1E1E1E; padding: 12px; border-radius: 6px; border-left: 5px solid {border_color};">
                                    <label style="font-size: 11px; color: #aaa; font-weight: bold; text-transform: uppercase;">{monthly_title}</label>
                                    <h1 style="font-size: 30px; margin: 4px 0; color: #4CAF50; font-weight: bold; line-height: 1;">${int(avg_usd_monthly):,} <span style="font-size:13px; color:#aaa;">USD</span></h1>
                                    <p style="font-size: 12px; color: #888; margin: 0;">↳ {int(avg_mru_monthly):,} MRU / month</p>
                                </div>
                                
                                <div style="margin-bottom: 15px; background-color: #1E1E1E; padding: 12px; border-radius: 6px; border-left: 5px solid {border_color};">
                                    <label style="font-size: 11px; color: #aaa; font-weight: bold; text-transform: uppercase;">{hourly_title}</label>
                                    <h1 style="font-size: 30px; margin: 4px 0; color: #2196F3; font-weight: bold; line-height: 1;">${round(avg_usd_hourly, 2):.2f} <span style="font-size:13px; color:#aaa;">USD</span></h1>
                                    <p style="font-size: 12px; color: #888; margin: 0;">↳ {round(avg_mru_hourly, 1):.1f} MRU / hour</p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.sidebar.markdown("""
                                <div style="margin-bottom: 15px; background-color: #1E1E1E; padding: 12px; border-radius: 6px; border-left: 5px solid #d32f2f;">
                                    <label style="font-size: 11px; color: #aaa; font-weight: bold; text-transform: uppercase;">💵 AVG MONTHLY SALARY</label>
                                    <h1 style="font-size: 30px; margin: 4px 0; color: #f44336; font-weight: bold; line-height: 1;">$0 <span style="font-size:14px; color:#aaa;">USD</span></h1>
                                    <p style="font-size: 12px; color: #888; margin: 0;">↳ 0 MRU</p>
                                </div>
                            """, unsafe_allow_html=True)

                    render_precision_salaries(filtered_df, processed_df)
                else:
                    st.sidebar.info("Salary headers not detected.")

                # --- MAIN DISPLAY TITLE ENGINE ---
                if selected_platform != "All Platforms":
                    chart_title = f"📊 Metrics for {selected_platform}"
                else:
                    chart_title = "✨ Aggregated Market Demand Matrix (Local & Global)"
                st.write(f"### {chart_title}")
                
                # --- NATIVE GRAPH GENERATION ---
                chart_data = filtered_df.groupby('Cleaned Category')[count_col].sum().sort_values(ascending=True)
                
                if not chart_data.empty:
                    st.bar_chart(chart_data, horizontal=True, use_container_width=True)
                else:
                    st.info("No records match your selected combination filters.")
                
                # --- HIGH-PRECISION KPI CARDS ---
                st.subheader("📊 Key Performance Indicators")
                st.markdown(f"""
                    <div style="display: flex; gap: 20px;">
                        <div style="flex: 1; background: #1E1E1E; padding: 15px; border-radius: 5px;">
                            <span style="color: #aaa; font-size: 14px;">Total Filtered Listings</span>
                            <h2 style="margin: 5px 0 0 0; color: #fff;">{int(filtered_df[count_col].sum()):,}</h2>
                        </div>
                        <div style="flex: 1; background: #1E1E1E; padding: 15px; border-radius: 5px;">
                            <span style="color: #aaa; font-size: 14px;">Active Targeted Profiles</span>
                            <h2 style="margin: 5px 0 0 0; color: #fff;">{len(filtered_df['Cleaned Category'].unique())}</h2>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    except Exception as error_msg:
        st.error(f"🚨 Python Error while processing: {str(error_msg)}")
        