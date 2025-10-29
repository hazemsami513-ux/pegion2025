
import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="Pigeon Breeding App", layout="wide")
st.markdown("<h1 style='text-align:center;'>Pigeon Pair Compatibility</h1>", unsafe_allow_html=True)

st.sidebar.header("Data / Upload")
uploaded = st.sidebar.file_uploader("Upload CSV or Excel (headers: ID,Name,Gender,Color,Weight,Head,Feather,Power,Health,Image_Path)", type=['csv','xlsx','xls'])
use_sample = st.sidebar.checkbox("Use included sample data", value=True)

sample_file = "data.csv"

def load_data(uploaded, use_sample):
    if uploaded is not None:
        fn = uploaded.name.lower()
        if fn.endswith('.csv'):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
    else:
        if use_sample and os.path.exists(sample_file):
            df = pd.read_csv(sample_file)
        else:
            st.error("Please upload data or enable sample data.")
            return None
    df.columns = [c.strip() for c in df.columns]
    req = ['ID','Name','Gender','Color','Weight','Head','Feather','Power','Health','Image_Path']
    missing = [c for c in req if c not in df.columns]
    if missing:
        st.error(f"Missing columns: {missing}")
        return None
    df['Gender'] = df['Gender'].astype(str).str.lower()
    df['gender_norm'] = df['Gender'].apply(lambda x: 'male' if 'm' in x else ('female' if 'f' in x else x))
    return df

df = load_data(uploaded, use_sample)
if df is None:
    st.stop()

color_map = {'white':10,'gray':8,'black':6,'brown':7}
head_map = {'long':10,'medium':7,'short':5}
feather_map = {'smooth':10,'medium':7,'rough':4}

st.sidebar.header("Targets & Weights")
target_weight = st.sidebar.number_input("Target weight (grams)", value=400)
w_color = st.sidebar.number_input('Weight: Color', 0.0, 1.0, 0.3)
w_weight = st.sidebar.number_input('Weight: Weight', 0.0, 1.0, 0.2)
w_head = st.sidebar.number_input('Weight: Head', 0.0, 1.0, 0.1)
w_feather = st.sidebar.number_input('Weight: Feather', 0.0, 1.0, 0.1)
w_power = st.sidebar.number_input('Weight: Power', 0.0, 1.0, 0.2)
w_health = st.sidebar.number_input('Weight: Health', 0.0, 1.0, 0.1)

def mval(text, mapping, default=7):
    try:
        return mapping.get(str(text).strip().lower(), default)
    except:
        return default

df['color_v'] = df['Color'].apply(lambda x: mval(x, color_map))
df['head_v'] = df['Head'].apply(lambda x: mval(x, head_map))
df['feather_v'] = df['Feather'].apply(lambda x: mval(x, feather_map))

males = df[df['gender_norm']=='male']
females = df[df['gender_norm']=='female']

if males.empty or females.empty:
    st.error("Need at least one male and one female in data.")
    st.stop()

st.subheader("Select pair to compare")
c1, c2 = st.columns(2)
with c1:
    male_id = st.selectbox("Select Male", options=males['ID'].tolist())
with c2:
    female_id = st.selectbox("Select Female", options=females['ID'].tolist())

male = males[males['ID']==male_id].iloc[0]
female = females[females['ID']==female_id].iloc[0]

diff_color = abs(male['color_v'] - female['color_v'])
diff_head = abs(male['head_v'] - female['head_v'])
diff_feather = abs(male['feather_v'] - female['feather_v'])
diff_weight = abs(float(male['Weight']) - float(female['Weight'])) / max(1, float(target_weight)) * 10
diff_power = abs(float(male['Power']) - float(female['Power']))
diff_health = abs(float(male['Health']) - float(female['Health']))

weighted_sum = (diff_color * w_color + diff_head * w_head + diff_feather * w_feather +
                diff_weight * w_weight + diff_power * w_power + diff_health * w_health)
compatibility = max(0, round(100 - weighted_sum*1,2))

colA, colB, colC = st.columns([1,2,1])
with colA:
    if os.path.exists(male['Image_Path']):
        st.image(male['Image_Path'], caption=f"{male['Name']} — {male['ID']}", use_column_width=True)
    else:
        st.write(f"{male['Name']} — {male['ID']}")
with colB:
    st.markdown(f"### Compatibility: **{compatibility} / 100**")
    bar_color = "#f03b20" if compatibility < 50 else ("#ffae42" if compatibility < 80 else "#2ca02c")
    st.markdown(f"""<div style='width:100%;background:#eee;border-radius:6px'><div style='width:{compatibility}%;background:{bar_color};height:18px;border-radius:6px'></div></div>""", unsafe_allow_html=True)
    comp_df = pd.DataFrame([
        ['Color', male['Color'], female['Color'], male['color_v'], female['color_v'], diff_color],
        ['Weight', male['Weight'], female['Weight'], '', '', round(diff_weight,2)],
        ['Head', male['Head'], female['Head'], male['head_v'], female['head_v'], diff_head],
        ['Feather', male['Feather'], female['Feather'], male['feather_v'], female['feather_v'], diff_feather],
        ['Power', male['Power'], female['Power'], '', '', diff_power],
        ['Health', male['Health'], female['Health'], '', '', diff_health],
    ], columns=['Trait','Male','Female','Male (v)','Female (v)','Difference'])
    st.table(comp_df)
with colC:
    if os.path.exists(female['Image_Path']):
        st.image(female['Image_Path'], caption=f"{female['Name']} — {female['ID']}", use_column_width=True)
    else:
        st.write(f"{female['Name']} — {female['ID']}")

st.write('Weighted sum used:', round(weighted_sum,3))
