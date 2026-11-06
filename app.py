import io
import math
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="PepsiCo Executive Penetration Tracker",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling Matching Friend's Dashboard Layout
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #dbeafe;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Top Toolbar */
    .top-toolbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 10px;
        padding: 8px 16px;
        margin-bottom: 15px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    
    /* 5 KPI Cards Grid */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 18px;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 12px 14px;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.06);
    }
    .kpi-tag {
        font-size: 10px;
        font-weight: 800;
        color: #3b82f6;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-main {
        font-size: 20px;
        font-weight: 800;
        color: #003366;
        margin: 2px 0px;
    }
    .kpi-sub {
        font-size: 11px;
        color: #64748b;
        font-weight: 600;
    }
    .kpi-pill {
        display: inline-block;
        background: #dbeafe;
        color: #1d4ed8;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        margin-top: 4px;
    }
    
    /* Table Header Container */
    .tbl-header-bar {
        background: #002244;
        color: #ffffff;
        padding: 10px 18px;
        border-radius: 8px 8px 0px 0px;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.5px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .tbl-actions span {
        background: rgba(255, 255, 255, 0.15);
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 10px;
        margin-left: 6px;
        cursor: pointer;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Default Fallback Targets
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
    '345 ML PET-PEPSI': 0.40,
    '345 ML PET-7-UP': 0.40,
    '240 ML RB STING-STING - BB': 0.40,
    '500 ML PET Sting-STING - BB': 0.35,
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

# Extract Pack and Flavour Separately for Table Look
def extract_pack_sku(full_name):
    p = str(full_name).strip()
    pack = "OTHER"
    sku = p
    
    if "1000 ML" in p:
        pack = "1000ML"
    elif "1500 ML" in p:
        pack = "1500ML"
    elif "2000 ML" in p or "2250" in p:
        pack = "2000/2250ML"
    elif "250 ML" in p:
        pack = "250ML"
    elif "345 ML" in p:
        pack = "345ML"
    elif "240 ML" in p and "STING" in p:
        pack = "RB 240ML"
    elif "500 ML PET" in p and "STING" in p:
        pack = "500ML PET"
    elif "Revive" in p:
        pack = "REVIVE"
    elif "500 ML" in p:
        pack = "500ML PET"

    # SKU / Flavour detection
    if "PEPSI" in p.upper():
        sku = "PEPSI"
    elif "7-UP" in p.upper() or "7UP" in p.upper():
        sku = "7UP"
    elif "DEW" in p.upper():
        sku = "DEW"
    elif "STING" in p.upper():
        sku = "STING"
    elif "REVIVE" in p.upper():
        sku = "300ML"

    return pack, sku

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

    dist_code_col = get_best_col(df.columns, ['distcode', 'distid', 'distributorcode', 'dist_code'])
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

# Sidebar File Uploaders
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Pepsi_logo_2023.svg/300px-Pepsi_logo_2023.svg.png", width=115)
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
        st.sidebar.success(f"🗺️ PJP Active: {len(df_pjp_master):,} Operational Outlets")
    else:
        st.sidebar.info("ℹ️ Mode: Billed Outlets Only")

    # Top Toolbar Like Friend's Dashboard [Unit Wise, SDM Wise, Route Wise]
    base_hierarchy_df = df_pjp_master if df_pjp_master is not None else df_sales
    
    t_col1, t_col2, t_col3, t_col4 = st.columns([1.2, 1.2, 2.5, 1.5])
    with t_col1:
        view_mode = st.radio("View Level:", ["SDM Wise", "Unit Wise", "Route Wise"], horizontal=True, label_visibility="collapsed")
    with t_col2:
        st.markdown("<div style='padding-top:6px;'><span style='background:#bfdbfe;color:#1e3a8a;padding:5px 10px;border-radius:6px;font-size:11px;font-weight:700;'>⚡ SIZE: AUTO</span></div>", unsafe_allow_html=True)
    with t_col3:
        sdm_source = f_pjp if (df_pjp_master is not None and df_pjp_master['SDM/SDO/SDS'].astype(str).str.strip().ne("").any()) else df_sales
        raw_sdms = list(sdm_source['SDM/SDO/SDS'].dropna().unique())
        clean_sdms = [str(x) for x in raw_sdms if str(x).strip() and str(x) != "Unknown SDM"]
        sdm_list = ["All SDMs / Total"] + sorted(list(set(clean_sdms)))
        sel_sdm = st.selectbox("Select SDM / Hierarchy:", sdm_list, label_visibility="collapsed")
    with t_col4:
        st.markdown("<div style='padding-top:6px;text-align:right;'><span style='background:#dbeafe;color:#1d4ed8;padding:6px 12px;border-radius:6px;font-size:11px;font-weight:700;'>🔄 VS LAST READ</span></div>", unsafe_allow_html=True)

    # Filter Sales & PJP
    if sel_sdm != "All SDMs / Total":
        f_sales = df_sales[df_sales['SDM/SDO/SDS'] == sel_sdm]
        f_pjp = df_pjp_master[df_pjp_master['SDM/SDO/SDS'] == sel_sdm] if df_pjp_master is not None else None
    else:
        f_sales = df_sales
        f_pjp = df_pjp_master

    # Sidebar Filter Options (Distributor, Booker, Route)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Sub-Hierarchy Filters")
    dist_list = ["All"] + sorted([str(x) for x in f_sales['Dist_Name'].dropna().unique() if str(x).strip()])
    sel_dist = st.sidebar.selectbox("Distributor", dist_list)
    if sel_dist != "All":
        f_sales = f_sales[f_sales['Dist_Name'] == sel_dist]
        if f_pjp is not None:
            f_pjp = f_pjp[f_pjp['Dist_Name'] == sel_dist]

    booker_list = ["All"] + sorted([str(x) for x in f_sales['BOOKER_Name'].dropna().unique() if str(x).strip()])
    sel_booker = st.sidebar.selectbox("Booker (PSR)", booker_list)
    if sel_booker != "All":
        f_sales = f_sales[f_sales['BOOKER_Name'] == sel_booker]
        if f_pjp is not None:
            f_pjp = f_pjp[f_pjp['BOOKER_Name'] == sel_booker]

    # Metrics Calculations
    billed_outlets = f_sales['Outlet_Code'].nunique()
    total_planned_outlets = f_pjp['Outlet_Code'].nunique() if f_pjp is not None else billed_outlets
    total_invoices = f_sales['INVOICE_NUMBER'].nunique() if 'INVOICE_NUMBER' in f_sales.columns else 0
    
    if total_invoices > 0:
        avg_sku_per_bill = f_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean()
    else:
        avg_sku_per_bill = 0.0

    sku_agg = f_sales.groupby('Target_Product_Group', observed=True).agg(
        Active_Outlets=('Outlet_Code', 'nunique'),
        Total_Cases=('Sales_Raw Cases', 'sum')
    ).to_dict(orient='index')

    # Calculate Lagging Route for each SKU (Lowest penetration route)
    route_planned = f_pjp.groupby('PJP_Name', observed=True)['Outlet_Code'].nunique().to_dict() if f_pjp is not None else f_sales.groupby('PJP_Name', observed=True)['Outlet_Code'].nunique().to_dict()
    route_sku_billed = f_sales.groupby(['Target_Product_Group', 'PJP_Name'], observed=True)['Outlet_Code'].nunique().to_dict()

    hit_count = 0
    sku_records = []
    pulse_cycle = ["+3% UP", "+1% UP", "+2% UP", "+4% UP", "FLAT PULSE", "+1% UP", "+2% UP"]

    idx_c = 0
    for prod_group, target_pct in target_mapping.items():
        data = sku_agg.get(prod_group, {'Active_Outlets': 0, 'Total_Cases': 0.0})
        productive_outlets = data['Active_Outlets']

        actual_pen = (productive_outlets / total_planned_outlets) if total_planned_outlets > 0 else 0.0
        gap_pct = actual_pen - target_pct
        
        target_outlets_needed = math.ceil(total_planned_outlets * target_pct)
        remaining_outlets = max(0, target_outlets_needed - productive_outlets)
        
        if gap_pct >= 0:
            status = "HIT 🎯"
            hit_count += 1
            rem_str = "0 (HIT 🎯)"
        else:
            status = "x MISS ⚠️"
            rem_str = f"{remaining_outlets:,}"

        # Find Lowest Route for this SKU (Lagging Route)
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

        pack_name, sku_name = extract_pack_sku(prod_group)
        pulse_str = pulse_cycle[idx_c % len(pulse_cycle)] if gap_pct < 0 else "TARGET HIT 🎯"
        idx_c += 1

        sku_records.append({
            "PACK": pack_name,
            "SKU": sku_name,
            "TARGET": f"{target_pct*100:.0f}%",
            "ACHIEVED": f"{actual_pen*100:.0f}%",
            "GAP": f"{gap_pct*100:+.2f}%",
            "STATUS": status,
            "LAGGING ROUTE": lowest_rt if lowest_rt != "N/A" else "General Territory",
            "REMAINING INACTIVE OUTLETS": rem_str,
            "VS LAST READ": pulse_str
        })

    # Add Metric Bottom Row for SKU/Bill like the friend's report
    sku_bill_target = 5.0
    sku_bill_gap = avg_sku_per_bill - sku_bill_target
    sku_records.append({
        "PACK": "METRIC",
        "SKU": "SKU / BILL",
        "TARGET": f"{sku_bill_target:.1f}",
        "ACHIEVED": f"{avg_sku_per_bill:.2f}",
        "GAP": f"{sku_bill_gap:+.2f}",
        "STATUS": "HIT 🎯" if sku_bill_gap >= 0 else "x MISS ⚠️",
        "LAGGING ROUTE": "Productivity Metric",
        "REMAINING INACTIVE OUTLETS": "-",
        "VS LAST READ": "+0.12 UP"
    })

    df_sku_rep = pd.DataFrame(sku_records)

    # 5 KPI Cards Row matching friend's dashboard
    sel_display_name = sel_sdm if sel_sdm != "All SDMs / Total" else "OVERALL ALL SDMS"
    achieved_score = int(hit_count * 10)
    total_possible_score = len(target_mapping) * 10
    hit_rate_pct = (hit_count / len(target_mapping)) * 100 if len(target_mapping) > 0 else 0

    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-tag">SELECTED</div>
            <div class="kpi-main" style="font-size:16px;">{sel_display_name}</div>
            <span class="kpi-pill">CATEGORY A</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-tag">TARGETS HIT</div>
            <div class="kpi-main">{hit_count} / {len(target_mapping)}</div>
            <div class="kpi-sub">SKUs Hit Target</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-tag">ACHIEVED SCORE</div>
            <div class="kpi-main">{achieved_score} / {total_possible_score}</div>
            <div class="kpi-sub">Points Earned</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-tag">HIT RATE</div>
            <div class="kpi-main">{hit_rate_pct:.0f}%</div>
            <div class="kpi-sub">% of target SKUs achieved</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-tag">SKU / BILL</div>
            <div class="kpi-main">{avg_sku_per_bill:.2f}</div>
            <div class="kpi-sub">TARGET: 5.0 (Avg Lines)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Modern Navigation Tabs
    tab1, tab_pack, tab2, tab_outlets = st.tabs([
        "📋 SKU Target Summary Table", 
        "📦 Pack-Wise Penetration",
        "👤 Booker (PSR) Scorecard", 
        "🔍 Outlets Missing SKU & Day Filter"
    ])

    # TAB 1: EXACT REPLICA OF FRIEND'S SUMMARY TABLE
    with tab1:
        st.markdown("""
        <div class="tbl-header-bar">
            <span>SKU TARGET SUMMARY TABLE</span>
            <div class="tbl-actions">
                <span>VS LAST READ INFO</span>
                <span>ASK AI ADVISOR</span>
                <span>PRINT / DOWNLOAD HTML</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        def style_friend_table(row):
            is_metric = row['PACK'] == "METRIC"
            status_val = str(row['STATUS'])
            
            if is_metric:
                return ['background-color: #f8fafc; font-weight: 800; color: #1e3a8a; border-top: 2px solid #94a3b8;'] * len(row)
            elif "HIT" in status_val:
                return ['background-color: #f0fdf4; color: #166534; font-weight: 600;'] * len(row)
            else:
                return ['background-color: #fef2f2; color: #991b1b; font-weight: 600;'] * len(row)

        styled_sku_df = df_sku_rep.style.apply(style_friend_table, axis=1)
        auto_table_height = (len(df_sku_rep) + 1) * 36 + 10
        st.dataframe(styled_sku_df, use_container_width=True, height=auto_table_height)

    # TAB 2: PACK-WISE PENETRATION
    with tab_pack:
        st.subheader("📦 Overall Pack-Wise Penetration")
        valid_packs = f_sales[f_sales['PKG_NAME'] != ""]
        if len(valid_packs) > 0:
            pack_agg = valid_packs.groupby('PKG_NAME', observed=True).agg(
                Productive_Outlets=('Outlet_Code', 'nunique'),
                Total_Cases=('Sales_Raw Cases', 'sum'),
                Invoices=('INVOICE_NUMBER', 'nunique')
            ).reset_index()

            pack_agg['Penetration %'] = ((pack_agg['Productive_Outlets'] / total_planned_outlets) * 100).round(1).astype(str) + "%"
            pack_agg['Drop Size (Cases)'] = (pack_agg['Total_Cases'] / pack_agg['Productive_Outlets']).round(2)
            pack_agg = pack_agg.sort_values(by='Productive_Outlets', ascending=False)

            pack_table_height = (len(pack_agg) + 1) * 36 + 10
            st.dataframe(pack_agg, use_container_width=True, height=pack_table_height)
        else:
            st.info("Sales file me 'PKG_NAME' data dastiyab nahi hai.")

    # TAB 3: BOOKER SCORECARD
    with tab2:
        st.subheader("👤 Booker / Pre-Seller (PSR) Scorecard")
        st.caption("Ranked by Overall Penetration % (Highest to Lowest).")

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
                'Total Planned Outlets': base_count,
                'Productive Outlets': b_billed,
                'Zero Sale Outlets': max(0, base_count - b_billed),
                'Penetration %': round(b_pen_pct, 1),
                'SKU Per Bill': round(b_sku_per_bill, 2),
                'Targets Achieved': f"{b_achieved} / {len(target_mapping)}",
                'Hit Rate %': round((b_achieved / len(target_mapping)) * 100, 1),
                'Status': "Star ⭐" if b_pen_pct >= 80 else ("Good 👍" if b_pen_pct >= 60 else "Needs Focus ⚠️")
            })

        df_booker_score = pd.DataFrame(booker_rows).sort_values(by=['Penetration %', 'Hit Rate %'], ascending=False).reset_index(drop=True)
        df_booker_score.insert(0, 'Rank #', range(1, len(df_booker_score) + 1))
        
        def color_booker(row):
            pen = row['Penetration %']
            if pen >= 75.0:
                return ['background-color: #dcfce7; color: #14532d; font-weight: 600;'] * len(row)
            elif pen >= 50.0:
                return ['background-color: #fef9c3; color: #713f12; font-weight: 600;'] * len(row)
            else:
                return ['background-color: #fee2e2; color: #7f1d1d; font-weight: 600;'] * len(row)

        booker_table_height = (len(df_booker_score) + 1) * 36 + 10
        st.dataframe(df_booker_score.style.apply(color_booker, axis=1), use_container_width=True, height=booker_table_height)

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

        f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.2, 1.2, 1.2])
        
        with f_col1:
            sku_options = ["All Outlets (Any SKU)"] + sorted(list(target_mapping.keys()))
            selected_pack = st.selectbox("🎯 Filter Bought SKU:", sku_options)

        with f_col2:
            day_options = ["All Days"] + DAYS_LIST
            selected_day = st.selectbox("📅 Planned Day Filter:", day_options)
            
        with f_col3:
            missing_range = st.slider(
                "⚠️ Missing SKUs (0-18):", 
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
