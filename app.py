import io
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="PepsiCo Sales Penetration Tracker",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Pepsi Styling & Themes
st.markdown("""
<style>
    .header-container {
        display: flex;
        align-items: center;
        gap: 18px;
        background: linear-gradient(135deg, #002244 0%, #004B93 60%, #C9082A 100%);
        padding: 16px 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 34, 68, 0.15);
    }
    .header-logo {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: white;
        padding: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    .header-title {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #ffffff;
    }
    .header-subtitle {
        font-size: 13px;
        color: #e0e8f5;
        margin: 0;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 14px;
        border-left: 5px solid #004B93;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        transition: transform 0.15s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-val { 
        font-size: 24px; 
        font-weight: 800; 
        color: #002244; 
    }
    .metric-lbl { 
        font-size: 12px; 
        color: #555555; 
        font-weight: 600; 
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Top & Bottom Leaderboard Cards */
    .lead-card-top {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 6px solid #16a34a;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .lead-card-bottom {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 6px solid #dc2626;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .lead-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .lead-name {
        font-size: 15px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 2px;
    }
    .lead-stats {
        font-size: 12px;
        font-weight: 600;
        color: #4b5563;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        border-radius: 6px 6px 0px 0px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

# Pepsi Brand Header with Official SVG Logo
st.markdown("""
<div class="header-container">
    <div class="header-logo">
        <svg viewBox="0 0 100 100" width="52" height="52">
            <circle cx="50" cy="50" r="48" fill="#004B93" />
            <path d="M 6,50 A 44,44 0 0,1 94,50 Q 75,70 50,50 T 6,50 Z" fill="#C9082A" />
            <path d="M 6,50 A 44,44 0 0,0 94,50 Q 75,30 50,50 T 6,50 Z" fill="#FFFFFF" />
            <path d="M 6,50 A 44,44 0 0,0 94,50 Q 75,70 50,50 T 6,50 Z" fill="#004B93" />
        </svg>
    </div>
    <div>
        <h1 class="header-title">PEPSICO SALES PENETRATION TRACKER</h1>
        <p class="header-subtitle">PJP Planned Coverage • Pre-Seller Productivity (SKU/Bill) • Outlet Missing Gap Analysis</p>
    </div>
</div>
""", unsafe_allow_html=True)

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
    '500 ML PET Sting-STING - BB': 0.35,
    '500 ML PET AF-Aquafina': 0.35,
    '1500 ML PET AF-Aquafina': 0.35,
    '500 ML PET (CSD Combined)': 0.35,
    '300 ML PET Revive (Combined)': 0.40
}

DAYS_LIST = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

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

def load_target_data(target_bytes):
    targets_dict = DEFAULT_TARGETS.copy()
    if target_bytes is not None:
        try:
            df_t = pd.read_excel(io.BytesIO(target_bytes))
            p_col = get_best_col(df_t.columns, ['productname', 'product', 'sku', 'skuname', 'name'])
            t_col = get_best_col(df_t.columns, ['target', 'target%', 'targetpct', 'penetrationtarget'])
            
            if p_col and t_col:
                for _, row in df_t.iterrows():
                    val = row[t_col]
                    prod_name = str(row[p_col]).strip()
                    if pd.notna(val):
                        val = float(val) if float(val) <= 1.0 else float(val) / 100.0
                        if prod_name == '500 ML PET':
                            targets_dict['500 ML PET (CSD Combined)'] = val
                        elif 'Revive' in prod_name:
                            targets_dict['300 ML PET Revive (Combined)'] = 0.40
                        else:
                            targets_dict[prod_name] = val
        except Exception as e:
            st.sidebar.error(f"Target error: {e}")
    targets_dict['300 ML PET Revive (Combined)'] = 0.40
    return targets_dict

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

    # Explicit column detection
    dist_code_col = get_best_col(df.columns, ['distcode', 'distid', 'distributorcode', 'dist_code'])
    
    # Non-ID columns
    name_cols = [c for c in df.columns if not any(x in clean_col_str(c) for x in ['id', 'code'])]
    dist_name_col = get_best_col(name_cols, ['distname', 'distributor', 'dist'])

    sdm_id_col = get_best_col(df.columns, ['sdmsdosdsid', 'sdmid', 'sdoid', 'tseid', 'sdm_id'])
    sdm_name_col = get_best_col(name_cols, ['sdmsdosds', 'sdmname', 'sdm', 'sdo', 'tse'])

    standard_df = pd.DataFrame()
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

    for cat_col in ['Dist_Name', 'SDM/SDO/SDS', 'BOOKER_Name', 'PJP_Name', 'Target_Product_Group', 'PKG_NAME']:
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
        oc_col = get_best_col(df_pjp.columns, ['outletid', 'outletcode', 'customercode', 'code'])
        pjp_std['Outlet_Code'] = df_pjp[oc_col].apply(clean_id_str) if oc_col else ""
        
        on_col = get_best_col(name_cols, ['outletname', 'customername', 'shopname', 'name'])
        pjp_std['Outlet_Name'] = df_pjp[on_col].astype(str).str.strip() if on_col else ""
        
        b_col = get_best_col(name_cols, ['bookername', 'booker', 'psr', 'orderbooker'])
        pjp_std['BOOKER_Name'] = df_pjp[b_col].astype(str).str.strip() if b_col else ""
        
        r_col = get_best_col(name_cols, ['routename', 'pjpname', 'pjp', 'route'])
        pjp_std['PJP_Name'] = df_pjp[r_col].astype(str).str.strip() if r_col else ""
        
        d_code_col = get_best_col(df_pjp.columns, ['distid', 'distcode', 'distributorid'])
        d_name_col = get_best_col(name_cols, ['distname', 'distributor', 'dist'])
        
        pjp_std['Dist_Code'] = df_pjp[d_code_col].apply(clean_id_str) if d_code_col else ""
        pjp_std['Raw_Dist_Name'] = df_pjp[d_name_col].astype(str).str.strip() if d_name_col else ""
        
        # Link SDM and full formatted Dist_Name
        if df_sales_ref is not None:
            # 1. Map Distributor Name
            sales_dist_map = df_sales_ref[df_sales_ref['Dist_Code'] != ""].drop_duplicates('Dist_Code').set_index('Dist_Code')['Dist_Name'].to_dict()
            pjp_std['Dist_Name'] = pjp_std['Dist_Code'].map(sales_dist_map)
            missing_dist = pjp_std['Dist_Name'].isna()
            pjp_std.loc[missing_dist, 'Dist_Name'] = pjp_std.loc[missing_dist].apply(
                lambda r: f"{r['Raw_Dist_Name']} - {r['Dist_Code']}" if r['Raw_Dist_Name'] and r['Dist_Code'] else r['Raw_Dist_Name'], axis=1
            )
            
            # 2. Smart SDM Linkage: First by Booker_Name (because each booker has exactly 1 SDM)
            valid_sales = df_sales_ref[df_sales_ref['SDM/SDO/SDS'].astype(str).str.strip() != ""]
            booker_to_sdm = valid_sales.drop_duplicates('BOOKER_Name').set_index('BOOKER_Name')['SDM/SDO/SDS'].to_dict()
            outlet_to_sdm = valid_sales.drop_duplicates('Outlet_Code').set_index('Outlet_Code')['SDM/SDO/SDS'].to_dict()
            dist_to_sdm = valid_sales.drop_duplicates('Dist_Code').set_index('Dist_Code')['SDM/SDO/SDS'].to_dict()

            pjp_std['SDM/SDO/SDS'] = pjp_std['BOOKER_Name'].map(booker_to_sdm)
            # Fallback 1: Outlet Code
            need_sdm = pjp_std['SDM/SDO/SDS'].isna()
            pjp_std.loc[need_sdm, 'SDM/SDO/SDS'] = pjp_std.loc[need_sdm, 'Outlet_Code'].map(outlet_to_sdm)
            # Fallback 2: Dist Code
            need_sdm2 = pjp_std['SDM/SDO/SDS'].isna()
            pjp_std.loc[need_sdm2, 'SDM/SDO/SDS'] = pjp_std.loc[need_sdm2, 'Dist_Code'].map(dist_to_sdm).fillna("Unknown SDM")
        else:
            pjp_std['Dist_Name'] = pjp_std.apply(
                lambda r: f"{r['Raw_Dist_Name']} - {r['Dist_Code']}" if r['Raw_Dist_Name'] and r['Dist_Code'] else r['Raw_Dist_Name'], axis=1
            )
            pjp_std['SDM/SDO/SDS'] = "Unknown SDM"

        # Map Days (1 = Planned)
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

# Sidebar File Uploaders
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Pepsi_logo_2023.svg/300px-Pepsi_logo_2023.svg.png", width=110)
st.sidebar.header("📁 Data Source Files")
uploaded_sales = st.sidebar.file_uploader("1. Sales Raw Data (.xlsx)", type=["xlsx"])
uploaded_target = st.sidebar.file_uploader("2. Targets File (.xlsx)", type=["xlsx"])
uploaded_pjp = st.sidebar.file_uploader("3. PJP Master File (Optional .xlsx)", type=["xlsx"])

if uploaded_sales is not None:
    sales_bytes = uploaded_sales.getvalue()
    target_bytes = uploaded_target.getvalue() if uploaded_target is not None else None
    pjp_bytes = uploaded_pjp.getvalue() if uploaded_pjp is not None else None
    
    df_sales = load_sales_data(sales_bytes)
    target_mapping = load_target_data(target_bytes)
    df_pjp_master = load_pjp_data(pjp_bytes, df_sales)

    if uploaded_target is not None:
        st.sidebar.success(f"✅ Targets Active: {len(target_mapping)} SKUs")
    else:
        st.sidebar.info("ℹ️ Default Targets Active")
        
    if df_pjp_master is not None:
        st.sidebar.success(f"🗺️ PJP Active: {len(df_pjp_master):,} Operational Planned Outlets")
    else:
        st.sidebar.info("ℹ️ Mode: Billed Outlets Only (PJP upload karein planned universe k liye)")

    # Hierarchy Filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Hierarchy Filters")

    base_hierarchy_df = df_pjp_master if df_pjp_master is not None else df_sales

    dist_list = ["All"] + sorted([str(x) for x in base_hierarchy_df['Dist_Name'].dropna().unique() if str(x).strip()])
    sel_dist = st.sidebar.selectbox("Distributor", dist_list)

    f_sales = df_sales if sel_dist == "All" else df_sales[df_sales['Dist_Name'] == sel_dist]
    f_pjp = df_pjp_master if (df_pjp_master is None or sel_dist == "All") else df_pjp_master[df_pjp_master['Dist_Name'] == sel_dist]

    # Clean SDM list from both PJP and Sales
    sdm_source = f_pjp if (f_pjp is not None and f_pjp['SDM/SDO/SDS'].astype(str).str.strip().ne("").any()) else f_sales
    raw_sdms = list(sdm_source['SDM/SDO/SDS'].dropna().unique())
    clean_sdms = [str(x) for x in raw_sdms if str(x).strip() and str(x) != "Unknown SDM"]
    sdm_list = ["All"] + sorted(list(set(clean_sdms)))

    sel_sdm = st.sidebar.selectbox("SDM / SDS / TSE", sdm_list)
    if sel_sdm != "All":
        f_sales = f_sales[f_sales['SDM/SDO/SDS'] == sel_sdm]
        if f_pjp is not None and 'SDM/SDO/SDS' in f_pjp.columns:
            f_pjp = f_pjp[f_pjp['SDM/SDO/SDS'] == sel_sdm]

    booker_source = f_pjp if f_pjp is not None else f_sales
    booker_list = ["All"] + sorted([str(x) for x in booker_source['BOOKER_Name'].dropna().unique() if str(x).strip()])
    sel_booker = st.sidebar.selectbox("Booker (PSR)", booker_list)
    if sel_booker != "All":
        f_sales = f_sales[f_sales['BOOKER_Name'] == sel_booker]
        if f_pjp is not None:
            f_pjp = f_pjp[f_pjp['BOOKER_Name'] == sel_booker]

    pjp_source = f_pjp if f_pjp is not None else f_sales
    pjp_list = ["All"] + sorted([str(x) for x in pjp_source['PJP_Name'].dropna().unique() if str(x).strip()])
    sel_pjp = st.sidebar.selectbox("Route (PJP)", pjp_list)
    if sel_pjp != "All":
        f_sales = f_sales[f_sales['PJP_Name'] == sel_pjp]
        if f_pjp is not None:
            f_pjp = f_pjp[f_pjp['PJP_Name'] == sel_pjp]

    # Universe & Metrics Calculations
    billed_outlets = f_sales['Outlet_Code'].nunique()
    total_planned_outlets = f_pjp['Outlet_Code'].nunique() if f_pjp is not None else billed_outlets
    zero_sale_outlets = max(0, total_planned_outlets - billed_outlets)
    total_invoices = f_sales['INVOICE_NUMBER'].nunique() if 'INVOICE_NUMBER' in f_sales.columns else 0
    
    if total_invoices > 0:
        avg_sku_per_bill = f_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean()
    else:
        avg_sku_per_bill = 0.0

    sku_agg = f_sales.groupby('Target_Product_Group', observed=True).agg(
        Active_Outlets=('Outlet_Code', 'nunique'),
        Total_Cases=('Sales_Raw Cases', 'sum')
    ).to_dict(orient='index')

    hit_count = 0
    close_count = 0
    far_count = 0
    sku_records = []

    for prod_group, target_pct in target_mapping.items():
        data = sku_agg.get(prod_group, {'Active_Outlets': 0, 'Total_Cases': 0.0})
        buying_outlets = data['Active_Outlets']
        cases_sold = data['Total_Cases']

        actual_pen = (buying_outlets / total_planned_outlets) if total_planned_outlets > 0 else 0.0
        gap_pct = actual_pen - target_pct
        
        if gap_pct >= 0:
            status = "Hit 🎯 😊"
            hit_count += 1
        elif gap_pct >= -0.05:
            status = "Close ⚠️ 😕"
            close_count += 1
        else:
            status = "Far 😡"
            far_count += 1

        sku_records.append({
            "SKU / Group Name": prod_group,
            "Target %": f"{target_pct*100:.0f}%",
            "Actual Outlets": buying_outlets,
            "Actual Pen %": f"{actual_pen*100:.1f}%",
            "Gap %": f"{gap_pct*100:+.1f}%",
            "Total Cases": round(cases_sold, 1),
            "Status": status
        })

    df_sku_rep = pd.DataFrame(sku_records)

    # Top KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    if f_pjp is not None:
        c1.markdown(f'<div class="metric-card"><div class="metric-val">{total_planned_outlets:,}</div><div class="metric-lbl">Planned PJP Outlets <span style="font-size:11px;color:#c9082a;">[{billed_outlets} Billed | {zero_sale_outlets} Zero]</span></div></div>', unsafe_allow_html=True)
    else:
        c1.markdown(f'<div class="metric-card"><div class="metric-val">{billed_outlets:,}</div><div class="metric-lbl">Buying Outlets (Billed)</div></div>', unsafe_allow_html=True)
        
    c2.markdown(f'<div class="metric-card"><div class="metric-val">{avg_sku_per_bill:.2f}</div><div class="metric-lbl">Avg SKU Per Bill</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-val">{hit_count} / {len(target_mapping)}</div><div class="metric-lbl">Target Achieved SKUs 🎯</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-val">{(hit_count / len(target_mapping) * 100):.1f}%</div><div class="metric-lbl">SKU Hit Rate %</div></div>', unsafe_allow_html=True)

    # ------------------ ACCURATE TOP & BOTTOM SDM & DISTRIBUTORS ------------------
    sdm_performance = []
    # Loop across ALL SDMs from Sales
    all_sdms = [s for s in df_sales['SDM/SDO/SDS'].dropna().unique() if str(s).strip() and str(s) != "Unknown SDM"]
    
    for s_name in all_sdms:
        s_sales = df_sales[df_sales['SDM/SDO/SDS'] == s_name]
        if len(s_sales) == 0:
            continue
            
        if df_pjp_master is not None and 'SDM/SDO/SDS' in df_pjp_master.columns and (df_pjp_master['SDM/SDO/SDS'] == s_name).any():
            s_outlets = df_pjp_master[df_pjp_master['SDM/SDO/SDS'] == s_name]['Outlet_Code'].nunique()
        else:
            s_outlets = s_sales['Outlet_Code'].nunique()
            
        if s_outlets == 0:
            continue
            
        s_sku_bill = s_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean() if len(s_sales) > 0 else 0.0
        s_sku_grp = s_sales.groupby('Target_Product_Group', observed=True)['Outlet_Code'].nunique()
        s_hit = sum(1 for sku_k, tgt_v in target_mapping.items() if (s_sku_grp.get(sku_k, 0) / s_outlets) >= tgt_v)
        s_rate = (s_hit / len(target_mapping)) * 100
        sdm_performance.append({
            'Name': s_name, 'Outlets': s_outlets, 'SKU_Bill': s_sku_bill, 'Hit_Count': s_hit, 'Hit_Rate': s_rate
        })
        
    if sdm_performance:
        df_sdm_rank = pd.DataFrame(sdm_performance).sort_values(by=['Hit_Rate', 'SKU_Bill'], ascending=False)
    else:
        df_sdm_rank = pd.DataFrame(columns=['Name', 'Outlets', 'SKU_Bill', 'Hit_Count', 'Hit_Rate'])

    dist_performance = []
    all_dists = [d for d in df_sales['Dist_Name'].dropna().unique() if str(d).strip()]
    
    for d_name in all_dists:
        d_sales = df_sales[df_sales['Dist_Name'] == d_name]
        if len(d_sales) == 0:
            continue
            
        if df_pjp_master is not None:
            d_outlets = df_pjp_master[df_pjp_master['Dist_Name'] == d_name]['Outlet_Code'].nunique()
        else:
            d_outlets = d_sales['Outlet_Code'].nunique()
            
        if d_outlets == 0:
            continue
            
        d_sku_bill = d_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean() if len(d_sales) > 0 else 0.0
        d_sku_grp = d_sales.groupby('Target_Product_Group', observed=True)['Outlet_Code'].nunique()
        d_hit = sum(1 for sku_k, tgt_v in target_mapping.items() if (d_sku_grp.get(sku_k, 0) / d_outlets) >= tgt_v)
        d_rate = (d_hit / len(target_mapping)) * 100
        dist_performance.append({
            'Name': d_name, 'Outlets': d_outlets, 'SKU_Bill': d_sku_bill, 'Hit_Count': d_hit, 'Hit_Rate': d_rate
        })
        
    if dist_performance:
        df_dist_rank = pd.DataFrame(dist_performance).sort_values(by=['Hit_Rate', 'SKU_Bill'], ascending=False)
    else:
        df_dist_rank = pd.DataFrame(columns=['Name', 'Outlets', 'SKU_Bill', 'Hit_Count', 'Hit_Rate'])

    st.write("")
    
    # Leaderboard Section
    if len(df_sdm_rank) > 0 or len(df_dist_rank) > 0:
        l_col1, l_col2, l_col3, l_col4 = st.columns(4)
        
        if len(df_sdm_rank) > 0:
            top_sdm = df_sdm_rank.iloc[0]
            bot_sdm = df_sdm_rank.iloc[-1]
            with l_col1:
                st.markdown(f"""
                <div class="lead-card-top">
                    <div class="lead-title" style="color: #16a34a;">🏆 Top SDM / SDO</div>
                    <div class="lead-name">{top_sdm['Name']}</div>
                    <div class="lead-stats">Hit Rate: <b>{top_sdm['Hit_Rate']:.1f}%</b> ({top_sdm['Hit_Count']}/{len(target_mapping)} SKUs) | SKU/Bill: <b>{top_sdm['SKU_Bill']:.2f}</b></div>
                </div>
                """, unsafe_allow_html=True)
            with l_col2:
                st.markdown(f"""
                <div class="lead-card-bottom">
                    <div class="lead-title" style="color: #dc2626;">🔻 Bottom SDM / SDO</div>
                    <div class="lead-name">{bot_sdm['Name']}</div>
                    <div class="lead-stats">Hit Rate: <b>{bot_sdm['Hit_Rate']:.1f}%</b> ({bot_sdm['Hit_Count']}/{len(target_mapping)} SKUs) | SKU/Bill: <b>{bot_sdm['SKU_Bill']:.2f}</b></div>
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
                    <div class="lead-stats">Hit Rate: <b>{top_dist['Hit_Rate']:.1f}%</b> ({top_dist['Hit_Count']}/{len(target_mapping)} SKUs) | Outlets: <b>{top_dist['Outlets']:,}</b></div>
                </div>
                """, unsafe_allow_html=True)
            with l_col4:
                st.markdown(f"""
                <div class="lead-card-bottom">
                    <div class="lead-title" style="color: #dc2626;">⚠️ Bottom Distributor</div>
                    <div class="lead-name">{bot_dist['Name']}</div>
                    <div class="lead-stats">Hit Rate: <b>{bot_dist['Hit_Rate']:.1f}%</b> ({bot_dist['Hit_Count']}/{len(target_mapping)} SKUs) | Outlets: <b>{bot_dist['Outlets']:,}</b></div>
                </div>
                """, unsafe_allow_html=True)

    st.write("")

    # Modern Navigation Tabs
    tab1, tab_pack, tab2, tab_outlets = st.tabs([
        "🎯 SKU Target & Penetration", 
        "📦 Pack-Wise Penetration",
        "👤 Booker (PSR) Scorecard", 
        "🔍 Outlets Missing SKU & Day Filter"
    ])

    # TAB 1: SKU PENETRATION TABLE
    with tab1:
        st.subheader("Target vs Actual SKU Penetration")
        basis_note = f"Universe Base: **{total_planned_outlets:,} Planned Outlets**" + (f" ({zero_sale_outlets} Zero-Sale Included)" if f_pjp is not None else " (Billed Only)")
        st.caption(f"{basis_note} | Status: **{hit_count} Hit 🎯** | **{close_count} Close ⚠️** | **{far_count} Far 😡**")

        def color_status_rows(row):
            st_val = str(row['Status'])
            if "Hit" in st_val:
                return ['background-color: #d4edda; color: #155724; font-weight: 500;'] * len(row)
            elif "Close" in st_val:
                return ['background-color: #fff3cd; color: #856404; font-weight: 500;'] * len(row)
            else:
                return ['background-color: #f8d7da; color: #721c24; font-weight: 500;'] * len(row)

        styled_sku_df = df_sku_rep.style.apply(color_status_rows, axis=1)
        st.dataframe(styled_sku_df, use_container_width=True, height=520)

    # TAB 2: PACK-WISE PENETRATION
    with tab_pack:
        st.subheader("📦 Overall Pack-Wise Penetration (All Flavours Combined)")
        valid_packs = f_sales[f_sales['PKG_NAME'] != ""]
        if len(valid_packs) > 0:
            pack_agg = valid_packs.groupby('PKG_NAME', observed=True).agg(
                Billed_Outlets=('Outlet_Code', 'nunique'),
                Total_Cases=('Sales_Raw Cases', 'sum'),
                Invoices=('INVOICE_NUMBER', 'nunique')
            ).reset_index()

            pack_agg['Penetration %'] = ((pack_agg['Billed_Outlets'] / total_planned_outlets) * 100).round(1).astype(str) + "%"
            pack_agg['Drop Size (Cases)'] = (pack_agg['Total_Cases'] / pack_agg['Billed_Outlets']).round(2)
            pack_agg = pack_agg.sort_values(by='Billed_Outlets', ascending=False)

            st.dataframe(pack_agg, use_container_width=True, height=500)
        else:
            st.info("Sales file me 'PKG_NAME' data dastiyab nahi hai.")

    # TAB 3: BOOKER SCORECARD
    with tab2:
        st.subheader("👤 Booker / Pre-Seller Scorecard")
        st.caption("Productivity, Route Coverage & Target Hit Rate Rollup")

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

            b_sku_per_bill = b_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean() if len(b_sales) > 0 else 0.0
            
            b_achieved = 0
            b_sku_grp = b_sales.groupby('Target_Product_Group', observed=True)['Outlet_Code'].nunique()
            
            base_count = b_total_outlets if f_pjp is not None else b_billed
            for sku_name, tgt in target_mapping.items():
                if base_count > 0 and (b_sku_grp.get(sku_name, 0) / base_count) >= tgt:
                    b_achieved += 1

            dist = b_meta['Dist_Name'].iloc[0] if 'Dist_Name' in b_meta.columns else ""
            sdm = b_meta['SDM/SDO/SDS'].iloc[0] if 'SDM/SDO/SDS' in b_meta.columns else ""

            booker_rows.append({
                'Distributor': dist,
                'SDM': sdm,
                'Booker Name': b_name,
                'Total Planned Outlets': b_total_outlets if f_pjp is not None else b_billed,
                'Billed Outlets': b_billed,
                'Zero Sale Outlets': max(0, b_total_outlets - b_billed) if f_pjp is not None else 0,
                'SKU Per Bill': round(b_sku_per_bill, 2),
                'Targets Achieved': f"{b_achieved} / {len(target_mapping)}",
                'Hit Rate %': round((b_achieved / len(target_mapping)) * 100, 1),
                'Status': "Star ⭐" if b_achieved >= 10 else ("Good 👍" if b_achieved >= 6 else "Needs Focus ⚠️")
            })

        df_booker_score = pd.DataFrame(booker_rows).sort_values(by='Hit Rate %', ascending=False)
        
        def color_booker(row):
            hr = row['Hit Rate %']
            if hr >= 50.0:
                return ['background-color: #d4edda; color: #155724; font-weight: 500;'] * len(row)
            elif hr >= 30.0:
                return ['background-color: #fff3cd; color: #856404; font-weight: 500;'] * len(row)
            else:
                return ['background-color: #f8d7da; color: #721c24; font-weight: 500;'] * len(row)

        st.dataframe(df_booker_score.style.apply(color_booker, axis=1), use_container_width=True, height=500)

    # TAB 4: OUTLETS MISSING SKU & DAY FILTER
    with tab_outlets:
        st.subheader("🔍 Outlets Missing SKU Gap Analysis & Day-Wise Visit Plan")
        st.caption("PJP Planned days, specific pack purchases, aur zero-sale outlets ko filter karein.")

        all_target_skus = set(target_mapping.keys())
        total_sku_count = len(all_target_skus)

        valid_target_sales = f_sales[f_sales['Target_Product_Group'].isin(all_target_skus)]
        outlet_bought_sets = valid_target_sales.groupby('Outlet_Code', observed=True)['Target_Product_Group'].apply(lambda s: set(s)).to_dict()

        if f_pjp is not None:
            outlet_meta = f_pjp[['Outlet_Code', 'Outlet_Name', 'PJP_Name', 'BOOKER_Name', 'Dist_Name', 'SDM/SDO/SDS', 'Planned_Days'] + DAYS_LIST].copy()
        else:
            outlet_meta = f_sales[['Outlet_Code', 'Outlet_Name', 'PJP_Name', 'BOOKER_Name', 'Dist_Name', 'SDM/SDO/SDS']].drop_duplicates('Outlet_Code').copy()
            outlet_meta['Planned_Days'] = "N/A (Upload PJP)"
            for day in DAYS_LIST:
                outlet_meta[day] = 1

        def get_missing_details(row):
            bought = outlet_bought_sets.get(row['Outlet_Code'], set())
            missing = all_target_skus - bought
            is_zero = len(bought) == 0
            return len(bought), len(missing), ", ".join(sorted(missing)), ("Zero Sale ⚠️" if is_zero else "Billed ✅")

        details = outlet_meta.apply(get_missing_details, axis=1)
        outlet_meta['SKUs_Bought'] = [d[0] for d in details]
        outlet_meta['SKUs_Missing'] = [d[1] for d in details]
        outlet_meta['Missing_Products_List'] = [d[2] for d in details]
        outlet_meta['Billing_Status'] = [d[3] for d in details]

        # Filter Section with Day Filter
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.2, 1.2, 1.2])
        
        with f_col1:
            sku_options = ["All Outlets (Any SKU)"] + sorted(list(target_mapping.keys()))
            selected_pack = st.selectbox("🎯 Filter Bought SKU:", sku_options)

        with f_col2:
            day_options = ["All Days"] + DAYS_LIST
            selected_day = st.selectbox("📅 Planned Day Filter:", day_options)
            
        with f_col3:
            missing_range = st.slider(
                "⚠️ Missing SKUs (0-17):", 
                min_value=0, 
                max_value=total_sku_count, 
                value=(1, total_sku_count), 
                step=1
            )
            
        with f_col4:
            status_filter = st.selectbox("Billing Filter:", ["All Outlets", "Billed Outlets Only", "Zero-Sale Outlets Only"])

        filtered_outlets = outlet_meta[
            (outlet_meta['SKUs_Missing'] >= missing_range[0]) & 
            (outlet_meta['SKUs_Missing'] <= missing_range[1])
        ]

        if selected_day != "All Days" and f_pjp is not None:
            filtered_outlets = filtered_outlets[filtered_outlets[selected_day] == 1]

        if status_filter == "Billed Outlets Only":
            filtered_outlets = filtered_outlets[filtered_outlets['Billing_Status'] == "Billed ✅"]
        elif status_filter == "Zero-Sale Outlets Only":
            filtered_outlets = filtered_outlets[filtered_outlets['Billing_Status'] == "Zero Sale ⚠️"]

        if selected_pack != "All Outlets (Any SKU)":
            pack_buyers = set(valid_target_sales[valid_target_sales['Target_Product_Group'] == selected_pack]['Outlet_Code'].unique())
            filtered_outlets = filtered_outlets[filtered_outlets['Outlet_Code'].isin(pack_buyers)]

        st.markdown(f"**Found {len(filtered_outlets):,} outlets** matching filters (Day: **{selected_day}** | Purchased: **{selected_pack}** | Missing: **{missing_range[0]} to {missing_range[1]} SKUs**).")

        display_cols = ['Outlet_Code', 'Outlet_Name', 'BOOKER_Name', 'PJP_Name', 'SDM/SDO/SDS', 'Planned_Days', 'Billing_Status', 'SKUs_Missing', 'SKUs_Bought', 'Missing_Products_List']
        st.dataframe(
            filtered_outlets[display_cols].sort_values(by='SKUs_Missing', ascending=False), 
            use_container_width=True, 
            height=480
        )

    # Excel Export
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sku_rep.to_excel(writer, sheet_name='SKU Penetration', index=False)
        if len(valid_packs) > 0:
            pack_agg.to_excel(writer, sheet_name='Pack Penetration', index=False)
        df_booker_score.to_excel(writer, sheet_name='Booker Scorecard', index=False)
        filtered_outlets.to_excel(writer, sheet_name='Missing & Zero Outlets', index=False)

    st.download_button(
        label="📥 Download Full Report (Excel)",
        data=output.getvalue(),
        file_name="Pepsi_Penetration_Fast_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👈 Baraye meharbani sidebar se Sales Raw Data aur Target File upload karein.")
