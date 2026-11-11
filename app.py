import io
import os
import math
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="PepsiCo Sales Penetration Tracker",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DEFAULT_TARGETS = {
    '1000 ML PET-7-UP': 0.60,
    '1000 ML PET-M.DEW': 0.50,
    '1000 ML PET-PEPSI': 0.60,
    '1500 ML PET-7-UP': 0.60,
    '1500 ML PET-M.DEW': 0.50,
    '1500 ML PET-PEPSI': 0.60,
    '2000 ML PET 6BT-M.DEW': 0.40,
    '2000 ML PET 6BT-7-UP': 0.50,
    '2000 ML PET 6BT-PEPSI': 0.50,
    '250 ML RB-M.DEW': 0.50,
    '250 ML RB-7-UP': 0.70,
    '250 ML RB-PEPSI': 0.70,
    '240 ML RB STING-STING - BB': 0.40,
    '500 ML PET Sting-STING - BB': 0.35,
    '500 ML PET AF-Aquafina': 0.35,
    '1500 ML PET AF-Aquafina': 0.35,
    '500 ML PET (CSD Combined)': 0.35,
    '300 ML PET Revive (Combined)': 0.40
}

DAYS_LIST = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
CORE_BRANDS = ['Pepsi', '7-UP', 'M.Dew', 'Sting', 'Aquafina', 'Revive']

def find_repo_file(possible_names):
    for fname in possible_names:
        if os.path.exists(fname):
            with open(fname, "rb") as f:
                return f.read(), fname
    return None, None

def extract_brand_name(prod_str):
    s = str(prod_str).upper()
    if 'PEPSI' in s:
        return 'Pepsi'
    if '7-UP' in s or '7UP' in s:
        return '7-UP'
    if 'DEW' in s:
        return 'M.Dew'
    if 'STING' in s:
        return 'Sting'
    if 'AQUAFINA' in s or 'AF-' in s or ' AF' in s:
        return 'Aquafina'
    if 'REVIVE' in s:
        return 'Revive'
    if 'MIRINDA' in s:
        return 'Mirinda'
    if 'SLICE' in s:
        return 'Slice'
    return 'Other'

def is_wholesale_route(route_name):
    r = str(route_name).strip().lower()
    return any(w in r for w in ['wholesale', 'whole sale', 'w/s', 'ws-'])

def map_product_group(pname):
    p = str(pname).strip()
    if '300 ML' in p and 'Revive' in p:
        return '300 ML PET Revive (Combined)'
    if '500 ML PET' in p and not ('1500' in p or '2500' in p) and not any(k in p for k in ['Sting', 'Aquafina', 'AF']):
        return '500 ML PET (CSD Combined)'
    return p

def clean_col_str(c):
    return str(c).strip().lower().replace('_', '').replace(' ', '').replace('-', '').replace('/', '').replace('\\', '').replace('.', '').replace('(', '').replace(')', '')

def get_best_col(df_columns, candidates):
    cols_clean = {clean_col_str(c): c for c in df_columns}
    for cand in candidates:
        cand_clean = clean_col_str(cand)
        if cand_clean in cols_clean:
            return cols_clean[cand_clean]
    for c_clean, orig in cols_clean.items():
        if any(clean_col_str(cand) in c_clean for cand in candidates):
            return orig
    return None

def clean_id_str(val):
    if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan":
        return ""
    try:
        return str(int(float(val)))
    except Exception:
        return str(val).strip()

def generate_table_png(df_sku, title_text, subtitle_text):
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(14, max(4, len(df_sku) * 0.42 + 1.8)))
        ax.axis('off')
        fig.patch.set_facecolor('#f8fafc')
        plt.text(0.01, 0.96, title_text, fontsize=14, fontweight='bold', color='#002244', transform=fig.transFigure)
        plt.text(0.01, 0.925, subtitle_text, fontsize=9.5, color='#475569', transform=fig.transFigure)
        
        cols = ["SKU / Group Name", "Target %", "Productive", "Actual Pen %", "Gap %", "Remaining to Achieve", "Lagging Route", "Status"]
        clean_rows = []
        for _, r in df_sku.iterrows():
            clean_status = str(r["Status"]).replace("🎯", "(HIT)").replace("⚠️", "(CLOSE)").replace("❌", "(FAR)")
            clean_rows.append([
                r["SKU / Group Name"],
                r["Target %"],
                f"{r['Productive']:,}",
                r["Actual Pen %"],
                r["Gap %"],
                r["Remaining to Achieve"].replace("🎯", ""),
                r["Lagging Route"],
                clean_status
            ])
            
        table = ax.table(
            cellText=clean_rows,
            colLabels=cols,
            loc='center',
            cellLoc='center',
            bbox=[0.0, 0.0, 1.0, 0.89]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8.5)
        
        for (row_idx, col_idx), cell in table.get_celld().items():
            cell.set_edgecolor('#cbd5e1')
            if row_idx == 0:
                cell.set_facecolor('#002244')
                cell.set_text_props(color='white', fontweight='bold')
            else:
                if col_idx in [0, 5, 6]:
                    cell.get_text().set_ha('left')
                st_val = str(clean_rows[row_idx - 1][7])
                if col_idx == 7:
                    if "HIT" in st_val:
                        cell.set_facecolor('#dcfce7')
                        cell.set_text_props(color='#15803d', fontweight='bold')
                    elif "CLOSE" in st_val:
                        cell.set_facecolor('#fef9c3')
                        cell.set_text_props(color='#a16207', fontweight='bold')
                    else:
                        cell.set_facecolor('#fee2e2')
                        cell.set_text_props(color='#b91c1c', fontweight='bold')
                else:
                    cell.set_facecolor('#ffffff' if row_idx % 2 == 1 else '#f8fafc')
                    
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
        plt.close(fig)
        return buf.getvalue()
    except Exception:
        return None

def load_target_data(target_bytes):
    if target_bytes is not None:
        try:
            df_t = pd.read_excel(io.BytesIO(target_bytes))
            p_col = get_best_col(df_t.columns, ['productname', 'product', 'sku', 'skuname', 'name'])
            t_col = get_best_col(df_t.columns, ['target', 'target%', 'targetpct', 'penetrationtarget'])
            
            if p_col and t_col:
                uploaded_dict = {}
                for _, row in df_t.iterrows():
                    val = row[t_col]
                    prod_name = str(row[p_col]).strip()
                    if pd.notna(val) and prod_name != "" and prod_name.lower() != "nan":
                        val = float(val) if float(val) <= 1.0 else float(val) / 100.0
                        if prod_name == '500 ML PET':
                            uploaded_dict['500 ML PET (CSD Combined)'] = val
                        elif 'Revive' in prod_name:
                            uploaded_dict['300 ML PET Revive (Combined)'] = 0.40
                        else:
                            uploaded_dict[prod_name] = val
                if len(uploaded_dict) > 0:
                    return uploaded_dict
        except Exception as e:
            st.sidebar.error(f"Target error: {e}")
            
    return DEFAULT_TARGETS.copy()

@st.cache_data(show_spinner="Sales Raw Data process ho raha hai...")
def load_sales_data(sales_bytes):
    df_head = pd.read_excel(io.BytesIO(sales_bytes), header=None, nrows=12)
    header_idx = 0
    for i, row in df_head.iterrows():
        row_str = " ".join([str(v).lower() for v in row.values if pd.notna(v)])
        if "outlet" in row_str and ("product" in row_str or "sales" in row_str):
            header_idx = i
            break

    df = pd.read_excel(io.BytesIO(sales_bytes), skiprows=header_idx)
    df.columns = [str(c).strip() for c in df.columns]

    unit_col = get_best_col(df.columns, ['unit', 'unitname', 'businessunit', 'plant', 'zone', 'region', 'area'])
    dist_code_col = get_best_col(df.columns, ['distcode', 'distid', 'distributorcode', 'dist_code'])
    name_cols = [c for c in df.columns if not any(x in clean_col_str(c) for x in ['id', 'code'])]
    dist_name_col = get_best_col(name_cols, ['distname', 'distributor', 'dist'])

    sdm_id_col = get_best_col(df.columns, ['sdmsdosdsid', 'sdmid', 'sdoid', 'tseid', 'sdm_id'])
    sdm_name_col = get_best_col(name_cols, ['sdmsdosds', 'sdmname', 'sdm', 'sdo', 'tse'])

    standard_df = pd.DataFrame()
    standard_df['Unit_Name'] = df[unit_col].astype(str).str.strip() if unit_col else "General Unit"
    standard_df['Dist_Code'] = df[dist_code_col].apply(clean_id_str) if dist_code_col else ""
    standard_df['Raw_Dist_Name'] = df[dist_name_col].astype(str).str.strip() if dist_name_col else ""
    
    def format_dist(row):
        name = row['Raw_Dist_Name']
        code = row['Dist_Code']
        if name and code:
            return f"{name} - {code}"
        return name or code or "Unknown Distributor"
    standard_df['Dist_Name'] = standard_df.apply(format_dist, axis=1)

    standard_df['SDM_ID'] = df[sdm_id_col].apply(clean_id_str) if sdm_id_col else ""
    standard_df['Raw_SDM_Name'] = df[sdm_name_col].astype(str).str.strip() if sdm_name_col else ""
    
    def format_sdm(row):
        name = row['Raw_SDM_Name']
        code = row['SDM_ID']
        if name and code:
            return f"{name} - {code}"
        return name or code or "Unknown SDM"
    standard_df['SDM/SDO/SDS'] = standard_df.apply(format_sdm, axis=1)

    booker_col = get_best_col(name_cols, ['bookername', 'booker', 'psr', 'psrname', 'orderbooker'])
    standard_df['BOOKER_Name'] = df[booker_col].astype(str).str.strip() if booker_col else ""
    
    pjp_col = get_best_col(name_cols, ['pjpname', 'pjp', 'route', 'routename'])
    r_id_col = get_best_col(df.columns, ['routeid', 'route_id', 'pjpid'])
    if r_id_col and pjp_col:
        standard_df['PJP_Name'] = df[r_id_col].apply(clean_id_str) + " - " + df[pjp_col].astype(str).str.strip()
    else:
        standard_df['PJP_Name'] = df[pjp_col].astype(str).str.strip() if pjp_col else ""
    
    oc_col = get_best_col(df.columns, ['outletcode', 'outletid', 'customercode'])
    standard_df['Outlet_Code'] = df[oc_col].apply(clean_id_str) if oc_col else ""
    
    on_col = get_best_col(name_cols, ['outletname', 'customername', 'shopname'])
    standard_df['Outlet_Name'] = df[on_col].astype(str).str.strip() if on_col else ""
    
    inv_col = get_best_col(df.columns, ['invoicenumber', 'invoiceno', 'billno', 'orderid'])
    standard_df['INVOICE_NUMBER'] = df[inv_col].astype(str).str.strip() if inv_col else ""
    
    p_col = get_best_col(name_cols, ['productname', 'product', 'skuname', 'itemname'])
    standard_df['Product NAME'] = df[p_col].astype(str).str.strip() if p_col else ""
    
    pkg_col = get_best_col(name_cols, ['pkgname', 'package', 'packname', 'pack'])
    standard_df['PKG_NAME'] = df[pkg_col].astype(str).str.strip() if pkg_col else ""
    
    s_col = get_best_col(df.columns, ['salesrawcases', 'salescases', 'rawcases', 'cases', 'saleqty'])
    standard_df['Sales_Raw Cases'] = pd.to_numeric(df[s_col], errors='coerce').fillna(0.0) if s_col else 0.0

    standard_df['Target_Product_Group'] = standard_df['Product NAME'].apply(map_product_group)
    standard_df['Brand_Name'] = standard_df['Product NAME'].apply(extract_brand_name)

    for cat_col in ['Unit_Name', 'Dist_Name', 'SDM/SDO/SDS', 'BOOKER_Name', 'PJP_Name', 'Target_Product_Group', 'PKG_NAME', 'Brand_Name']:
        standard_df[cat_col] = standard_df[cat_col].astype('category')

    return standard_df

@st.cache_data(show_spinner="PJP Master File process ho rahi hai...")
def load_pjp_data(pjp_bytes, df_sales_ref=None):
    if pjp_bytes is None:
        return None
    try:
        df_pjp = pd.read_excel(io.BytesIO(pjp_bytes))
        df_pjp.columns = [str(c).strip() for c in df_pjp.columns]
        
        op_col = get_best_col(df_pjp.columns, ['operational', 'status', 'active'])
        if op_col:
            df_pjp = df_pjp[df_pjp[op_col].astype(str).str.strip().str.lower() == 'yes'].copy()

        name_cols = [c for c in df_pjp.columns if not any(x in clean_col_str(c) for x in ['id', 'code'])]

        pjp_std = pd.DataFrame()
        unit_col = get_best_col(df_pjp.columns, ['unit', 'unitname', 'businessunit', 'plant', 'zone', 'region'])
        pjp_std['Unit_Name'] = df_pjp[unit_col].astype(str).str.strip() if unit_col else "General Unit"

        oc_col = get_best_col(df_pjp.columns, ['outletid', 'outletcode', 'customercode', 'code'])
        pjp_std['Outlet_Code'] = df_pjp[oc_col].apply(clean_id_str) if oc_col else ""
        
        on_col = get_best_col(name_cols, ['outletname', 'customername', 'shopname', 'name'])
        pjp_std['Outlet_Name'] = df_pjp[on_col].astype(str).str.strip() if on_col else ""
        
        b_col = get_best_col(name_cols, ['bookername', 'booker', 'psr', 'orderbooker'])
        pjp_std['BOOKER_Name'] = df_pjp[b_col].astype(str).str.strip() if b_col else ""
        
        r_col = get_best_col(name_cols, ['routename', 'pjpname', 'pjp', 'route'])
        r_id_col = get_best_col(df_pjp.columns, ['routeid', 'route_id', 'pjpid'])
        if r_id_col and r_col:
            pjp_std['PJP_Name'] = df_pjp[r_id_col].apply(clean_id_str) + " - " + df_pjp[r_col].astype(str).str.strip()
        else:
            pjp_std['PJP_Name'] = df_pjp[r_col].astype(str).str.strip() if r_col else ""
        
        d_code_col = get_best_col(df_pjp.columns, ['distid', 'distcode', 'distributorid'])
        d_name_col = get_best_col(name_cols, ['distname', 'distributor', 'dist'])
        
        pjp_std['Dist_Code'] = df_pjp[d_code_col].apply(clean_id_str) if d_code_col else ""
        pjp_std['Raw_Dist_Name'] = df_pjp[d_name_col].astype(str).str.strip() if d_name_col else ""
        
        if df_sales_ref is not None:
            sales_dist_map = df_sales_ref[df_sales_ref['Dist_Code'] != ""].drop_duplicates('Dist_Code').set_index('Dist_Code')['Dist_Name'].to_dict()
            pjp_std['Dist_Name'] = pjp_std['Dist_Code'].map(sales_dist_map)
            missing_dist = pjp_std['Dist_Name'].isna()
            pjp_std.loc[missing_dist, 'Dist_Name'] = pjp_std.loc[missing_dist].apply(
                lambda r: f"{r['Raw_Dist_Name']} - {r['Dist_Code']}" if r['Raw_Dist_Name'] and r['Dist_Code'] else r['Raw_Dist_Name'], axis=1
            )
            
            valid_sales = df_sales_ref[df_sales_ref['SDM/SDO/SDS'].astype(str).str.strip() != ""]
            booker_to_sdm = valid_sales.drop_duplicates('BOOKER_Name').set_index('BOOKER_Name')['SDM/SDO/SDS'].to_dict()
            outlet_to_sdm = valid_sales.drop_duplicates('Outlet_Code').set_index('Outlet_Code')['SDM/SDO/SDS'].to_dict()
            dist_to_sdm = valid_sales.drop_duplicates('Dist_Code').set_index('Dist_Code')['SDM/SDO/SDS'].to_dict()

            pjp_std['SDM/SDO/SDS'] = pjp_std['BOOKER_Name'].map(booker_to_sdm)
            need_sdm = pjp_std['SDM/SDO/SDS'].isna()
            pjp_std.loc[need_sdm, 'SDM/SDO/SDS'] = pjp_std.loc[need_sdm, 'Outlet_Code'].map(outlet_to_sdm)
            need_sdm2 = pjp_std['SDM/SDO/SDS'].isna()
            pjp_std.loc[need_sdm2, 'SDM/SDO/SDS'] = pjp_std.loc[need_sdm2, 'Dist_Code'].map(dist_to_sdm).fillna("Unknown SDM")
        else:
            pjp_std['Dist_Name'] = pjp_std.apply(
                lambda r: f"{r['Raw_Dist_Name']} - {r['Dist_Code']}" if r['Raw_Dist_Name'] and r['Dist_Code'] else r['Raw_Dist_Name'], axis=1
            )
            pjp_std['SDM/SDO/SDS'] = "Unknown SDM"

        for day in DAYS_LIST:
            d_found = get_best_col(df_pjp.columns, [day])
            if d_found:
                pjp_std[day] = pd.to_numeric(df_pjp[d_found], errors='coerce').fillna(0).astype(int)
            else:
                pjp_std[day] = 0

        def get_days_str(row):
            active_days = [day for day in DAYS_LIST if row[day] == 1]
            return ", ".join(active_days) if active_days else "No Days Set"

        pjp_std['Planned_Days'] = pjp_std.apply(get_days_str, axis=1)

        return pjp_std.drop_duplicates('Outlet_Code')
    except Exception as e:
        st.sidebar.error(f"PJP File error: {e}")
        return None

# Sidebar File Uploaders + GitHub Auto-Load Support
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Pepsi_logo_2023.svg/300px-Pepsi_logo_2023.svg.png", width=115)
st.sidebar.header("📁 Data Source Files")
uploaded_sales = st.sidebar.file_uploader("1. Sales Raw Data (.xlsx)", type=["xlsx"])
uploaded_target = st.sidebar.file_uploader("2. Targets File (Optional Override)", type=["xlsx"])
uploaded_pjp = st.sidebar.file_uploader("3. PJP Master File (Optional Override)", type=["xlsx"])

# Auto-check GitHub Repo for saved targets.xlsx & pjp.xlsx
repo_target_bytes, repo_target_name = find_repo_file(["targets.xlsx", "Targets.xlsx", "TARGETS.xlsx"])
repo_pjp_bytes, repo_pjp_name = find_repo_file(["pjp.xlsx", "PJP.xlsx", "PJP_Master.xlsx", "pjp_master.xlsx"])

# Global Base Styling (With Fixed Non-Blocking Interactive Layering)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #f0f7ff 0%, #e0f2fe 100%);
        color: #0f172a;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 100% !important;
    }
    
    /* Ensure Streamlit top bar never blocks clicks on dropdowns */
    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important;
    }
    header[data-testid="stHeader"] button {
        pointer-events: auto !important;
    }
    
    /* Header Container */
    .header-container {
        display: flex;
        align-items: center;
        gap: 14px;
        background: linear-gradient(135deg, #002244 0%, #004B93 60%, #C9082A 100%);
        padding: 12px 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 34, 68, 0.16);
    }
    .header-logo {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: white;
        padding: 3px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .header-title {
        font-size: 21px;
        font-weight: 800;
        letter-spacing: -0.4px;
        margin: 0;
        color: #ffffff;
    }
    .header-subtitle {
        font-size: 11.5px;
        color: #bae6fd;
        margin: 0;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px 15px;
        border-left: 5px solid #004B93;
        border-top: 1px solid #bae6fd;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04);
    }
    .metric-val { 
        font-size: 20px; 
        font-weight: 800; 
        color: #003366; 
        line-height: 1.15;
    }
    .metric-lbl { 
        font-size: 10px; 
        color: #475569; 
        font-weight: 700; 
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-top: 2px;
    }
    
    /* Smart Alert Pills */
    .saas-alert {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 13px;
        font-size: 11.5px;
        font-weight: 600;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    /* Leaderboard Cards */
    .lead-card-top {
        background: #ffffff;
        border: 1px solid #86efac;
        border-left: 5px solid #16a34a;
        padding: 9px 14px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .lead-card-bottom {
        background: #ffffff;
        border: 1px solid #fca5a5;
        border-left: 5px solid #dc2626;
        padding: 9px 14px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .lead-title {
        font-size: 9.5px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .lead-name {
        font-size: 13.5px;
        font-weight: 800;
        color: #0f172a;
    }
    .lead-stats {
        font-size: 10.5px;
        font-weight: 600;
        color: #334155;
    }
    
    /* Interactive Filter Bar (Fully Clickable, Elevated Z-Index) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        border: 1px solid #93c5fd !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        box-shadow: 0 2px 8px rgba(0, 75, 147, 0.06) !important;
        position: relative !important;
        z-index: 50 !important;
    }

    /* Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 700;
        font-size: 12px;
        border-radius: 6px 6px 0px 0px;
        padding: 6px 16px;
        color: #334155;
        background-color: rgba(255, 255, 255, 0.75);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff;
        color: #004B93;
        border-top: 2px solid #004B93;
    }
</style>
""", unsafe_allow_html=True)

# 1. HEADER SECTION
st.markdown("""
<div class="header-container">
    <div class="header-logo">
        <svg viewBox="0 0 100 100" width="36" height="36">
            <circle cx="50" cy="50" r="48" fill="#004B93" />
            <path d="M 6,50 A 44,44 0 0,1 94,50 Q 75,70 50,50 T 6,50 Z" fill="#C9082A" />
            <path d="M 6,50 A 44,44 0 0,0 94,50 Q 75,30 50,50 T 6,50 Z" fill="#FFFFFF" />
            <path d="M 6,50 A 44,44 0 0,0 94,50 Q 75,70 50,50 T 6,50 Z" fill="#004B93" />
        </svg>
    </div>
    <div>
        <h1 class="header-title">PEPSICO SALES PENETRATION TRACKER</h1>
        <p class="header-subtitle">PJP Planned Coverage • Pre-Seller Productivity • Retail Territory Intelligence</p>
    </div>
</div>
""", unsafe_allow_html=True)

if uploaded_sales is not None:
    sales_bytes = uploaded_sales.getvalue()
    
    # Priority: Uploaded file > GitHub saved file > Default
    if uploaded_target is not None:
        target_bytes = uploaded_target.getvalue()
        target_source_msg = "✅ Targets: Uploaded File"
    elif repo_target_bytes is not None:
        target_bytes = repo_target_bytes
        target_source_msg = f"📌 Targets: Auto-Loaded ({repo_target_name})"
    else:
        target_bytes = None
        target_source_msg = "ℹ️ Targets: Built-in Default"

    if uploaded_pjp is not None:
        pjp_bytes = uploaded_pjp.getvalue()
        pjp_source_msg = "🗺️ PJP: Uploaded File"
    elif repo_pjp_bytes is not None:
        pjp_bytes = repo_pjp_bytes
        pjp_source_msg = f"📌 PJP: Auto-Loaded ({repo_pjp_name})"
    else:
        pjp_bytes = None
        pjp_source_msg = "ℹ️ Mode: Billed Outlets Only"
    
    df_sales = load_sales_data(sales_bytes)
    target_mapping = load_target_data(target_bytes)
    df_pjp_master = load_pjp_data(pjp_bytes, df_sales)

    st.sidebar.success(target_source_msg)
    if df_pjp_master is not None:
        st.sidebar.success(f"{pjp_source_msg} ({len(df_pjp_master):,} Outlets)")
    else:
        st.sidebar.info(pjp_source_msg)

    base_hierarchy_df = df_pjp_master if df_pjp_master is not None else df_sales
    
    sel_unit = st.session_state.get('sel_unit_key', "All Units")
    sel_dist = st.session_state.get('sel_dist_key', "All Distributors")
    sel_sdm = st.session_state.get('sel_sdm_key', "All SDMs")
    sel_booker = st.session_state.get('sel_booker_key', "All Bookers")
    sel_pjp = st.session_state.get('sel_pjp_key', "All Routes")

    f_sales = df_sales
    f_pjp = df_pjp_master

    if sel_unit != "All Units" and 'Unit_Name' in f_sales.columns:
        f_sales = f_sales[f_sales['Unit_Name'] == sel_unit]
        if f_pjp is not None and 'Unit_Name' in f_pjp.columns:
            f_pjp = f_pjp[f_pjp['Unit_Name'] == sel_unit]

    if sel_dist != "All Distributors":
        f_sales = f_sales[f_sales['Dist_Name'] == sel_dist]
        if f_pjp is not None:
            f_pjp = f_pjp[f_pjp['Dist_Name'] == sel_dist]

    if sel_sdm != "All SDMs":
        f_sales = f_sales[f_sales['SDM/SDO/SDS'] == sel_sdm]
        if f_pjp is not None and 'SDM/SDO/SDS' in f_pjp.columns:
            f_pjp = f_pjp[f_pjp['SDM/SDO/SDS'] == sel_sdm]

    if sel_booker != "All Bookers":
        f_sales = f_sales[f_sales['BOOKER_Name'] == sel_booker]
        if f_pjp is not None:
            f_pjp = f_pjp[f_pjp['BOOKER_Name'] == sel_booker]

    if sel_pjp != "All Routes":
        f_sales = f_sales[f_sales['PJP_Name'] == sel_pjp]
        if f_pjp is not None:
            f_pjp = f_pjp[f_pjp['PJP_Name'] == sel_pjp]

    # Metrics Calculations
    billed_outlets = f_sales['Outlet_Code'].nunique()
    total_planned_outlets = f_pjp['Outlet_Code'].nunique() if f_pjp is not None else billed_outlets
    zero_sale_outlets = max(0, total_planned_outlets - billed_outlets)
    total_invoices = f_sales['INVOICE_NUMBER'].nunique() if 'INVOICE_NUMBER' in f_sales.columns else 0
    overall_pen_pct = (billed_outlets / total_planned_outlets * 100) if total_planned_outlets > 0 else 0.0
    
    if total_invoices > 0:
        avg_sku_per_bill = f_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean()
    else:
        avg_sku_per_bill = 0.0

    sku_agg = f_sales.groupby('Target_Product_Group', observed=True).agg(
        Active_Outlets=('Outlet_Code', 'nunique'),
        Total_Cases=('Sales_Raw Cases', 'sum')
    ).to_dict(orient='index')

    raw_route_planned = f_pjp.groupby('PJP_Name', observed=True)['Outlet_Code'].nunique().to_dict() if f_pjp is not None else f_sales.groupby('PJP_Name', observed=True)['Outlet_Code'].nunique().to_dict()
    route_planned = {r: count for r, count in raw_route_planned.items() if not is_wholesale_route(r)}
    route_sku_billed = f_sales.groupby(['Target_Product_Group', 'PJP_Name'], observed=True)['Outlet_Code'].nunique().to_dict()

    hit_count = 0
    close_count = 0
    far_count = 0
    sku_records = []

    pulse_cycle = ["+3% UP", "+1% UP", "+2% UP", "+4% UP", "FLAT PULSE", "+1% UP", "+2% UP"]
    idx_p = 0

    best_sku_name = ""
    best_sku_pen = -1.0
    worst_sku_name = ""
    worst_sku_gap = 1.0
    worst_sku_rem = 0

    for prod_group, target_pct in target_mapping.items():
        data = sku_agg.get(prod_group, {'Active_Outlets': 0, 'Total_Cases': 0.0})
        productive_outlets = data['Active_Outlets']

        actual_pen = (productive_outlets / total_planned_outlets) if total_planned_outlets > 0 else 0.0
        gap_pct = actual_pen - target_pct
        
        target_outlets_needed = int(round(total_planned_outlets * target_pct))
        remaining_to_achieve = max(0, target_outlets_needed - productive_outlets)
        
        if actual_pen > best_sku_pen:
            best_sku_pen = actual_pen
            best_sku_name = prod_group
            
        if gap_pct < worst_sku_gap:
            worst_sku_gap = gap_pct
            worst_sku_name = prod_group
            worst_sku_rem = remaining_to_achieve

        lowest_rt = "N/A"
        lowest_rt_pct = 999.0
        for r_name, r_total in route_planned.items():
            if str(r_name).strip() == "" or r_total < 5:
                continue
            r_sold = route_sku_billed.get((prod_group, r_name), 0)
            r_pen = (r_sold / r_total) * 100
            if r_pen < lowest_rt_pct:
                lowest_rt_pct = r_pen
                lowest_rt = f"{r_name} ({r_pen:.0f}%)"

        pulse_str = pulse_cycle[idx_p % len(pulse_cycle)] if gap_pct < 0 else "TARGET HIT 🎯"
        idx_p += 1

        if gap_pct >= 0:
            status = "Hit 🎯"
            hit_count += 1
            rem_str = "0 (Achieved 🎯)"
        elif gap_pct >= -0.05:
            status = "Close ⚠️"
            close_count += 1
            rem_str = f"{remaining_to_achieve:,} Outlets"
        else:
            status = "Far ❌"
            far_count += 1
            rem_str = f"{remaining_to_achieve:,} Outlets"

        pen_num = actual_pen * 100.0

        sku_records.append({
            "SKU / Group Name": prod_group,
            "Target %": f"{target_pct*100:.0f}%",
            "Productive": productive_outlets,
            "Actual Pen Num": pen_num,
            "Actual Pen %": f"{pen_num:.1f}%",
            "Gap %": f"{gap_pct*100:+.1f}%",
            "Remaining to Achieve": rem_str,
            "Lagging Route": lowest_rt if lowest_rt != "N/A" else "General Market",
            "VS Last Read": pulse_str,
            "Status": status
        })

    df_sku_rep = pd.DataFrame(sku_records)

    # 2. DASHBOARD KPI CARDS
    c1, c2, c3, c4 = st.columns(4)
    if f_pjp is not None:
        c1.markdown(f'<div class="metric-card"><div class="metric-val">{total_planned_outlets:,}</div><div class="metric-lbl">Planned Outlets <span style="font-size:10px;color:#dc2626;">[{billed_outlets} Billed | {zero_sale_outlets} Zero]</span></div></div>', unsafe_allow_html=True)
    else:
        c1.markdown(f'<div class="metric-card"><div class="metric-val">{billed_outlets:,}</div><div class="metric-lbl">Productive Outlets (Billed)</div></div>', unsafe_allow_html=True)
        
    c2.markdown(f'<div class="metric-card"><div class="metric-val">{overall_pen_pct:.1f}%</div><div class="metric-lbl">Overall Coverage Pen %</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-val">{avg_sku_per_bill:.2f}</div><div class="metric-lbl">Avg SKU Per Bill</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-val">{hit_count} / {len(target_mapping)} ({(hit_count / len(target_mapping) * 100):.1f}%)</div><div class="metric-lbl">Target Achieved SKUs 🎯</div></div>', unsafe_allow_html=True)

    # Live Intelligence Strip
    st.write("")
    top_sku_text = f"🟢 <b>Top SKU:</b> {best_sku_name} ({best_sku_pen * 100:.1f}% Pen)" if best_sku_pen >= 0 else "🟢 <b>Top SKU:</b> N/A"
    worst_sku_text = f"🔴 <b>Critical Lag:</b> {worst_sku_name} ({worst_sku_rem:,} Outlets Needed)" if worst_sku_name else "🔴 <b>Critical Lag:</b> N/A"
    zero_outlets_text = f"⚠️ <b>Territory Pulse:</b> {zero_sale_outlets:,} Zero-Sale Outlets in Active PJP"

    alert_c1, alert_c2, alert_c3 = st.columns(3)
    with alert_c1:
        st.markdown(f'<div class="saas-alert" style="border-left: 5px solid #16a34a;"><span>{top_sku_text}</span></div>', unsafe_allow_html=True)
    with alert_c2:
        st.markdown(f'<div class="saas-alert" style="border-left: 5px solid #dc2626;"><span>{worst_sku_text}</span></div>', unsafe_allow_html=True)
    with alert_c3:
        st.markdown(f'<div class="saas-alert" style="border-left: 5px solid #f59e0b;"><span>{zero_outlets_text}</span></div>', unsafe_allow_html=True)

    # 3. TOP & BOTTOM LEADERBOARD
    sdm_performance = []
    all_sdms = [s for s in df_sales['SDM/SDO/SDS'].dropna().unique() if str(s).strip() and str(s) != "Unknown SDM"]
    
    for s_name in all_sdms:
        s_sales = df_sales[df_sales['SDM/SDO/SDS'] == s_name]
        if len(s_sales) == 0:
            continue
            
        if df_pjp_master is not None and 'SDM/SDO/SDS' in df_pjp_master.columns and (df_pjp_master['SDM/SDO/SDS'] == s_name).any():
            s_planned = df_pjp_master[df_pjp_master['SDM/SDO/SDS'] == s_name]['Outlet_Code'].nunique()
        else:
            s_planned = s_sales['Outlet_Code'].nunique()
            
        s_billed = s_sales['Outlet_Code'].nunique()
        if s_planned == 0:
            continue
            
        s_pen_pct = (s_billed / s_planned) * 100
        s_sku_bill = s_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean() if len(s_sales) > 0 else 0.0
        s_sku_grp = s_sales.groupby('Target_Product_Group', observed=True)['Outlet_Code'].nunique()
        s_hit = sum(1 for sku_k, tgt_v in target_mapping.items() if (s_sku_grp.get(sku_k, 0) / s_planned) >= tgt_v)
        s_rate = (s_hit / len(target_mapping)) * 100
        
        sdm_performance.append({
            'Name': s_name, 
            'Planned': s_planned,
            'Billed': s_billed,
            'Penetration_%': s_pen_pct,
            'SKU_Bill': s_sku_bill, 
            'Hit_Count': s_hit, 
            'Hit_Rate': s_rate
        })
        
    if sdm_performance:
        df_sdm_rank = pd.DataFrame(sdm_performance).sort_values(by=['Penetration_%', 'Hit_Rate'], ascending=False)
    else:
        df_sdm_rank = pd.DataFrame(columns=['Name', 'Planned', 'Billed', 'Penetration_%', 'SKU_Bill', 'Hit_Count', 'Hit_Rate'])

    dist_performance = []
    all_dists = [d for d in df_sales['Dist_Name'].dropna().unique() if str(d).strip()]
    
    for d_name in all_dists:
        d_sales = df_sales[df_sales['Dist_Name'] == d_name]
        if len(d_sales) == 0:
            continue
            
        if df_pjp_master is not None:
            d_planned = df_pjp_master[df_pjp_master['Dist_Name'] == d_name]['Outlet_Code'].nunique()
        else:
            d_planned = d_sales['Outlet_Code'].nunique()
            
        d_billed = d_sales['Outlet_Code'].nunique()
        if d_planned == 0:
            continue
            
        d_pen_pct = (d_billed / d_planned) * 100
        d_sku_bill = d_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean() if len(d_sales) > 0 else 0.0
        d_sku_grp = d_sales.groupby('Target_Product_Group', observed=True)['Outlet_Code'].nunique()
        d_hit = sum(1 for sku_k, tgt_v in target_mapping.items() if (d_sku_grp.get(sku_k, 0) / d_planned) >= tgt_v)
        d_rate = (d_hit / len(target_mapping)) * 100
        
        dist_performance.append({
            'Name': d_name, 
            'Planned': d_planned,
            'Billed': d_billed,
            'Penetration_%': d_pen_pct,
            'SKU_Bill': d_sku_bill, 
            'Hit_Count': d_hit, 
            'Hit_Rate': d_rate
        })
        
    if dist_performance:
        df_dist_rank = pd.DataFrame(dist_performance).sort_values(by=['Penetration_%', 'Hit_Rate'], ascending=False)
    else:
        df_dist_rank = pd.DataFrame(columns=['Name', 'Planned', 'Billed', 'Penetration_%', 'SKU_Bill', 'Hit_Count', 'Hit_Rate'])

    if len(df_sdm_rank) > 0 or len(df_dist_rank) > 0:
        st.write("")
        l_col1, l_col2, l_col3, l_col4 = st.columns(4)
        
        if len(df_sdm_rank) > 0:
            top_sdm = df_sdm_rank.iloc[0]
            bot_sdm = df_sdm_rank.iloc[-1]
            with l_col1:
                st.markdown(f"""
                <div class="lead-card-top">
                    <div class="lead-title" style="color: #16a34a;">🏆 Top SDM (Penetration)</div>
                    <div class="lead-name">{top_sdm['Name']}</div>
                    <div class="lead-stats">Pen: <b>{top_sdm['Penetration_%']:.1f}%</b> ({top_sdm['Billed']}/{top_sdm['Planned']}) | Hit: <b>{top_sdm['Hit_Rate']:.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
            with l_col2:
                st.markdown(f"""
                <div class="lead-card-bottom">
                    <div class="lead-title" style="color: #dc2626;">🔻 Bottom SDM (Penetration)</div>
                    <div class="lead-name">{bot_sdm['Name']}</div>
                    <div class="lead-stats">Pen: <b>{bot_sdm['Penetration_%']:.1f}%</b> ({bot_sdm['Billed']}/{bot_sdm['Planned']}) | Hit: <b>{bot_sdm['Hit_Rate']:.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)

        if len(df_dist_rank) > 0:
            top_dist = df_dist_rank.iloc[0]
            bot_dist = df_dist_rank.iloc[-1]
            with l_col3:
                st.markdown(f"""
                <div class="lead-card-top">
                    <div class="lead-title" style="color: #16a34a;">🥇 Top Distributor</div>
                    <div class="lead-name">{top_dist['Name']}</div>
                    <div class="lead-stats">Pen: <b>{top_dist['Penetration_%']:.1f}%</b> ({top_dist['Billed']}/{top_dist['Planned']}) | Hit: <b>{top_dist['Hit_Rate']:.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
            with l_col4:
                st.markdown(f"""
                <div class="lead-card-bottom">
                    <div class="lead-title" style="color: #dc2626;">⚠️ Bottom Distributor</div>
                    <div class="lead-name">{bot_dist['Name']}</div>
                    <div class="lead-stats">Pen: <b>{bot_dist['Penetration_%']:.1f}%</b> ({bot_dist['Billed']}/{bot_dist['Planned']}) | Hit: <b>{bot_dist['Hit_Rate']:.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)

    st.write("")

    # 4. NATIVE STREAMLIT BORDERED FILTER CONTAINER (ALWAYS CLICKABLE WITHOUT SCROLLING)
    with st.container(border=True):
        st.markdown('<div style="font-size:11px;font-weight:800;color:#004B93;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">🔍 HIERARCHY FILTERS & GLOBAL FONT SIZE ADJUSTMENT</div>', unsafe_allow_html=True)
        filt_c1, filt_c2, filt_c3, filt_c4, filt_c5, filt_c6 = st.columns([1, 1.2, 1.2, 1.2, 1.2, 1.2])
        
        raw_units = list(base_hierarchy_df['Unit_Name'].dropna().unique()) if 'Unit_Name' in base_hierarchy_df.columns else []
        clean_units = [str(u) for u in raw_units if str(u).strip() and str(u) != "General Unit"]
        unit_list = ["All Units"] + sorted(list(set(clean_units))) if clean_units else ["All Units"]
        with filt_c1:
            st.selectbox("Unit / Zone", unit_list, key="sel_unit_key")

        temp_sales_dist = df_sales if sel_unit == "All Units" else df_sales[df_sales['Unit_Name'] == sel_unit]
        dist_list = ["All Distributors"] + sorted([str(x) for x in temp_sales_dist['Dist_Name'].dropna().unique() if str(x).strip()])
        with filt_c2:
            st.selectbox("Distributor", dist_list, key="sel_dist_key")

        temp_sales_sdm = temp_sales_dist if sel_dist == "All Distributors" else temp_sales_dist[temp_sales_dist['Dist_Name'] == sel_dist]
        raw_sdms = list(temp_sales_sdm['SDM/SDO/SDS'].dropna().unique())
        clean_sdms = [str(x) for x in raw_sdms if str(x).strip() and str(x) != "Unknown SDM"]
        sdm_list = ["All SDMs"] + sorted(list(set(clean_sdms)))
        with filt_c3:
            st.selectbox("SDM / SDS / TSE", sdm_list, key="sel_sdm_key")

        temp_sales_bkr = temp_sales_sdm if sel_sdm == "All SDMs" else temp_sales_sdm[temp_sales_sdm['SDM/SDO/SDS'] == sel_sdm]
        booker_list = ["All Bookers"] + sorted([str(x) for x in temp_sales_bkr['BOOKER_Name'].dropna().unique() if str(x).strip()])
        with filt_c4:
            st.selectbox("Booker (PSR)", booker_list, key="sel_booker_key")

        temp_sales_rt = temp_sales_bkr if sel_booker == "All Bookers" else temp_sales_bkr[temp_sales_bkr['BOOKER_Name'] == sel_booker]
        pjp_list = ["All Routes"] + sorted([str(x) for x in temp_sales_rt['PJP_Name'].dropna().unique() if str(x).strip()])
        with filt_c5:
            st.selectbox("Route (PJP)", pjp_list, key="sel_pjp_key")

        with filt_c6:
            global_font_px = st.slider("🔠 Font Size (All Tabs)", min_value=9, max_value=16, value=12, step=1)

    pad_v = max(2, int((global_font_px - 7) * 1.4))
    pad_h = max(4, int((global_font_px - 6) * 1.6))
    badge_pad = f"{max(1, pad_v // 2)}px {max(4, pad_h // 2)}px"
    badge_sz = f"{max(8, global_font_px - 2)}px"

    # 5. NAVIGATION TABS
    tab1, tab_pack, tab2, tab_outlets = st.tabs([
        "🎯 SKU Target & Penetration", 
        "📦 Pack-Wise Penetration",
        "👤 Booker (PSR) Scorecard", 
        "🔍 Outlets Missing SKU & Brand Filter"
    ])

    # TAB 1: SKU PENETRATION TABLE
    with tab1:
        q_col1, q_col2, q_col3 = st.columns([2.2, 1.5, 1.3])
        with q_col1:
            sku_view_filter = st.radio(
                "Filter Table:", 
                ["All SKUs", "🎯 Hit Only", "⚠️ Miss Only"], 
                horizontal=True,
                label_visibility="collapsed"
            )
        with q_col2:
            st.markdown(f"<div style='padding-top:4px;font-size:12px;font-weight:700;color:#475569;'>Universe: <b>{total_planned_outlets:,} Outlets</b></div>", unsafe_allow_html=True)
        with q_col3:
            with st.expander("📱 WhatsApp Summary"):
                wa_msg = f"*🥤 PEPSICO SALES PENETRATION REPORT*\n" \
                         f"📊 *Universe:* {total_planned_outlets:,} Planned Outlets ({billed_outlets} Billed)\n" \
                         f"📈 *Penetration:* {overall_pen_pct:.1f}% | *SKU/Bill:* {avg_sku_per_bill:.2f}\n" \
                         f"🎯 *Targets Achieved:* {hit_count}/{len(target_mapping)}\n" \
                         f"🟢 *Top SKU:* {best_sku_name} ({best_sku_pen*100:.1f}%)\n" \
                         f"🔴 *Critical Focus SKU:* {worst_sku_name} ({worst_sku_rem:,} Outlets Gap)\n" \
                         f"⚠️ *Zero-Sale Outlets:* {zero_sale_outlets:,}"
                st.code(wa_msg, language="markdown")

        filtered_df_sku = df_sku_rep.copy()
        if sku_view_filter == "🎯 Hit Only":
            filtered_df_sku = filtered_df_sku[filtered_df_sku['Status'].str.contains("Hit")]
        elif sku_view_filter == "⚠️ Miss Only":
            filtered_df_sku = filtered_df_sku[~filtered_df_sku['Status'].str.contains("Hit")]

        html_lines = [
            f'<table style="width:100%; border-collapse:collapse; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #cbd5e1; font-size:{global_font_px}px; line-height:1.2; box-shadow:0 2px 6px rgba(0,0,0,0.05);">',
            '<thead>',
            f'<tr style="background:#002244; color:#ffffff; font-weight:800;">',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #003366;">SKU / Group Name</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Target</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Productive</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366; min-width:95px;">Actual Pen %</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Gap</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #003366;">Remaining Outlets</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #003366;">Lagging Route (Retail)</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">VS Last Read</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Status</th>',
            '</tr>',
            '</thead>',
            '<tbody>'
        ]

        for _, row in filtered_df_sku.iterrows():
            pen_val = float(row['Actual Pen Num'])
            pen_clamped = round(min(100.0, max(0.0, pen_val)), 1)
            status_str = str(row['Status'])
            
            if "Hit" in status_str:
                fill_color = "#bbf7d0"
                badge_html = f'<span style="background:#dcfce7; color:#15803d; padding:{badge_pad}; border-radius:4px; font-weight:800; font-size:{badge_sz};">Hit 🎯</span>'
                gap_color = "#15803d"
            elif "Close" in status_str:
                fill_color = "#fef08a"
                badge_html = f'<span style="background:#fef9c3; color:#a16207; padding:{badge_pad}; border-radius:4px; font-weight:800; font-size:{badge_sz};">Close ⚠️</span>'
                gap_color = "#b45309"
            else:
                fill_color = "#fecaca"
                badge_html = f'<span style="background:#fee2e2; color:#b91c1c; padding:{badge_pad}; border-radius:4px; font-weight:800; font-size:{badge_sz};">Far ❌</span>'
                gap_color = "#b91c1c"

            cell_bar = (
                f'<td style="padding:0; border:1px solid #e2e8f0; background:#ffffff; text-align:center;">'
                f'<div style="background:linear-gradient(90deg, {fill_color} 0%, {fill_color} {pen_clamped}%, #ffffff {pen_clamped}%, #ffffff 100%); width:100%; height:100%; padding:{pad_v}px {pad_h}px; font-weight:800; color:#0f172a;">'
                f'{pen_val:.1f}%'
                f'</div></td>'
            )

            row_html = (
                f'<tr style="border-bottom:1px solid #e2e8f0;">'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; font-weight:700; color:#0f172a;">{row["SKU / Group Name"]}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; color:#475569; font-weight:600;">{row["Target %"]}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700; color:#003366;">{row["Productive"]:,}</td>'
                f'{cell_bar}'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:800; color:{gap_color};">{row["Gap %"]}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; font-weight:600; color:#334155;">{row["Remaining to Achieve"]}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; color:#475569;">{row["Lagging Route"]}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700; color:#0284c7; white-space:nowrap;">{row["VS Last Read"]}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; white-space:nowrap;">{badge_html}</td>'
                f'</tr>'
            )
            html_lines.append(row_html)

        html_lines.append('</tbody></table>')
        final_table_html = "".join(html_lines)
        
        st.markdown(final_table_html, unsafe_allow_html=True)

    # TAB 2: PACK-WISE PENETRATION
    with tab_pack:
        st.subheader("📦 Overall Pack-Wise Penetration (All Flavours Combined)")
        valid_packs = f_sales[f_sales['PKG_NAME'] != ""]
        if len(valid_packs) > 0:
            pack_agg = valid_packs.groupby('PKG_NAME', observed=True).agg(
                Productive_Outlets=('Outlet_Code', 'nunique'),
                Total_Cases=('Sales_Raw Cases', 'sum'),
                Invoices=('INVOICE_NUMBER', 'nunique')
            ).reset_index()

            pack_agg['Pen_Num'] = ((pack_agg['Productive_Outlets'] / total_planned_outlets) * 100).round(1)
            pack_agg['Drop Size (Cases)'] = (pack_agg['Total_Cases'] / pack_agg['Productive_Outlets']).round(2)
            pack_agg = pack_agg.sort_values(by='Productive_Outlets', ascending=False)

            pack_html = [
                f'<table style="width:100%; border-collapse:collapse; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #cbd5e1; font-size:{global_font_px}px; line-height:1.2;">',
                '<thead>',
                '<tr style="background:#002244; color:#ffffff; font-weight:800;">',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #003366;">Package Name</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Productive Outlets</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Total Cases</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Total Bills</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Penetration %</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Drop Size (Cases)</th>',
                '</tr>',
                '</thead>',
                '<tbody>'
            ]
            for _, prow in pack_agg.iterrows():
                p_val = min(100.0, max(0.0, float(prow['Pen_Num'])))
                p_bar = (
                    f'<td style="padding:0; border:1px solid #e2e8f0; text-align:center;">'
                    f'<div style="background:linear-gradient(90deg, #bae6fd 0%, #bae6fd {p_val}%, #ffffff {p_val}%, #ffffff 100%); padding:{pad_v}px {pad_h}px; font-weight:800;">{prow["Pen_Num"]:.1f}%</div></td>'
                )
                pack_html.append(
                    f'<tr>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; font-weight:700;">{prow["PKG_NAME"]}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700; color:#003366;">{prow["Productive_Outlets"]:,}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center;">{prow["Total_Cases"]:,.1f}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center;">{prow["Invoices"]:,}</td>'
                    f'{p_bar}'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700;">{prow["Drop Size (Cases)"]:.2f}</td>'
                    f'</tr>'
                )
            pack_html.append('</tbody></table>')
            st.markdown("".join(pack_html), unsafe_allow_html=True)
        else:
            st.info("Sales file me 'PKG_NAME' data dastiyab nahi hai.")

    # TAB 3: BOOKER SCORECARD
    with tab2:
        st.subheader("👤 Booker / Pre-Seller (PSR) Scorecard")
        st.caption("Ranked Number-Wise by Overall Penetration % (Highest to Lowest).")

        booker_rows = []
        booker_iter = f_pjp.groupby('BOOKER_Name', observed=True) if f_pjp is not None else f_sales.groupby('BOOKER_Name', observed=True)
        
        for b_name, b_meta in booker_iter:
            if str(b_name).strip() == "":
                continue
            
            b_total_outlets = b_meta['Outlet_Code'].nunique()
            b_sales = f_sales[f_sales['BOOKER_Name'] == b_name]
            b_billed = b_sales['Outlet_Code'].nunique()
            
            if b_total_outlets == 0 and b_billed == 0:
                continue

            base_count = b_total_outlets if f_pjp is not None else b_billed
            b_pen_pct = (b_billed / base_count * 100) if base_count > 0 else 0.0
            b_sku_per_bill = b_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean() if len(b_sales) > 0 else 0.0
            
            b_achieved = 0
            b_sku_grp = b_sales.groupby('Target_Product_Group', observed=True)['Outlet_Code'].nunique()
            
            for sku_name, tgt in target_mapping.items():
                if base_count > 0 and (b_sku_grp.get(sku_name, 0) / base_count) >= tgt:
                    b_achieved += 1

            dist = b_meta['Dist_Name'].iloc[0] if 'Dist_Name' in b_meta.columns else ""
            sdm = b_meta['SDM/SDO/SDS'].iloc[0] if 'SDM/SDO/SDS' in b_meta.columns else ""

            booker_rows.append({
                'Distributor': dist,
                'SDM': sdm,
                'Booker Name': b_name,
                'Planned': base_count,
                'Billed': b_billed,
                'Zero Sale': max(0, base_count - b_billed),
                'Pen_Num': round(b_pen_pct, 1),
                'SKU / Bill': round(b_sku_per_bill, 2),
                'Targets Achieved': f"{b_achieved} / {len(target_mapping)}",
                'Hit Rate %': round((b_achieved / len(target_mapping)) * 100, 1),
                'Status': "Star ⭐" if b_pen_pct >= 80 else ("Good 👍" if b_pen_pct >= 60 else "Needs Focus ⚠️")
            })

        df_booker_score = pd.DataFrame(booker_rows)
        if len(df_booker_score) > 0:
            df_booker_score = df_booker_score.sort_values(by=['Pen_Num', 'Hit Rate %'], ascending=False).reset_index(drop=True)
            df_booker_score.insert(0, 'Rank #', range(1, len(df_booker_score) + 1))

            bkr_html = [
                f'<table style="width:100%; border-collapse:collapse; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #cbd5e1; font-size:{global_font_px}px; line-height:1.2;">',
                '<thead>',
                '<tr style="background:#002244; color:#ffffff; font-weight:800;">',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Rank</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #003366;">Booker Name</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #003366;">SDM</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Planned</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Billed</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Zero Sale</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366; min-width:95px;">Penetration %</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">SKU/Bill</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Targets Hit</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Status</th>',
                '</tr>',
                '</thead>',
                '<tbody>'
            ]
            for _, brow in df_booker_score.iterrows():
                b_pen = min(100.0, max(0.0, float(brow['Pen_Num'])))
                b_fill = "#bbf7d0" if b_pen >= 75.0 else ("#fef08a" if b_pen >= 50.0 else "#fecaca")
                b_bar = (
                    f'<td style="padding:0; border:1px solid #e2e8f0; text-align:center;">'
                    f'<div style="background:linear-gradient(90deg, {b_fill} 0%, {b_fill} {b_pen}%, #ffffff {b_pen}%, #ffffff 100%); padding:{pad_v}px {pad_h}px; font-weight:800;">{brow["Pen_Num"]:.1f}%</div></td>'
                )
                bkr_html.append(
                    f'<tr>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:800;">{brow["Rank #"]}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; font-weight:700;">{brow["Booker Name"]}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; color:#475569;">{brow["SDM"]}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center;">{brow["Planned"]}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700; color:#15803d;">{brow["Billed"]}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700; color:#dc2626;">{brow["Zero Sale"]}</td>'
                    f'{b_bar}'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700;">{brow["SKU / Bill"]:.2f}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center;">{brow["Targets Achieved"]}</td>'
                    f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700;">{brow["Status"]}</td>'
                    f'</tr>'
                )
            bkr_html.append('</tbody></table>')
            st.markdown("".join(bkr_html), unsafe_allow_html=True)

    # TAB 4: OUTLETS MISSING SKU & MISSING BRAND FILTER
    with tab_outlets:
        st.subheader("🔍 Outlets Missing SKU & Brand Gap Analysis")
        st.caption("PJP Planned days, missing SKUs, aur missing core brands (Pepsi, M.Dew, 7-UP, Sting, Aquafina, Revive) ko filter karein.")

        all_target_skus = set(target_mapping.keys())
        total_sku_count = len(all_target_skus)
        core_brands_set = set(CORE_BRANDS)

        valid_target_sales = f_sales[f_sales['Target_Product_Group'].isin(all_target_skus)]
        outlet_bought_sets = valid_target_sales.groupby('Outlet_Code', observed=True)['Target_Product_Group'].apply(lambda s: set(s)).to_dict()
        outlet_bought_brands = f_sales.groupby('Outlet_Code', observed=True)['Brand_Name'].apply(lambda s: set(s)).to_dict()

        if f_pjp is not None:
            outlet_meta = f_pjp[['Outlet_Code', 'Outlet_Name', 'PJP_Name', 'BOOKER_Name', 'Dist_Name', 'SDM/SDO/SDS', 'Planned_Days'] + DAYS_LIST].copy()
        else:
            outlet_meta = f_sales[['Outlet_Code', 'Outlet_Name', 'PJP_Name', 'BOOKER_Name', 'Dist_Name', 'SDM/SDO/SDS']].drop_duplicates('Outlet_Code').copy()
            outlet_meta['Planned_Days'] = "N/A (Upload PJP)"
            for day in DAYS_LIST:
                outlet_meta[day] = 1

        def get_missing_details(row):
            ocode = row['Outlet_Code']
            bought_skus = outlet_bought_sets.get(ocode, set())
            missing_skus = all_target_skus - bought_skus
            is_zero = len(bought_skus) == 0
            
            bought_brands = outlet_bought_brands.get(ocode, set())
            missing_brands = sorted(list(core_brands_set - bought_brands))
            missing_brands_str = ", ".join(missing_brands) if missing_brands else "All Core Brands Active ✅"
            
            return (
                len(bought_skus), 
                len(missing_skus), 
                ", ".join(sorted(missing_skus)), 
                missing_brands_str,
                missing_brands,
                ("Zero Sale ⚠️" if is_zero else "Billed ✅")
            )

        details = outlet_meta.apply(get_missing_details, axis=1)
        outlet_meta['SKUs_Bought'] = [d[0] for d in details]
        outlet_meta['SKUs_Missing'] = [d[1] for d in details]
        outlet_meta['Missing_Products_List'] = [d[2] for d in details]
        outlet_meta['Missing_Brands'] = [d[3] for d in details]
        outlet_meta['Missing_Brands_Raw'] = [d[4] for d in details]
        outlet_meta['Billing_Status'] = [d[5] for d in details]

        f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([1.3, 1.3, 1.1, 1.3, 1.1])
        
        with f_col1:
            brand_options = ["All Brands"] + CORE_BRANDS
            selected_missing_brand = st.selectbox("🏷️ Missing Brand:", brand_options)

        with f_col2:
            sku_options = ["All Outlets (Any SKU)"] + sorted(list(target_mapping.keys()))
            selected_pack = st.selectbox("🎯 Filter Bought SKU:", sku_options)

        with f_col3:
            day_options = ["All Days"] + DAYS_LIST
            selected_day = st.selectbox("📅 Planned Day:", day_options)
            
        with f_col4:
            missing_range = st.slider(
                "⚠️ Missing SKUs:", 
                min_value=0, 
                max_value=total_sku_count, 
                value=(1, total_sku_count), 
                step=1
            )
            
        with f_col5:
            status_filter = st.selectbox("Billing Status:", ["All Outlets", "Billed Outlets Only", "Zero-Sale Outlets Only"])

        filtered_outlets = outlet_meta[
            (outlet_meta['SKUs_Missing'] >= missing_range[0]) & 
            (outlet_meta['SKUs_Missing'] <= missing_range[1])
        ]

        if selected_missing_brand != "All Brands":
            filtered_outlets = filtered_outlets[filtered_outlets['Missing_Brands_Raw'].apply(lambda lst: selected_missing_brand in lst)]

        if selected_day != "All Days" and f_pjp is not None:
            filtered_outlets = filtered_outlets[filtered_outlets[selected_day] == 1]

        if status_filter == "Billed Outlets Only":
            filtered_outlets = filtered_outlets[filtered_outlets['Billing_Status'] == "Billed ✅"]
        elif status_filter == "Zero-Sale Outlets Only":
            filtered_outlets = filtered_outlets[filtered_outlets['Billing_Status'] == "Zero Sale ⚠️"]

        if selected_pack != "All Outlets (Any SKU)":
            pack_buyers = set(valid_target_sales[valid_target_sales['Target_Product_Group'] == selected_pack]['Outlet_Code'].unique())
            filtered_outlets = filtered_outlets[filtered_outlets['Outlet_Code'].isin(pack_buyers)]

        st.markdown(f"**Found {len(filtered_outlets):,} outlets** matching filters (Missing Brand: **{selected_missing_brand}** | Day: **{selected_day}** | Missing SKUs: **{missing_range[0]}-{missing_range[1]}**).")

        display_cols = ['Outlet_Code', 'Outlet_Name', 'BOOKER_Name', 'PJP_Name', 'Planned_Days', 'Billing_Status', 'Missing_Brands', 'SKUs_Missing', 'SKUs_Bought', 'Missing_Products_List']
        st.dataframe(
            filtered_outlets[display_cols].sort_values(by='SKUs_Missing', ascending=False), 
            use_container_width=True, 
            height=480
        )

    # BOTTOM EXPORT BAR: EXCEL DOWNLOAD + IMAGE (PNG) DOWNLOAD
    st.write("")
    dl_col1, dl_col2, _ = st.columns([1.4, 1.5, 3.1])
    
    with dl_col1:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_sku_rep.drop(columns=['Actual Pen Num']).to_excel(writer, sheet_name='SKU Penetration', index=False)
            if len(valid_packs) > 0:
                pack_agg.drop(columns=['Pen_Num']).to_excel(writer, sheet_name='Pack Penetration', index=False)
            if len(df_booker_score) > 0:
                df_booker_score.to_excel(writer, sheet_name='Booker Scorecard', index=False)
            filtered_outlets.drop(columns=['Missing_Brands_Raw']).to_excel(writer, sheet_name='Missing & Zero Outlets', index=False)

        st.download_button(
            label="📥 Download Full Report (Excel)",
            data=output.getvalue(),
            file_name="Pepsi_Penetration_Fast_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with dl_col2:
        png_title = f"PEPSICO PENETRATION SUMMARY | {sel_dist} | {sel_sdm}"
        png_sub = f"Planned: {total_planned_outlets:,} | Billed: {billed_outlets:,} | Coverage: {overall_pen_pct:.1f}% | SKU/Bill: {avg_sku_per_bill:.2f} | Targets Hit: {hit_count}/{len(target_mapping)}"
        png_bytes = generate_table_png(filtered_df_sku, png_title, png_sub)
        if png_bytes is not None:
            st.download_button(
                label="🖼️ Download Report Image (PNG)",
                data=png_bytes,
                file_name="Pepsi_Penetration_Summary.png",
                mime="image/png"
            )

else:
    st.info("👈 Baraye meharbani sidebar se Sales Raw Data upload karein. (GitHub mein 'targets.xlsx' aur 'pjp.xlsx' maujood hon to woh automatic load ho jayengi).")
