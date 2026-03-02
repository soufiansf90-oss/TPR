import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import calendar
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# --- 1. SETTINGS & NEON UI ---
st.set_page_config(page_title="369 SHADOW V45", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');

.stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }

/* Welcome */
.welcome-text { font-family: 'Orbitron'; color: #00d4ff; font-size: 1.6rem; text-align: center; margin-bottom: 25px; text-shadow: 0 0 15px rgba(0,212,255,0.8); letter-spacing: 2px; }

/* Fade animation */
.content-fade { animation: slideUp 0.5s ease-out; }
@keyframes slideUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }

/* Sidebar Neon Buttons */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    background: rgba(255,255,255,0.03); border:1px solid rgba(0,212,255,0.2); padding:18px 22px !important;
    border-radius:12px; transition:0.3s all; width:100%; color:#8b949e; font-family:'Orbitron';
    text-transform:uppercase; font-size:0.9rem; text-align:center;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
    background: rgba(0,212,255,0.12) !important; border:1px solid #00d4ff !important; color:#00d4ff !important;
    box-shadow:0 0 20px rgba(0,212,255,0.4);
}

/* Journal */
.journal-win { border-left:5px solid #34d399 !important; background:rgba(52,211,153,0.05) !important; }
.journal-loss { border-left:5px solid #ef4444 !important; background:rgba(239,68,68,0.05) !important; }
.journal-be { border-left:5px solid #fbbf24 !important; background:rgba(251,191,36,0.05) !important; }

/* Performance */
.perf-card { background: rgba(22,27,34,0.6); border:1px solid rgba(0,212,255,0.1); padding:20px; border-radius:15px; text-align:center; transition:0.3s; }
.perf-card:hover { border-color:#00d4ff; box-shadow:0 0 15px rgba(0,212,255,0.2); }
.perf-val { font-size:1.8rem; font-weight:bold; font-family:'Orbitron'; color:#e6edf3; }
.perf-label { font-size:0.75rem; color:#00d4ff; text-transform:uppercase; letter-spacing:2px; margin-top:5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE ---
conn = sqlite3.connect('elite_v45.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT,
              outcome TEXT, pnl REAL, rr REAL, balance REAL, mindset TEXT, setup TEXT, image TEXT)''')
try: c.execute("ALTER TABLE trades ADD COLUMN image TEXT")
except: pass
conn.commit()

# --- 3. LOAD DATA ---
df = pd.read_sql_query("SELECT * FROM trades", conn)
current_balance, daily_net_pnl, initial_bal = 0.0, 0.0, 1000.0

if not df.empty:
    df['date_dt'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['date_dt','id'])
    initial_bal = df['balance'].iloc[0]
    df['cum_pnl'] = df['pnl'].cumsum()
    df['equity_curve'] = initial_bal + df['cum_pnl']
    current_balance = df['equity_curve'].iloc[-1]
    daily_net_pnl = df[df['date']==datetime.now().strftime('%Y-%m-%d')]['pnl'].sum()
    df['month_year'] = df['date_dt'].dt.to_period('M')

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="text-align:center; padding: 20px 0;"><span style="font-family:Orbitron; color:#00ffcc; font-size:1.5rem; text-shadow:0 0 10px #00ffcc66;">SHADOW SYSTEM</span></div>', unsafe_allow_html=True)
    st.divider()
    choice = st.radio("MENU", ["TERMINAL","CALENDAR","PERFORMANCE","ANALYZERS","JOURNAL"])
    st.divider()
    st.metric("EQUITY STATUS", f"${current_balance:,.2f}", f"{daily_net_pnl:+.2f} USD")
    st.divider()
    # Archive by year
    if not df.empty:
        years = sorted(df['date_dt'].dt.year.unique(), reverse=True)
        st.markdown("### ARCHIVE")
        archive_year = st.selectbox("Select Year", years, index=0)

# --- 5. WELCOME ---
st.markdown('<div class="welcome-text">WHAT\'S UP SHADOW, LET\'S SEE WHAT HAPPENED TODAY.</div>', unsafe_allow_html=True)

st.markdown('<div class="content-fade">', unsafe_allow_html=True)

# --- 6. MONTHLY P&L CHART (last 12 months) ---
if not df.empty:
    last_12_months = df['month_year'].drop_duplicates().sort_values(ascending=True)[-12:]
    df_12 = df[df['month_year'].isin(last_12_months)]
    monthly_pnl = df_12.groupby('month_year')['pnl'].sum().reset_index()
    monthly_pnl['equity_start'] = initial_bal + df_12.groupby('month_year')['cum_pnl'].min().values
    monthly_pnl['pct'] = (monthly_pnl['pnl']/monthly_pnl['equity_start'])*100
    fig_months = px.bar(monthly_pnl, x=monthly_pnl['month_year'].astype(str), y='pct',
                        color='pct', color_continuous_scale=['#ef4444','#34d399'],
                        text='pct', labels={'pct':'% P&L'}, title='Monthly P&L %', template='plotly_dark')
    fig_months.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    st.plotly_chart(fig_months, use_container_width=True)

# --- 7. MAIN CONTENT ---
# Filter df for selected archive year if applicable
if not df.empty and 'archive_year' in locals():
    df_year = df[df['date_dt'].dt.year==archive_year]
else:
    df_year = df.copy()

# --- TERMINAL ---
if choice=="TERMINAL":
    c1,c2 = st.columns([1,2.3])
    with c1:
        with st.form("entry_form"):
            st.markdown("### 📥 LOG ENTRY")
            d_in = st.date_input("Date", datetime.now())
            asset = st.text_input("Pair","NAS100").upper()
            res = st.selectbox("Outcome", ["WIN","LOSS","BE"])
            p_val = st.number_input("P&L ($)", value=0.0)
            r_val = st.number_input("RR Ratio", value=0.0)
            setup = st.text_input("Setup").upper()
            mind = st.selectbox("Mindset", ["Focused","Impulsive","Revenge","Bored"])
            img_file = st.file_uploader("Screenshot", type=['png','jpg','jpeg'])
            if st.form_submit_button("LOCK TRADE"):
                img_data = base64.b64encode(img_file.read()).decode() if img_file else None
                c.execute("INSERT INTO trades (date,pair,outcome,pnl,rr,balance,mindset,setup,image) VALUES (?,?,?,?,?,?,?,?,?)",
                          (str(d_in), asset, res, p_val, r_val, current_balance, mind, setup, img_data))
                conn.commit()
                st.rerun()
    with c2:
        if not df_year.empty:
            fig = go.Figure(go.Scatter(x=list(range(len(df_year))), y=df_year['equity_curve'],
                                       mode='lines+markers', line=dict(color='#00ffcc',width=3,shape='spline'),
                                       fill='tonexty', fillcolor='rgba(0,255,204,0.05)'))
            fig.update_layout(template="plotly_dark", height=480, title="ACCOUNT GROWTH CURVE", transition={'duration':500})
            st.plotly_chart(fig,use_container_width=True)

# --- CALENDAR ---
elif choice=="CALENDAR":
    if not df_year.empty:
        today=datetime.now()
        cal=calendar.monthcalendar(today.year,today.month)
        cols=st.columns(7)
        for i,d_name in enumerate(["MON","TUE","WED","THU","FRI","SAT","SUN"]):
            cols[i].markdown(f"<p style='text-align:center; color:#00d4ff; font-family:Orbitron; font-size:0.7rem;'>{d_name}</p>",unsafe_allow_html=True)
        for week in cal:
            cols=st.columns(7)
            for i,day in enumerate(week):
                if day==0: cols[i].markdown('<div class="cal-card" style="opacity:0.1"></div>',unsafe_allow_html=True)
                else:
                    d_str=datetime(today.year,today.month,day).strftime('%Y-%m-%d')
                    day_df=df_year[df_year['date']==d_str]
                    p_sum=day_df['pnl'].sum()
                    style="cal-win" if p_sum>0 else "cal-loss" if p_sum<0 else "cal-be" if len(day_df)>0 else ""
                    cols[i].markdown(f'<div class="cal-card {style}"><div style="font-size:0.7rem; color:#8b949e;">{day}</div><div style="font-weight:bold; font-size:0.9rem;">${p_sum:,.0f}</div></div>',unsafe_allow_html=True)

# --- PERFORMANCE ---
elif choice=="PERFORMANCE":
    if not df_year.empty:
        wins, losses = df_year[df_year['pnl']>0], df_year[df_year['pnl']<0]
        wr=(len(wins)/len(df_year))*100 if len(df_year)>0 else 0
        pf = wins['pnl'].sum()/abs(losses['pnl'].sum()) if not losses.empty else 0

        st.markdown("#### ⚡ PRIMARY METRICS")
        g1,g2,g3,g4 = st.columns(4)
        for col,label,val in zip([g1,g2,g3,g4],["Win Rate","Profit Factor","Avg RR","Net P&L"],
                                 [f"{wr:.1f}%", f"{pf:.2f}", f"{df_year['rr'].mean():.2f}", f"${df_year['pnl'].sum():,.0f}"]):
            col.markdown(f'<div class="perf-card"><div class="perf-val">{val}</div><div class="perf-label">{label}</div></div>',unsafe_allow_html=True)

# --- ANALYZERS ---
elif choice=="ANALYZERS":
    if not df_year.empty:
        fig_rr=go.Figure(data=[go.Scatter(x=list(range(len(df_year))),y=df_year['rr'],
                                          mode='lines+markers',line=dict(color='#fbbf24',width=2))])
        fig_rr.update_layout(template="plotly_dark", title="RR CONSISTENCY", transition={'duration':500})
        st.plotly_chart(fig_rr,use_container_width=True)
        st.plotly_chart(px.bar(df_year.groupby('mindset')['pnl'].sum().reset_index(),
                               x='mindset',y='pnl',title="PSYCHOLOGY IMPACT",template='plotly_dark'),use_container_width=True)

# --- JOURNAL ---
elif choice=="JOURNAL":
    if not df_year.empty:
        st.markdown("### 📜 TRADE ARCHIVE")
        for idx,row in df_year.sort_values('id',ascending=False).iterrows():
            j_class="journal-win" if row['pnl']>0 else "journal-loss" if row['pnl']<0 else "journal-be"
            with st.container():
                st.markdown(f'<div class="{j_class}" style="padding:10px; border-radius:0 10px 10px 0; margin-bottom:10px;">',unsafe_allow_html=True)
                with st.expander(f"● {row['date']} | {row['pair']} | P&L: ${row['pnl']:,.2f} | Setup: {row['setup']}"):
                    tx,im = st.columns([1,2])
                    with tx:
                        st.write(f"**Outcome:** {row['outcome']}")
                        st.write(f"**RR:** {row['rr']} | **Mindset:** {row['mindset']}")
                    with im:
                        if row['image']: st.image(base64.b64decode(row['image']),use_container_width=True)
                st.markdown('</div>',unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
