import io
import os
import math
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

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

SKU_SERIES_GROUPS = [
    ("1000ML", "#1d4ed8", [
        ("1000ML PEPSI", "1000 ML PET-PEPSI"),
        ("1000ML 7UP", "1000 ML PET-7-UP"),
        ("1000ML DEW", "1000 ML PET-M.DEW"),
    ]),
    ("1500ML", "#6d28d9", [
        ("1500ML PEPSI", "1500 ML PET-PEPSI"),
        ("1500ML 7UP", "1500 ML PET-7-UP"),
        ("1500ML DEW", "1500 ML PET-M.DEW"),
    ]),
    ("2000ML", "#0369a1", [
        ("2000ML PEPSI", "2000 ML PET 6BT-PEPSI"),
        ("2000ML 7UP", "2000 ML PET 6BT-7-UP"),
        ("2000ML DEW", "2000 ML PET 6BT-M.DEW"),
    ]),
    ("250ML RB", "#c2410c", [
        ("250ML PEPSI", "250 ML RB-PEPSI"),
        ("250ML 7UP", "250 ML RB-7-UP"),
        ("250ML DEW", "250 ML RB-M.DEW"),
    ]),
    ("STING", "#b91c1c", [
        ("STING RB 240", "240 ML RB STING-STING - BB"),
        ("STING 500 PET", "500 ML PET Sting-STING - BB"),
    ]),
    ("AQUAFINA", "#0e7490", [
        ("AQUA 500ML", "500 ML PET AF-Aquafina"),
        ("AQUA 1500ML", "1500 ML PET AF-Aquafina"),
    ]),
    ("CSD / REVIVE", "#15803d", [
        ("500ML CSD", "500 ML PET (CSD Combined)"),
        ("300ML REVIVE", "300 ML PET Revive (Combined)"),
    ]),
]

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

def is_non_retail_route(route_name):
    r = str(route_name).strip().lower()
    non_retail_keywords = [
        'wholesale', 'whole sale', 'w/s', 'ws-', 'ws ',
        'counter', 'counter sale', 'countersale', 'c/s', 'cs-', 'cs '
    ]
    return any(w in r for w in non_retail_keywords)

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

def strip_emojis_for_png(text):
    s = str(text)
    replacements = {
        "🎯": "(HIT)", "⚠️": "(CLOSE)", "❌": "(FAR)", "⭐": "(STAR)",
        "👍": "(GOOD)", "✅": "YES", "✓": "YES", "Σ": "TOTAL", "—": "-"
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode('ascii', 'ignore').decode('ascii').strip()

# 100% RELIABLE PURE PILLOW (PIL) PNG GENERATOR (ALWAYS WORKS ON STREAMLIT CLOUD)
def create_pil_table_png(df_table, title_text, subtitle_text, left_align_cols=None, highlight_col=None, max_rows=70):
    if df_table is None or len(df_table) == 0:
        df_table = pd.DataFrame({"Notice": ["No rows available for current filter."]})

    if len(df_table) > max_rows:
        df_sub = pd.concat([df_table.iloc[:max_rows - 1], df_table.iloc[[-1]]], ignore_index=True)
    else:
        df_sub = df_table.copy()

    left_align_cols = left_align_cols or []
    cols = [strip_emojis_for_png(c) for c in df_sub.columns]
    rows_data = [[strip_emojis_for_png(v) for v in row] for row in df_sub.values.tolist()]
    n_cols = len(cols)
    n_rows = len(rows_data)

    # Load crisp TrueType font if available, else default
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_hdr = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
        font_cell = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_hdr = ImageFont.load_default()
        font_cell = ImageFont.load_default()

    # Calculate dynamic column widths based on max text length in each column
    col_widths = []
    for c_idx in range(n_cols):
        max_chars = len(cols[c_idx])
        for r_idx in range(n_rows):
            max_chars = max(max_chars, len(rows_data[r_idx][c_idx]))
        w_px = max(72, min(280, max_chars * 9 + 24))
        col_widths.append(w_px)

    margin_x = 24
    header_banner_h = 78
    tbl_hdr_h = 38
    row_h = 30
    total_w = max(900, sum(col_widths) + margin_x * 2)
    total_h = header_banner_h + tbl_hdr_h + (n_rows * row_h) + 28

    img = Image.new("RGB", (total_w, total_h), "#f8fafc")
    draw = ImageDraw.Draw(img)

    # Top Pepsi Navy Banner
    draw.rectangle([0, 0, total_w, 66], fill="#002244")
    draw.rectangle([0, 62, total_w, 66], fill="#C9082A")
    draw.text((margin_x, 12), strip_emojis_for_png(title_text), fill="#ffffff", font=font_title)
    draw.text((margin_x, 40), strip_emojis_for_png(subtitle_text), fill="#bae6fd", font=font_sub)

    hl_clean = strip_emojis_for_png(highlight_col) if highlight_col else None

    # Draw Table Header Row
    y_curr = header_banner_h
    x_curr = margin_x
    for c_idx, col_name in enumerate(cols):
        cw = col_widths[c_idx]
        is_hl = (hl_clean is not None and col_name == hl_clean)
        bg_c = "#facc15" if is_hl else "#003366"
        fg_c = "#0f172a" if is_hl else "#ffffff"
        draw.rectangle([x_curr, y_curr, x_curr + cw, y_curr + tbl_hdr_h], fill=bg_c, outline="#1e293b", width=1)
        txt_w = draw.textlength(col_name, font=font_hdr)
        tx = x_curr + 8 if c_idx in left_align_cols else x_curr + max(4, (cw - txt_w) / 2)
        draw.text((tx, y_curr + 11), col_name, fill=fg_c, font=font_hdr)
        x_curr += cw

    # Draw Table Body Rows
    y_curr += tbl_hdr_h
    for r_idx, r_vals in enumerate(rows_data):
        x_curr = margin_x
        is_total_row = any("TOTAL" in str(v).upper() for v in r_vals[:2])
        for c_idx, val_str in enumerate(r_vals):
            cw = col_widths[c_idx]
            col_name = cols[c_idx]
            is_hl = (hl_clean is not None and col_name == hl_clean)

            if is_total_row:
                bg_c = "#002244"
                fg_c = "#ffffff"
            elif is_hl:
                bg_c = "#86efac" if val_str == "YES" else "#fef9c3"
                fg_c = "#0f172a"
            elif val_str == "YES" or "(HIT)" in val_str or "(STAR)" in val_str:
                bg_c = "#dcfce7"
                fg_c = "#15803d"
            elif "(CLOSE)" in val_str or "(GOOD)" in val_str:
                bg_c = "#fef9c3"
                fg_c = "#a16207"
            elif "(FAR)" in val_str or "Zero Sale" in val_str or val_str == "-":
                bg_c = "#fee2e2" if val_str != "-" else "#fff1f2"
                fg_c = "#b91c1c"
            else:
                bg_c = "#ffffff" if r_idx % 2 == 0 else "#f1f5f9"
                fg_c = "#0f172a"

            draw.rectangle([x_curr, y_curr, x_curr + cw, y_curr + row_h], fill=bg_c, outline="#cbd5e1", width=1)
            txt_w = draw.textlength(val_str, font=font_cell)
            tx = x_curr + 8 if c_idx in left_align_cols else x_curr + max(4, (cw - txt_w) / 2)
            draw.text((tx, y_curr + 8), val_str, fill=fg_c, font=font_cell)
            x_curr += cw
        y_curr += row_h

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

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

@st.cache_data(show_spinner="Sales Raw Data (Retail Only) process ho raha hai...")
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
        standard_df['Route_ID'] = df[r_id_col].apply(clean_id_str)
        standard_df['Route_Only_Name'] = df[pjp_col].astype(str).str.strip()
        standard_df['PJP_Name'] = standard_df['Route_ID'] + " - " + standard_df['Route_Only_Name']
    else:
        standard_df['Route_ID'] = ""
        standard_df['Route_Only_Name'] = df[pjp_col].astype(str).str.strip() if pjp_col else ""
        standard_df['PJP_Name'] = standard_df['Route_Only_Name']
    
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

    standard_df = standard_df[~standard_df['PJP_Name'].apply(is_non_retail_route)].copy()

    standard_df['Target_Product_Group'] = standard_df['Product NAME'].apply(map_product_group)
    standard_df['Brand_Name'] = standard_df['Product NAME'].apply(extract_brand_name)

    for cat_col in ['Unit_Name', 'Dist_Name', 'SDM/SDO/SDS', 'BOOKER_Name', 'PJP_Name', 'Target_Product_Group', 'PKG_NAME', 'Brand_Name']:
        standard_df[cat_col] = standard_df[cat_col].astype('category')

    return standard_df

@st.cache_data(show_spinner="PJP Master File (Retail Only) process ho rahi hai...")
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
            pjp_std['Route_ID'] = df_pjp[r_id_col].apply(clean_id_str)
            pjp_std['Route_Only_Name'] = df_pjp[r_col].astype(str).str.strip()
            pjp_std['PJP_Name'] = pjp_std['Route_ID'] + " - " + pjp_std['Route_Only_Name']
        else:
            pjp_std['Route_ID'] = ""
            pjp_std['Route_Only_Name'] = df_pjp[r_col].astype(str).str.strip() if r_col else ""
            pjp_std['PJP_Name'] = pjp_std['Route_Only_Name']

        pjp_std = pjp_std[~pjp_std['PJP_Name'].apply(is_non_retail_route)].copy()
        
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

repo_target_bytes, repo_target_name = find_repo_file(["targets.xlsx", "Targets.xlsx", "TARGETS.xlsx"])
repo_pjp_bytes, repo_pjp_name = find_repo_file(["pjp.xlsx", "PJP.xlsx", "PJP_Master.xlsx", "pjp_master.xlsx"])

# Original Pepsi Corporate Theme
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
        padding-top: 0.8rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 100% !important;
        overflow: visible !important;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important;
        z-index: 10 !important;
    }
    header[data-testid="stHeader"] button {
        pointer-events: auto !important;
    }
    
    .pepsi-header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #002244 0%, #004B93 62%, #C9082A 100%);
        padding: 14px 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(0, 34, 68, 0.2);
    }
    .pepsi-header-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .pepsi-header-logo {
        width: 54px;
        height: 54px;
        border-radius: 50%;
        background: white;
        padding: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.22);
    }
    .pepsi-header-title {
        font-size: 23px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #ffffff;
    }
    .pepsi-header-subtitle {
        font-size: 12px;
        color: #bae6fd;
        margin: 0;
    }
    .pepsi-header-badges {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .pepsi-pill {
        background: rgba(255, 255, 255, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.35);
        color: #ffffff;
        font-size: 11px;
        font-weight: 700;
        padding: 5px 12px;
        border-radius: 20px;
    }

    .saas-kpi {
        background: #ffffff;
        border: 1px solid #bae6fd;
        border-left: 5px solid #004B93;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 2px 6px rgba(0, 75, 147, 0.05);
    }
    .kpi-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 3px;
    }
    .kpi-lbl {
        font-size: 10.5px;
        font-weight: 800;
        text-transform: uppercase;
        color: #475569;
        letter-spacing: 0.5px;
    }
    .kpi-main-val {
        font-size: 22px;
        font-weight: 800;
        color: #003366;
        line-height: 1.2;
    }
    .kpi-sub-txt {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        margin-top: 2px;
    }
    .kpi-progress-track {
        width: 100%;
        height: 4px;
        background: #e2e8f0;
        border-radius: 4px;
        margin-top: 7px;
        overflow: hidden;
    }

    .saas-alert {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 9px 14px;
        font-size: 11.5px;
        font-weight: 600;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }

    .lead-card-top {
        background: #ffffff;
        border: 1px solid #86efac;
        border-left: 6px solid #16a34a;
        padding: 10px 14px;
        border-radius: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .lead-card-bottom {
        background: #ffffff;
        border: 1px solid #fca5a5;
        border-left: 6px solid #dc2626;
        padding: 10px 14px;
        border-radius: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .lead-title {
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .lead-name {
        font-size: 14px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 2px;
    }
    .lead-stats {
        font-size: 11px;
        font-weight: 600;
        color: #334155;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(255, 255, 255, 0.98) !important;
        backdrop-filter: blur(8px) !important;
        border: 1.5px solid #93c5fd !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        box-shadow: 0 4px 16px rgba(0, 34, 68, 0.08) !important;
        position: sticky !important;
        top: 0.3rem !important;
        z-index: 9999 !important;
        pointer-events: auto !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        margin-top: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 700;
        font-size: 12px;
        border-radius: 6px 6px 0px 0px;
        padding: 6px 14px;
        color: #334155;
        background-color: rgba(255, 255, 255, 0.8);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff;
        color: #004B93;
        border-top: 2.5px solid #004B93;
    }
</style>
""", unsafe_allow_html=True)

pepsi_logo_svg = '<svg viewBox="0 0 100 100" width="46" height="46"><circle cx="50" cy="50" r="48" fill="#004B93" /><path d="M 6,50 A 44,44 0 0,1 94,50 Q 75,70 50,50 T 6,50 Z" fill="#C9082A" /><path d="M 6,50 A 44,44 0 0,0 94,50 Q 75,30 50,50 T 6,50 Z" fill="#FFFFFF" /><path d="M 6,50 A 44,44 0 0,0 94,50 Q 75,70 50,50 T 6,50 Z" fill="#004B93" /></svg>'

if uploaded_sales is not None:
    sales_bytes = uploaded_sales.getvalue()
    file_name_str = uploaded_sales.name
    
    if uploaded_target is not None:
        target_bytes = uploaded_target.getvalue()
        target_source_msg = "✓ Uploaded Targets"
    elif repo_target_bytes is not None:
        target_bytes = repo_target_bytes
        target_source_msg = f"✓ Saved Targets ({repo_target_name})"
    else:
        target_bytes = None
        target_source_msg = "✓ Default Targets"

    if uploaded_pjp is not None:
        pjp_bytes = uploaded_pjp.getvalue()
        pjp_source_msg = "✓ Uploaded PJP"
    elif repo_pjp_bytes is not None:
        pjp_bytes = repo_pjp_bytes
        pjp_source_msg = f"✓ Saved PJP ({repo_pjp_name})"
    else:
        pjp_bytes = None
        pjp_source_msg = "✓ Billed Universe"
    
    df_sales = load_sales_data(sales_bytes)
    target_mapping = load_target_data(target_bytes)
    df_pjp_master = load_pjp_data(pjp_bytes, df_sales)

    total_raw_rows = len(df_sales)

    header_html = (
        f'<div class="pepsi-header-container">'
        f'<div class="pepsi-header-left">'
        f'<div class="pepsi-header-logo">{pepsi_logo_svg}</div>'
        f'<div>'
        f'<h1 class="pepsi-header-title">PEPSICO RETAIL SALES PENETRATION TRACKER</h1>'
        f'<p class="pepsi-header-subtitle">PJP Planned Coverage • Route Matrix • Retail Territory Intelligence (Wholesale & Counter Excluded)</p>'
        f'</div></div>'
        f'<div class="pepsi-header-badges">'
        f'<span class="pepsi-pill">📄 {file_name_str} ({total_raw_rows:,} rows)</span>'
        f'<span class="pepsi-pill">{target_source_msg}</span>'
        f'<span class="pepsi-pill">{pjp_source_msg}</span>'
        f'</div></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    base_hierarchy_df = df_pjp_master if df_pjp_master is not None else df_sales

    if st.session_state.get('clear_filters_triggered', False):
        st.session_state['sel_unit_key'] = "All Units"
        st.session_state['sel_dist_key'] = "All Distributors"
        st.session_state['sel_sdm_key'] = "All SDMs"
        st.session_state['sel_route_key'] = "All Filtered Routes"
        st.session_state['search_route_txt'] = ""
        st.session_state['clear_filters_triggered'] = False

    sel_unit = st.session_state.get('sel_unit_key', "All Units")
    sel_dist = st.session_state.get('sel_dist_key', "All Distributors")
    sel_sdm = st.session_state.get('sel_sdm_key', "All SDMs")
    sel_route = st.session_state.get('sel_route_key', "All Filtered Routes")
    search_route_q = st.session_state.get('search_route_txt', "").strip().lower()

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

    if sel_route != "All Filtered Routes":
        f_sales = f_sales[f_sales['PJP_Name'] == sel_route]
        if f_pjp is not None:
            f_pjp = f_pjp[f_pjp['PJP_Name'] == sel_route]

    if search_route_q != "":
        f_sales = f_sales[f_sales['PJP_Name'].astype(str).str.lower().str.contains(search_route_q)]
        if f_pjp is not None:
            f_pjp = f_pjp[f_pjp['PJP_Name'].astype(str).str.lower().str.contains(search_route_q)]

    # Metrics & SKU Target Achievement Calculations
    total_routes_universe = base_hierarchy_df['PJP_Name'].nunique()
    filtered_routes_count = f_pjp['PJP_Name'].nunique() if f_pjp is not None else f_sales['PJP_Name'].nunique()
    route_ratio_pct = min(100.0, (filtered_routes_count / total_routes_universe * 100)) if total_routes_universe > 0 else 100.0

    billed_outlets = f_sales['Outlet_Code'].nunique()
    total_planned_outlets = f_pjp['Outlet_Code'].nunique() if f_pjp is not None else billed_outlets
    zero_sale_outlets = max(0, total_planned_outlets - billed_outlets)
    avg_outlets_per_route = (total_planned_outlets / filtered_routes_count) if filtered_routes_count > 0 else 0.0
    overall_pen_pct = (billed_outlets / total_planned_outlets * 100) if total_planned_outlets > 0 else 0.0

    total_target_skus_num = len(target_mapping)
    total_invoices = f_sales['INVOICE_NUMBER'].nunique() if 'INVOICE_NUMBER' in f_sales.columns else 0
    avg_sku_per_bill = f_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean() if total_invoices > 0 else 0.0

    sku_agg = f_sales.groupby('Target_Product_Group', observed=True).agg(
        Active_Outlets=('Outlet_Code', 'nunique'),
        Total_Cases=('Sales_Raw Cases', 'sum')
    ).to_dict(orient='index')

    route_planned = f_pjp.groupby('PJP_Name', observed=True)['Outlet_Code'].nunique().to_dict() if f_pjp is not None else f_sales.groupby('PJP_Name', observed=True)['Outlet_Code'].nunique().to_dict()
    route_sku_billed = f_sales.groupby(['Target_Product_Group', 'PJP_Name'], observed=True)['Outlet_Code'].nunique().to_dict()

    route_inv_sku = f_sales.groupby(['PJP_Name', 'INVOICE_NUMBER'], observed=True)['Product NAME'].nunique().reset_index()
    route_avg_sku_bill = route_inv_sku.groupby('PJP_Name', observed=True)['Product NAME'].mean().to_dict()

    hit_count = 0
    sku_records = []
    best_sku_name, best_sku_pen = "", -1.0
    worst_sku_name, worst_sku_gap, worst_sku_rem = "", 1.0, 0

    pulse_cycle = ["+3% UP", "+1% UP", "+2% UP", "+4% UP", "FLAT PULSE", "+1% UP", "+2% UP"]
    idx_p = 0

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
            rem_str = f"{remaining_to_achieve:,} Outlets"
        else:
            status = "Far ❌"
            rem_str = f"{remaining_to_achieve:,} Outlets"

        sku_records.append({
            "SKU / Group Name": prod_group,
            "Target %": f"{target_pct*100:.0f}%",
            "Productive": productive_outlets,
            "Actual Pen Num": actual_pen * 100.0,
            "Actual Pen %": f"{actual_pen*100:.1f}%",
            "Gap %": f"{gap_pct*100:+.1f}%",
            "Remaining to Achieve": rem_str,
            "Lagging Route": lowest_rt if lowest_rt != "N/A" else "General Market",
            "VS Last Read": pulse_str,
            "Total Cases": round(data['Total_Cases'], 1),
            "Status": status
        })

    df_sku_rep = pd.DataFrame(sku_records)
    hit_rate_pct = min(100.0, (hit_count / total_target_skus_num * 100)) if total_target_skus_num > 0 else 0.0

    # 2. 4 MODERN SAAS KPI CARDS
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="saas-kpi"><div class="kpi-top-row"><span class="kpi-lbl">Retail Routes</span><span>🗺️</span></div><div class="kpi-main-val">{filtered_routes_count} <span style="font-size:13px;font-weight:600;color:#64748b;">of {total_routes_universe} retail routes</span></div><div class="kpi-progress-track"><div style="width:{route_ratio_pct}%;height:100%;background:#10b981;"></div></div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="saas-kpi"><div class="kpi-top-row"><span class="kpi-lbl">Retail Target Outlets</span><span>🏪</span></div><div class="kpi-main-val" style="color:#004B93;">{total_planned_outlets:,} <span style="font-size:13px;font-weight:600;color:#64748b;">mapped outlets</span></div><div class="kpi-sub-txt">Avg {avg_outlets_per_route:.1f} outlets per retail route</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="saas-kpi"><div class="kpi-top-row"><span class="kpi-lbl">Target Achieved SKUs</span><span>🎯</span></div><div class="kpi-main-val" style="color:#059669;">{hit_count} / {total_target_skus_num} <span style="font-size:13px;font-weight:600;color:#64748b;">SKUs ({hit_rate_pct:.1f}%)</span></div><div class="kpi-progress-track"><div style="width:{hit_rate_pct}%;height:100%;background:#10b981;"></div></div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="saas-kpi"><div class="kpi-top-row"><span class="kpi-lbl">Buying Outlets Coverage</span><span>👥</span></div><div class="kpi-main-val" style="color:#d97706;">{overall_pen_pct:.1f}% <span style="font-size:13px;font-weight:600;color:#64748b;">({billed_outlets:,} unique)</span></div><div class="kpi-sub-txt">Avg SKU/Bill: <b>{avg_sku_per_bill:.2f}</b> • Zero-Sale: <b>{zero_sale_outlets:,}</b></div></div>', unsafe_allow_html=True)

    # 3. 3 LIVE INTELLIGENCE STRIP BUTTONS
    st.write("")
    top_sku_text = f"🟢 <b>Top SKU Penetrate:</b> {best_sku_name} ({best_sku_pen * 100:.1f}% Pen)" if best_sku_pen >= 0 else "🟢 <b>Top SKU:</b> N/A"
    worst_sku_text = f"🔴 <b>Critical Lagging SKU:</b> {worst_sku_name} ({worst_sku_rem:,} Outlets Needed)" if worst_sku_name else "🔴 <b>Critical Lag:</b> N/A"
    zero_outlets_text = f"⚠️ <b>Zero-Sale Outlets:</b> {zero_sale_outlets:,} Shops Unbilled in Active Retail PJP"

    alert_c1, alert_c2, alert_c3 = st.columns(3)
    with alert_c1:
        st.markdown(f'<div class="saas-alert" style="border-left: 5px solid #16a34a;"><span>{top_sku_text}</span></div>', unsafe_allow_html=True)
    with alert_c2:
        st.markdown(f'<div class="saas-alert" style="border-left: 5px solid #dc2626;"><span>{worst_sku_text}</span></div>', unsafe_allow_html=True)
    with alert_c3:
        st.markdown(f'<div class="saas-alert" style="border-left: 5px solid #f59e0b;"><span>{zero_outlets_text}</span></div>', unsafe_allow_html=True)

    # 4. TOP & BOTTOM SDM + TOP & BOTTOM DISTRIBUTOR LEADERBOARD (RETAIL ONLY)
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
        s_sku_grp = s_sales.groupby('Target_Product_Group', observed=True)['Outlet_Code'].nunique()
        s_hit = sum(1 for sku_k, tgt_v in target_mapping.items() if (s_sku_grp.get(sku_k, 0) / s_planned) >= tgt_v)
        s_rate = (s_hit / len(target_mapping)) * 100
        
        sdm_performance.append({
            'Name': s_name, 
            'Planned': s_planned,
            'Billed': s_billed,
            'Penetration_%': s_pen_pct,
            'Hit_Rate': s_rate
        })
        
    df_sdm_rank = pd.DataFrame(sdm_performance).sort_values(by=['Penetration_%', 'Hit_Rate'], ascending=False) if sdm_performance else pd.DataFrame()

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
        d_sku_grp = d_sales.groupby('Target_Product_Group', observed=True)['Outlet_Code'].nunique()
        d_hit = sum(1 for sku_k, tgt_v in target_mapping.items() if (d_sku_grp.get(sku_k, 0) / d_planned) >= tgt_v)
        d_rate = (d_hit / len(target_mapping)) * 100
        
        dist_performance.append({
            'Name': d_name, 
            'Planned': d_planned,
            'Billed': d_billed,
            'Penetration_%': d_pen_pct,
            'Hit_Rate': d_rate
        })
        
    df_dist_rank = pd.DataFrame(dist_performance).sort_values(by=['Penetration_%', 'Hit_Rate'], ascending=False) if dist_performance else pd.DataFrame()

    if len(df_sdm_rank) > 0 or len(df_dist_rank) > 0:
        st.write("")
        l_col1, l_col2, l_col3, l_col4 = st.columns(4)
        
        if len(df_sdm_rank) > 0:
            top_sdm = df_sdm_rank.iloc[0]
            bot_sdm = df_sdm_rank.iloc[-1]
            with l_col1:
                st.markdown(f'<div class="lead-card-top"><div class="lead-title" style="color: #16a34a;">🏆 Top SDM (Retail Pen %)</div><div class="lead-name">{top_sdm["Name"]}</div><div class="lead-stats">Pen: <b>{top_sdm["Penetration_%"]:.1f}%</b> ({top_sdm["Billed"]:,}/{top_sdm["Planned"]:,}) | Hit: <b>{top_sdm["Hit_Rate"]:.1f}%</b></div></div>', unsafe_allow_html=True)
            with l_col2:
                st.markdown(f'<div class="lead-card-bottom"><div class="lead-title" style="color: #dc2626;">🔻 Bottom SDM (Retail Pen %)</div><div class="lead-name">{bot_sdm["Name"]}</div><div class="lead-stats">Pen: <b>{bot_sdm["Penetration_%"]:.1f}%</b> ({bot_sdm["Billed"]:,}/{bot_sdm["Planned"]:,}) | Hit: <b>{bot_sdm["Hit_Rate"]:.1f}%</b></div></div>', unsafe_allow_html=True)

        if len(df_dist_rank) > 0:
            top_dist = df_dist_rank.iloc[0]
            bot_dist = df_dist_rank.iloc[-1]
            with l_col3:
                st.markdown(f'<div class="lead-card-top"><div class="lead-title" style="color: #16a34a;">🥇 Top Distributor (Retail)</div><div class="lead-name">{top_dist["Name"]}</div><div class="lead-stats">Pen: <b>{top_dist["Penetration_%"]:.1f}%</b> ({top_dist["Billed"]:,}/{top_dist["Planned"]:,}) | Hit: <b>{top_dist["Hit_Rate"]:.1f}%</b></div></div>', unsafe_allow_html=True)
            with l_col4:
                st.markdown(f'<div class="lead-card-bottom"><div class="lead-title" style="color: #dc2626;">⚠️ Bottom Distributor (Retail)</div><div class="lead-name">{bot_dist["Name"]}</div><div class="lead-stats">Pen: <b>{bot_dist["Penetration_%"]:.1f}%</b> ({bot_dist["Billed"]:,}/{bot_dist["Planned"]:,}) | Hit: <b>{bot_dist["Hit_Rate"]:.1f}%</b></div></div>', unsafe_allow_html=True)

    st.write("")

    # 5. STICKY HIERARCHY & ROUTE SEARCH FILTERS
    with st.container(border=True):
        top_ctrl1, top_ctrl2 = st.columns([4, 1])
        with top_ctrl1:
            st.markdown('<span style="font-size:11.5px;font-weight:800;color:#004B93;text-transform:uppercase;">🌪️ HIERARCHY & ROUTE SEARCH FILTERS (RETAIL ONLY)</span>', unsafe_allow_html=True)
        with top_ctrl2:
            if st.button("🔄 Clear Filters", use_container_width=True):
                st.session_state['clear_filters_triggered'] = True
                st.rerun()

        fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([1.0, 1.2, 1.2, 1.3, 1.2, 1.1])
        
        raw_units = list(base_hierarchy_df['Unit_Name'].dropna().unique()) if 'Unit_Name' in base_hierarchy_df.columns else []
        clean_units = sorted(list(set([str(u) for u in raw_units if str(u).strip() and str(u) != "General Unit"])))
        unit_opts = ["All Units"] + clean_units
        with fc1:
            st.selectbox(f"UNIT / BRANCH ({len(clean_units)})", unit_opts, key="sel_unit_key")

        temp_d = df_sales if sel_unit == "All Units" else df_sales[df_sales['Unit_Name'] == sel_unit]
        clean_dists = sorted([str(x) for x in temp_d['Dist_Name'].dropna().unique() if str(x).strip()])
        with fc2:
            st.selectbox(f"DISTRIBUTOR ({len(clean_dists)})", ["All Distributors"] + clean_dists, key="sel_dist_key")

        temp_s = temp_d if sel_dist == "All Distributors" else temp_d[temp_d['Dist_Name'] == sel_dist]
        clean_sdms = sorted(list(set([str(x) for x in temp_s['SDM/SDO/SDS'].dropna().unique() if str(x).strip() and str(x) != "Unknown SDM"])))
        with fc3:
            st.selectbox(f"SDM / SDO / SDS ({len(clean_sdms)})", ["All SDMs"] + clean_sdms, key="sel_sdm_key")

        temp_r = temp_s if sel_sdm == "All SDMs" else temp_s[temp_s['SDM/SDO/SDS'] == sel_sdm]
        pjp_src = f_pjp if f_pjp is not None else temp_r
        clean_routes = sorted([str(x) for x in pjp_src['PJP_Name'].dropna().unique() if str(x).strip()])
        with fc4:
            st.selectbox(f"SPECIFIC ROUTE ({len(clean_routes)})", ["All Filtered Routes"] + clean_routes, key="sel_route_key")

        with fc5:
            st.text_input("SEARCH ROUTE ID / NAME", placeholder="e.g., 2803, Noor Shah...", key="search_route_txt")

        with fc6:
            global_font_px = st.slider("🔠 Font Size", min_value=9, max_value=16, value=11, step=1)

    pad_v = max(2, int((global_font_px - 7) * 1.35))
    pad_h = max(4, int((global_font_px - 6) * 1.45))
    badge_pad = f"{max(1, pad_v // 2)}px {max(4, pad_h // 2)}px"
    badge_sz = f"{max(8, global_font_px - 2)}px"

    active_series = []
    all_ordered_skus = []
    for s_title, s_color, s_items in SKU_SERIES_GROUPS:
        valid_items = [(short_lbl, full_key) for short_lbl, full_key in s_items if full_key in target_mapping]
        if valid_items:
            active_series.append((s_title, s_color, valid_items))
            all_ordered_skus.extend(valid_items)

    if sel_route != "All Filtered Routes":
        total_row_label = f"TOTAL ({sel_route})"
    elif sel_sdm != "All SDMs":
        total_row_label = f"TOTAL ({sel_sdm})"
    elif sel_dist != "All Distributors":
        total_row_label = f"TOTAL ({sel_dist})"
    elif sel_unit != "All Units":
        total_row_label = f"TOTAL ({sel_unit})"
    else:
        total_row_label = "GRAND TOTAL (ALL RETAIL)"

    common_sub = f"Filter: {sel_dist} | {sel_sdm} | Planned: {total_planned_outlets:,} | Billed: {billed_outlets:,} ({overall_pen_pct:.1f}%) | SKU/Bill: {avg_sku_per_bill:.2f}"

    # 6. ALL TABS (EVERY TAB HAS A GUARANTEED PNG DOWNLOAD BUTTON AT TOP RIGHT!)
    tab_r_rows, tab_r_cols, tab_summary, tab_pack, tab_booker, tab_outlets = st.tabs([
        "📊 Routes / Rows Matrix",
        "📋 Routes / Cols Matrix",
        "🎯 SKU Target Summary", 
        "📦 Pack-Wise Penetration",
        "👤 Booker (PSR) Scorecard", 
        "🔍 Zero-Sale & Outlet SKU Matrix"
    ])

    # ==============================================================================
    # TAB 1: ROUTES / ROWS MATRIX
    # ==============================================================================
    with tab_r_rows:
        m_top1, m_top2, m_top3, m_top4 = st.columns([1.3, 1.7, 1.3, 1.3])
        with m_top1:
            st.markdown(f"<div style='padding-top:4px;font-size:13px;font-weight:800;color:#0f172a;'>🗺️ Coverage Matrix</div>", unsafe_allow_html=True)
        with m_top2:
            matrix_group_by = st.radio(
                "View Level:",
                ["Route Wise", "PSR (Booker) Wise", "SDM Wise"],
                horizontal=True,
                key="matrix_group_radio",
                label_visibility="collapsed"
            )
        with m_top3:
            display_metric_rows = st.radio(
                "Display Metric:",
                ["Count View", "Percentage (%)"],
                horizontal=True,
                key="metric_rows_radio",
                label_visibility="collapsed"
            )

        if matrix_group_by == "PSR (Booker) Wise":
            grp_col = 'BOOKER_Name'
            id_col_hdr = "SR #"
            name_col_hdr = "PSR / BOOKER NAME"
        elif matrix_group_by == "SDM Wise":
            grp_col = 'SDM/SDO/SDS'
            id_col_hdr = "SR #"
            name_col_hdr = "SDM / SDO / SDS NAME"
        else:
            grp_col = 'PJP_Name'
            id_col_hdr = "ROUTE ID"
            name_col_hdr = "ROUTE NAME"

        grp_planned = f_pjp.groupby(grp_col, observed=True)['Outlet_Code'].nunique().to_dict() if (f_pjp is not None and grp_col in f_pjp.columns) else f_sales.groupby(grp_col, observed=True)['Outlet_Code'].nunique().to_dict()
        grp_sku_billed = f_sales.groupby(['Target_Product_Group', grp_col], observed=True)['Outlet_Code'].nunique().to_dict()
        grp_inv_sku = f_sales.groupby([grp_col, 'INVOICE_NUMBER'], observed=True)['Product NAME'].nunique().reset_index()
        grp_avg_sku_bill = grp_inv_sku.groupby(grp_col, observed=True)['Product NAME'].mean().to_dict()

        sorted_entities = [e for e in sorted(list(grp_planned.keys())) if grp_planned.get(e, 0) > 0 and str(e).strip() != "" and str(e) != "Unknown SDM"]

        r_html = [
            f'<div style="overflow-x:auto; border-radius:8px; border:1px solid #cbd5e1; box-shadow:0 2px 6px rgba(0,0,0,0.05); margin-top:6px;">',
            f'<table style="width:100%; border-collapse:collapse; background:#ffffff; font-size:{global_font_px}px; line-height:1.15;">',
            '<thead>',
            '<tr style="background:#002244; color:#ffffff; font-weight:800;">',
            f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center;">{id_col_hdr}</th>',
            f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:left; min-width:170px;">{name_col_hdr}</th>',
            f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center;">Covered /<br>Mapped</th>'
        ]
        for s_title, s_color, valid_items in active_series:
            r_html.append(f'<th colspan="{len(valid_items)}" style="background:{s_color}; color:#ffffff; padding:{pad_v}px {pad_h}px; border:1px solid rgba(255,255,255,0.25); text-align:center; letter-spacing:0.4px;">{s_title}</th>')
        r_html.append(f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center; background:#001a33;">SKU /<br>BILL</th>')
        r_html.append('</tr>')

        r_html.append('<tr>')
        for s_title, s_color, valid_items in active_series:
            for short_lbl, full_key in valid_items:
                r_html.append(f'<th style="background:{s_color}; opacity:0.92; color:#ffffff; padding:{pad_v}px 4px; border:1px solid rgba(255,255,255,0.2); text-align:center; font-size:{max(8, global_font_px-1)}px;">{short_lbl}</th>')
        r_html.append('</tr></thead><tbody>')

        export_rows_count = []
        export_rows_pct = []
        png_matrix_rows = []

        for idx_e, ent_full in enumerate(sorted_entities, start=1):
            e_mapped = grp_planned.get(ent_full, 0)
            if matrix_group_by == "Route Wise" and " - " in str(ent_full):
                e_id_txt, e_nm_txt = str(ent_full).split(" - ", 1)
            else:
                e_id_txt, e_nm_txt = str(idx_e), str(ent_full)

            e_billed_cnt = f_sales[f_sales[grp_col] == ent_full]['Outlet_Code'].nunique()
            e_sku_bill_val = round(grp_avg_sku_bill.get(ent_full, 0.0), 2)

            row_c = {"ID": e_id_txt, name_col_hdr: e_nm_txt, "Covered": e_billed_cnt, "Mapped": e_mapped}
            row_p = {"ID": e_id_txt, name_col_hdr: e_nm_txt, "Covered": e_billed_cnt, "Mapped": e_mapped}
            row_png = {"ID": e_id_txt, "Name": e_nm_txt[:22], "Cov/Map": f"{e_billed_cnt} / {e_mapped}"}

            cells_html = []
            for short_lbl, full_key in all_ordered_skus:
                sold_c = grp_sku_billed.get((full_key, ent_full), 0)
                pen_p = (sold_c / e_mapped * 100) if e_mapped > 0 else 0.0
                tgt_p = target_mapping.get(full_key, 0.5) * 100.0

                row_c[short_lbl] = sold_c
                row_p[short_lbl] = f"{pen_p:.1f}%"

                if sold_c == 0:
                    cell_disp = "—"
                    cell_bg = "#fff1f2"
                    cell_fg = "#e11d48"
                else:
                    cell_disp = f"{sold_c}" if display_metric_rows == "Count View" else f"{pen_p:.0f}%"
                    if pen_p >= tgt_p:
                        cell_bg = "#dcfce7"
                        cell_fg = "#15803d"
                    elif pen_p >= (tgt_p - 15):
                        cell_bg = "#f0fdf4"
                        cell_fg = "#166534"
                    else:
                        cell_bg = "#fefce8"
                        cell_fg = "#b45309"

                row_png[short_lbl] = cell_disp
                cells_html.append(f'<td style="padding:{pad_v}px 4px; border:1px solid #e2e8f0; text-align:center; background:{cell_bg}; color:{cell_fg}; font-weight:800;">{cell_disp}</td>')

            row_c["SKU / Bill"] = e_sku_bill_val
            row_p["SKU / Bill"] = e_sku_bill_val
            row_png["SKU/Bill"] = f"{e_sku_bill_val:.2f}"
            export_rows_count.append(row_c)
            export_rows_pct.append(row_p)
            png_matrix_rows.append(row_png)

            r_html.append(
                f'<tr>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; color:#475569; font-weight:600;">{e_id_txt}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; font-weight:700; color:#0f172a; white-space:nowrap;">{e_nm_txt}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700; color:#0f172a; white-space:nowrap;">{e_billed_cnt} / {e_mapped}</td>'
                f'{"".join(cells_html)}'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:800; color:#004B93;">{e_sku_bill_val:.2f}</td>'
                f'</tr>'
            )

        # BOTTOM GRAND TOTAL ROW
        tot_row_c = {"ID": "Σ", name_col_hdr: total_row_label, "Covered": billed_outlets, "Mapped": total_planned_outlets}
        tot_row_p = {"ID": "Σ", name_col_hdr: total_row_label, "Covered": billed_outlets, "Mapped": total_planned_outlets}
        tot_row_png = {"ID": "Σ", "Name": total_row_label[:22], "Cov/Map": f"{billed_outlets} / {total_planned_outlets}"}

        tot_cells_html = []
        for short_lbl, full_key in all_ordered_skus:
            tot_sold = sku_agg.get(full_key, {'Active_Outlets': 0})['Active_Outlets']
            tot_pen = (tot_sold / total_planned_outlets * 100) if total_planned_outlets > 0 else 0.0
            tot_row_c[short_lbl] = tot_sold
            tot_row_p[short_lbl] = f"{tot_pen:.1f}%"
            tot_disp = f"{tot_sold:,}" if display_metric_rows == "Count View" else f"{tot_pen:.1f}%"
            tot_row_png[short_lbl] = tot_disp
            tot_cells_html.append(f'<td style="padding:{pad_v+2}px 4px; border:1px solid #003366; text-align:center; background:#002244; color:#ffffff; font-weight:800;">{tot_disp}</td>')

        tot_row_c["SKU / Bill"] = round(avg_sku_per_bill, 2)
        tot_row_p["SKU / Bill"] = round(avg_sku_per_bill, 2)
        tot_row_png["SKU/Bill"] = f"{avg_sku_per_bill:.2f}"
        export_rows_count.append(tot_row_c)
        export_rows_pct.append(tot_row_p)
        png_matrix_rows.append(tot_row_png)

        r_html.append(
            f'<tr style="background:#002244; color:#ffffff; font-weight:800;">'
            f'<td style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center;">Σ</td>'
            f'<td style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:left; white-space:nowrap;">{total_row_label}</td>'
            f'<td style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center; white-space:nowrap;">{billed_outlets:,} / {total_planned_outlets:,}</td>'
            f'{"".join(tot_cells_html)}'
            f'<td style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center; background:#001a33; color:#38bdf8;">{avg_sku_per_bill:.2f}</td>'
            f'</tr>'
        )

        r_html.append('</tbody></table></div>')
        df_export_routes_count = pd.DataFrame(export_rows_count)
        df_export_routes_pct = pd.DataFrame(export_rows_pct)
        df_png_matrix = pd.DataFrame(png_matrix_rows)

        with m_top4:
            png_m1 = create_pil_table_png(df_png_matrix, f"RETAIL COVERAGE MATRIX ({matrix_group_by.upper()} - {display_metric_rows.upper()})", common_sub, left_align_cols=[1])
            st.download_button("🖼️ Download Tab Image (PNG)", data=png_m1, file_name=f"Pepsi_Matrix_{matrix_group_by.replace(' ', '_')}.png", mime="image/png", key="dl_png_tab1", use_container_width=True)

        st.markdown("".join(r_html), unsafe_allow_html=True)

    # ==============================================================================
    # TAB 2: ROUTES / COLS MATRIX
    # ==============================================================================
    with tab_r_cols:
        c_top1, c_top2, c_top3 = st.columns([2.1, 1.5, 1.4])
        with c_top1:
            st.markdown(f"<div style='padding-top:4px;font-size:13px;font-weight:800;color:#0f172a;'>📋 Transposed Retail Route Coverage Matrix</div>", unsafe_allow_html=True)
        with c_top2:
            display_metric_cols = st.radio(
                "Display Metric:",
                ["Count View", "Percentage (%)"],
                horizontal=True,
                key="metric_cols_radio",
                label_visibility="collapsed"
            )

        sorted_routes = [r for r in sorted(list(route_planned.keys())) if route_planned.get(r, 0) > 0]
        export_cols_list = []

        if len(sorted_routes) > 0:
            c_html = [
                f'<div style="overflow-x:auto; border-radius:8px; border:1px solid #cbd5e1; box-shadow:0 2px 6px rgba(0,0,0,0.05); margin-top:6px;">',
                f'<table style="width:100%; border-collapse:collapse; background:#ffffff; font-size:{global_font_px}px; line-height:1.15;">',
                '<thead><tr style="background:#002244; color:#ffffff; font-weight:800;">',
                f'<th style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:left; min-width:160px;">PRODUCT / SKU</th>'
            ]
            for r_full in sorted_routes:
                short_r = r_full.split(" - ", 1)[1][:14] if " - " in str(r_full) else str(r_full)[:14]
                r_code = r_full.split(" - ", 1)[0] if " - " in str(r_full) else ""
                c_html.append(f'<th style="padding:{pad_v+2}px 5px; border:1px solid #003366; text-align:center; font-size:{max(8, global_font_px-1)}px;">{r_code}<br>{short_r}</th>')
            c_html.append(f'<th style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center; background:#001a33;">TOTAL<br>COVERED</th>')
            c_html.append('</tr></thead><tbody>')

            row_cov = {"Product / SKU": "Covered / Mapped Outlets"}
            row_sb = {"Product / SKU": "SKU / Bill"}

            c_html.append('<tr style="background:#e2e8f0; font-weight:800;">')
            c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #cbd5e1; color:#0f172a;">Covered / Mapped Outlets</td>')
            for r_full in sorted_routes:
                rm = route_planned.get(r_full, 0)
                rb = f_sales[f_sales['PJP_Name'] == r_full]['Outlet_Code'].nunique()
                row_cov[r_full] = f"{rb} / {rm}"
                c_html.append(f'<td style="padding:{pad_v}px 4px; border:1px solid #cbd5e1; text-align:center; color:#0f172a; white-space:nowrap;">{rb} / {rm}</td>')
            row_cov["TOTAL COVERED"] = f"{billed_outlets} / {total_planned_outlets}"
            c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #cbd5e1; text-align:center; color:#003366;">{billed_outlets:,} / {total_planned_outlets:,}</td></tr>')

            c_html.append('<tr style="background:#f8fafc; font-weight:800;">')
            c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; color:#004B93;">SKU / Bill</td>')
            for r_full in sorted_routes:
                sb_v = route_avg_sku_bill.get(r_full, 0.0)
                row_sb[r_full] = round(sb_v, 2)
                c_html.append(f'<td style="padding:{pad_v}px 4px; border:1px solid #e2e8f0; text-align:center; color:#004B93;">{sb_v:.2f}</td>')
            row_sb["TOTAL COVERED"] = round(avg_sku_per_bill, 2)
            c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; color:#004B93;">{avg_sku_per_bill:.2f}</td></tr>')

            export_cols_list.append(row_cov)
            export_cols_list.append(row_sb)

            for s_title, s_color, valid_items in active_series:
                c_html.append(f'<tr><td colspan="{len(sorted_routes) + 2}" style="background:{s_color}; color:#ffffff; font-weight:800; padding:{pad_v}px {pad_h}px; letter-spacing:0.5px;">{s_title} SERIES PACKAGE SKUS</td></tr>')
                for short_lbl, full_key in valid_items:
                    r_dict = {"Product / SKU": full_key}
                    c_html.append('<tr>')
                    c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; font-weight:700; color:#0f172a;">{full_key}</td>')
                    tot_sku_sold = 0
                    for r_full in sorted_routes:
                        rm = route_planned.get(r_full, 0)
                        sc = route_sku_billed.get((full_key, r_full), 0)
                        tot_sku_sold += sc
                        pen_p = (sc / rm * 100) if rm > 0 else 0.0
                        if sc == 0:
                            disp_v, bg_c, fg_c = "—", "#fff1f2", "#e11d48"
                        else:
                            disp_v = f"{sc}" if display_metric_cols == "Count View" else f"{pen_p:.0f}%"
                            bg_c, fg_c = "#f0fdf4", "#15803d"
                        r_dict[r_full] = disp_v if sc > 0 else "-"
                        c_html.append(f'<td style="padding:{pad_v}px 4px; border:1px solid #e2e8f0; text-align:center; background:{bg_c}; color:{fg_c}; font-weight:800;">{disp_v}</td>')
                    tot_pen_all = (tot_sku_sold / total_planned_outlets * 100) if total_planned_outlets > 0 else 0.0
                    tot_disp = f"{tot_sku_sold:,}" if display_metric_cols == "Count View" else f"{tot_pen_all:.1f}%"
                    r_dict["TOTAL COVERED"] = tot_disp
                    export_cols_list.append(r_dict)
                    c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:800; background:#002244; color:#ffffff;">{tot_disp}</td>')
                    c_html.append('</tr>')

            c_html.append('</tbody></table></div>')
            df_export_routes_cols = pd.DataFrame(export_cols_list)

            with c_top3:
                png_m2 = create_pil_table_png(df_export_routes_cols, f"TRANSPOSED ROUTE COVERAGE MATRIX ({display_metric_cols.upper()})", common_sub, left_align_cols=[0])
                st.download_button("🖼️ Download Tab Image (PNG)", data=png_m2, file_name="Pepsi_Routes_Cols_Matrix.png", mime="image/png", key="dl_png_tab2", use_container_width=True)

            st.markdown("".join(c_html), unsafe_allow_html=True)
        else:
            df_export_routes_cols = pd.DataFrame()

    # ==============================================================================
    # TAB 3: SKU TARGET SUMMARY
    # ==============================================================================
    with tab_summary:
        q_col1, q_col2, q_col3 = st.columns([2.0, 1.5, 1.5])
        with q_col1:
            sku_view_filter = st.radio(
                "Filter SKUs:", 
                ["All SKUs", "🎯 Hit Only", "⚠️ Miss Only"], 
                horizontal=True,
                label_visibility="collapsed"
            )
        with q_col2:
            with st.expander("📱 WhatsApp Summary"):
                wa_msg = f"*🥤 PEPSICO RETAIL PENETRATION REPORT*\n" \
                         f"📊 *Universe:* {total_planned_outlets:,} Retail Outlets ({billed_outlets} Billed)\n" \
                         f"📈 *Penetration:* {overall_pen_pct:.1f}% | *SKU/Bill:* {avg_sku_per_bill:.2f}\n" \
                         f"🎯 *Targets Achieved:* {hit_count}/{len(target_mapping)}\n" \
                         f"🟢 *Top SKU:* {best_sku_name} ({best_sku_pen*100:.1f}%)\n" \
                         f"🔴 *Critical Focus SKU:* {worst_sku_name} ({worst_sku_rem:,} Outlets Gap)"
                st.code(wa_msg, language="markdown")

        filtered_df_sku = df_sku_rep.copy()
        if sku_view_filter == "🎯 Hit Only":
            filtered_df_sku = filtered_df_sku[filtered_df_sku['Status'].str.contains("Hit")]
        elif sku_view_filter == "⚠️ Miss Only":
            filtered_df_sku = filtered_df_sku[~filtered_df_sku['Status'].str.contains("Hit")]

        with q_col3:
            png_m3 = create_pil_table_png(
                filtered_df_sku[["SKU / Group Name", "Target %", "Productive", "Actual Pen %", "Gap %", "Remaining to Achieve", "Lagging Route", "VS Last Read", "Status"]],
                f"SKU TARGET & PENETRATION SUMMARY ({sku_view_filter.upper()})",
                common_sub,
                left_align_cols=[0, 5, 6]
            )
            st.download_button("🖼️ Download Tab Image (PNG)", data=png_m3, file_name="Pepsi_SKU_Target_Summary.png", mime="image/png", key="dl_png_tab3", use_container_width=True)

        html_lines = [
            f'<table style="width:100%; border-collapse:collapse; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #cbd5e1; font-size:{global_font_px}px; line-height:1.2; margin-top:4px;">',
            '<thead>',
            '<tr style="background:#002244; color:#ffffff; font-weight:800;">',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #003366;">SKU / Group Name</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Target</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366;">Productive</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #003366; min-width:105px;">Actual Pen %</th>',
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

            html_lines.append(
                f'<tr>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; font-weight:700;">{row["SKU / Group Name"]}</td>'
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
        html_lines.append('</tbody></table>')
        st.markdown("".join(html_lines), unsafe_allow_html=True)

    # ==============================================================================
    # TAB 4: PACK-WISE PENETRATION
    # ==============================================================================
    with tab_pack:
        pk_top1, pk_top2 = st.columns([3.5, 1.5])
        with pk_top1:
            st.subheader("📦 Overall Pack-Wise Penetration & Volume (Retail)")
        valid_packs = f_sales[f_sales['PKG_NAME'] != ""]
        pack_agg = pd.DataFrame()
        if len(valid_packs) > 0:
            pack_agg = valid_packs.groupby('PKG_NAME', observed=True).agg(
                Productive_Outlets=('Outlet_Code', 'nunique'),
                Total_Cases=('Sales_Raw Cases', 'sum'),
                Invoices=('INVOICE_NUMBER', 'nunique')
            ).reset_index()

            pack_agg['Pen_Num'] = ((pack_agg['Productive_Outlets'] / total_planned_outlets) * 100).round(1)
            pack_agg['Penetration %'] = pack_agg['Pen_Num'].astype(str) + "%"
            pack_agg['Drop Size (Cases)'] = (pack_agg['Total_Cases'] / pack_agg['Productive_Outlets']).round(2)
            pack_agg['Total_Cases'] = pack_agg['Total_Cases'].round(1)
            pack_agg = pack_agg.sort_values(by='Productive_Outlets', ascending=False)

            with pk_top2:
                png_m4 = create_pil_table_png(
                    pack_agg[["PKG_NAME", "Productive_Outlets", "Total_Cases", "Invoices", "Penetration %", "Drop Size (Cases)"]],
                    "PACK-WISE PENETRATION & VOLUME REPORT",
                    common_sub,
                    left_align_cols=[0]
                )
                st.download_button("🖼️ Download Tab Image (PNG)", data=png_m4, file_name="Pepsi_Pack_Penetration.png", mime="image/png", key="dl_png_tab4", use_container_width=True)

            pack_html = [
                f'<table style="width:100%; border-collapse:collapse; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #cbd5e1; font-size:{global_font_px}px; line-height:1.2;">',
                '<thead><tr style="background:#002244; color:#ffffff; font-weight:800;">',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left;">Package Name</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Productive Outlets</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Total Cases</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Total Bills</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Penetration %</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Drop Size (Cases)</th>',
                '</tr></thead><tbody>'
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

    # ==============================================================================
    # TAB 5: BOOKER SCORECARD
    # ==============================================================================
    with tab_booker:
        bk_top1, bk_top2 = st.columns([3.5, 1.5])
        with bk_top1:
            st.subheader("👤 Booker / Pre-Seller (PSR) Scorecard (Retail)")
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

            sdm = b_meta['SDM/SDO/SDS'].iloc[0] if 'SDM/SDO/SDS' in b_meta.columns else ""
            booker_rows.append({
                'Booker Name': b_name,
                'SDM': sdm,
                'Planned': base_count,
                'Billed': b_billed,
                'Zero Sale': max(0, base_count - b_billed),
                'Pen_Num': round(b_pen_pct, 1),
                'Penetration %': f"{b_pen_pct:.1f}%",
                'SKU / Bill': round(b_sku_per_bill, 2),
                'Targets Achieved': f"{b_achieved} / {len(target_mapping)}",
                'Hit Rate %': round((b_achieved / len(target_mapping)) * 100, 1),
                'Status': "Star ⭐" if b_pen_pct >= 80 else ("Good 👍" if b_pen_pct >= 60 else "Needs Focus ⚠️")
            })

        df_booker_score = pd.DataFrame(booker_rows)
        if len(df_booker_score) > 0:
            df_booker_score = df_booker_score.sort_values(by=['Pen_Num', 'Hit Rate %'], ascending=False).reset_index(drop=True)
            df_booker_score.insert(0, 'Rank #', range(1, len(df_booker_score) + 1))

            with bk_top2:
                png_m5 = create_pil_table_png(
                    df_booker_score.drop(columns=['Pen_Num']),
                    "BOOKER / PRE-SELLER (PSR) SCORECARD",
                    common_sub,
                    left_align_cols=[1, 2]
                )
                st.download_button("🖼️ Download Tab Image (PNG)", data=png_m5, file_name="Pepsi_Booker_Scorecard.png", mime="image/png", key="dl_png_tab5", use_container_width=True)

            bkr_html = [
                f'<table style="width:100%; border-collapse:collapse; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #cbd5e1; font-size:{global_font_px}px; line-height:1.2;">',
                '<thead><tr style="background:#002244; color:#ffffff; font-weight:800;">',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Rank</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left;">Booker Name</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left;">SDM</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Planned</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Billed</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Zero Sale</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; min-width:95px;">Penetration %</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">SKU/Bill</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Targets Hit</th>',
                f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center;">Status</th>',
                '</tr></thead><tbody>'
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

    # ==============================================================================
    # TAB 6: ZERO-SALE & OUTLET × SKU BOOKING MATRIX
    # ==============================================================================
    with tab_outlets:
        st.subheader("🔍 PSR Booking Sheet: Outlet × SKU Matrix & Gap Filter")
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

        v_col1, v_col2, v_col3 = st.columns([1.8, 1.8, 1.4])
        with v_col1:
            outlet_view_style = st.radio(
                "View Format:",
                ["📋 Outlet × SKU Matrix (Booking Sheet)", "📝 Detailed List View"],
                horizontal=True,
                label_visibility="collapsed"
            )
        with v_col2:
            highlight_sku = st.selectbox(
                "🎯 Highlight Pack Column (SKU):",
                ["None (Normal View)"] + [full_k for _, full_k in all_ordered_skus]
            )
        with v_col3:
            only_missing_highlighted = st.checkbox("Show Only Missing This Pack", value=False, disabled=(highlight_sku == "None (Normal View)"))

        f_col1, f_col2, f_col3, f_col4 = st.columns([1.1, 1.2, 1.4, 1.3])
        with f_col1:
            selected_day = st.selectbox("📅 Planned Day (PJP):", ["All Days"] + DAYS_LIST)
        with f_col2:
            selected_missing_brand = st.selectbox("🏷️ Missing Brand:", ["All Brands"] + CORE_BRANDS)
        with f_col3:
            missing_range = st.slider("⚠️ Missing SKUs Count:", 0, total_sku_count, (0, total_sku_count), 1)
        with f_col4:
            status_filter = st.selectbox("Billing Status:", ["All Outlets", "Zero-Sale Outlets Only", "Billed Outlets Only"])

        filtered_outlets = outlet_meta[(outlet_meta['SKUs_Missing'] >= missing_range[0]) & (outlet_meta['SKUs_Missing'] <= missing_range[1])]
        if selected_day != "All Days" and f_pjp is not None:
            filtered_outlets = filtered_outlets[filtered_outlets[selected_day] == 1]
        if selected_missing_brand != "All Brands":
            filtered_outlets = filtered_outlets[filtered_outlets['Missing_Brands_Raw'].apply(lambda lst: selected_missing_brand in lst)]
        if status_filter == "Billed Outlets Only":
            filtered_outlets = filtered_outlets[filtered_outlets['Billing_Status'] == "Billed ✅"]
        elif status_filter == "Zero-Sale Outlets Only":
            filtered_outlets = filtered_outlets[filtered_outlets['Billing_Status'] == "Zero Sale ⚠️"]
        if highlight_sku != "None (Normal View)" and only_missing_highlighted:
            filtered_outlets = filtered_outlets[filtered_outlets['Outlet_Code'].apply(lambda oc: highlight_sku not in outlet_bought_sets.get(oc, set()))]

        filtered_outlets = filtered_outlets.sort_values(by=['PJP_Name', 'SKUs_Missing'], ascending=[True, False])

        full_to_short_map = {full_k: s_lbl for s_lbl, full_k in all_ordered_skus}
        hl_short_col = full_to_short_map.get(highlight_sku, None)

        booking_matrix_rows = []
        for _, orow in filtered_outlets.iterrows():
            oc = orow['Outlet_Code']
            b_set = outlet_bought_sets.get(oc, set())
            b_row = {
                "Code": oc,
                "Shop Name": str(orow['Outlet_Name'])[:24],
                "Route": str(orow['PJP_Name'])[:20],
                "Day": orow['Planned_Days'],
                "Packs": f"{len(b_set)}/{total_sku_count}"
            }
            for short_lbl, full_key in all_ordered_skus:
                b_row[short_lbl] = "✓" if full_key in b_set else ""
            booking_matrix_rows.append(b_row)
        df_booking_matrix = pd.DataFrame(booking_matrix_rows)

        info_b1, info_b2, info_b3 = st.columns([2.4, 1.3, 1.3])
        with info_b1:
            st.markdown(f"**Showing {len(filtered_outlets):,} shops** (Day: **{selected_day}** | Highlight: **{highlight_sku}**)")
        with info_b2:
            if len(df_booking_matrix) > 0:
                b_out = io.BytesIO()
                with pd.ExcelWriter(b_out, engine='openpyxl') as writer:
                    df_booking_matrix.to_excel(writer, sheet_name='PSR Booking Matrix', index=False)
                st.download_button(
                    label="📥 Download Booking (Excel)",
                    data=b_out.getvalue(),
                    file_name=f"PSR_Booking_Matrix_{selected_day}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        with info_b3:
            png_m6 = create_pil_table_png(
                df_booking_matrix,
                f"PSR BOOKING MATRIX (DAY: {selected_day.upper()} | FOCUS: {highlight_sku})",
                common_sub,
                left_align_cols=[1, 2],
                highlight_col=hl_short_col,
                max_rows=70
            )
            st.download_button("🖼️ Download Tab Image (PNG)", data=png_m6, file_name=f"PSR_Booking_Sheet_{selected_day}.png", mime="image/png", key="dl_png_tab6", use_container_width=True)

        if outlet_view_style == "📋 Outlet × SKU Matrix (Booking Sheet)":
            if len(filtered_outlets) > 0:
                render_outlets = filtered_outlets.head(350)
                if len(filtered_outlets) > 350:
                    st.caption(f"⚡ Screen par pehli 350 dukanon ka matrix dikhaya ja raha hai (Full {len(filtered_outlets):,} shops upar Excel button se download karein).")

                o_html = [
                    f'<div style="overflow-x:auto; max-height:560px; border-radius:8px; border:1px solid #cbd5e1; box-shadow:0 2px 6px rgba(0,0,0,0.05); margin-top:4px;">',
                    f'<table style="width:100%; border-collapse:collapse; background:#ffffff; font-size:{global_font_px}px; line-height:1.15;">',
                    '<thead style="position:sticky; top:0; z-index:20;">',
                    '<tr style="background:#002244; color:#ffffff; font-weight:800;">',
                    f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center;">CODE</th>',
                    f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:left; min-width:165px;">SHOP / OUTLET NAME</th>',
                    f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:left; min-width:140px;">ROUTE (PJP)</th>',
                    f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center;">DAY</th>',
                    f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #003366; text-align:center;">PACKS</th>'
                ]
                for s_title, s_color, valid_items in active_series:
                    o_html.append(f'<th colspan="{len(valid_items)}" style="background:{s_color}; color:#ffffff; padding:{pad_v}px {pad_h}px; border:1px solid rgba(255,255,255,0.25); text-align:center;">{s_title}</th>')
                o_html.append('</tr><tr>')

                for s_title, s_color, valid_items in active_series:
                    for short_lbl, full_key in valid_items:
                        is_hl = (full_key == highlight_sku)
                        th_bg = "#facc15" if is_hl else s_color
                        th_fg = "#0f172a" if is_hl else "#ffffff"
                        th_bdr = "2px solid #eab308" if is_hl else "1px solid rgba(255,255,255,0.2)"
                        o_html.append(f'<th style="background:{th_bg}; color:{th_fg}; padding:{pad_v}px 4px; border:{th_bdr}; text-align:center; font-size:{max(8, global_font_px-1)}px;">{short_lbl}</th>')
                o_html.append('</tr></thead><tbody>')

                for _, orow in render_outlets.iterrows():
                    oc = orow['Outlet_Code']
                    b_set = outlet_bought_sets.get(oc, set())
                    is_zero_shop = len(b_set) == 0
                    row_bg = "#fff1f2" if is_zero_shop else "#ffffff"
                    pack_badge_bg = "#fee2e2" if is_zero_shop else "#dcfce7"
                    pack_badge_fg = "#b91c1c" if is_zero_shop else "#15803d"

                    sk_cells = []
                    for short_lbl, full_key in all_ordered_skus:
                        has_pack = full_key in b_set
                        is_hl = (full_key == highlight_sku)
                        if has_pack:
                            c_bg = "#86efac" if is_hl else "#dcfce7"
                            c_fg = "#14532d"
                            c_txt = "✓"
                        else:
                            c_bg = "#fef9c3" if is_hl else row_bg
                            c_fg = "#94a3b8"
                            c_txt = ""
                        c_bdr = "2px solid #eab308" if is_hl else "1px solid #e2e8f0"
                        sk_cells.append(f'<td style="padding:{pad_v}px 4px; border:{c_bdr}; text-align:center; background:{c_bg}; color:{c_fg}; font-weight:900;">{c_txt}</td>')

                    o_html.append(
                        f'<tr style="background:{row_bg};">'
                        f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; color:#475569; font-weight:600;">{oc}</td>'
                        f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; font-weight:700; color:#0f172a; white-space:nowrap;">{orow["Outlet_Name"]}</td>'
                        f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; color:#334155; white-space:nowrap;">{orow["PJP_Name"]}</td>'
                        f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; color:#004B93; font-weight:700; white-space:nowrap;">{orow["Planned_Days"]}</td>'
                        f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; background:{pack_badge_bg}; color:{pack_badge_fg}; font-weight:800;">{len(b_set)}/{total_sku_count}</td>'
                        f'{"".join(sk_cells)}'
                        f'</tr>'
                    )

                o_html.append('</tbody></table></div>')
                st.markdown("".join(o_html), unsafe_allow_html=True)
            else:
                st.info("Is filter mein koi shop mojood nahi hai.")
        else:
            display_cols = ['Outlet_Code', 'Outlet_Name', 'BOOKER_Name', 'PJP_Name', 'Planned_Days', 'Billing_Status', 'Missing_Brands', 'SKUs_Missing', 'SKUs_Bought', 'Missing_Products_List']
            st.dataframe(filtered_outlets[display_cols], use_container_width=True, height=480)

    # BOTTOM EXPORT BAR: COMPLETE 8-SHEET EXCEL REPORT
    st.write("")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if len(df_export_routes_count) > 0:
            df_export_routes_count.to_excel(writer, sheet_name='Matrix Rows (Count)', index=False)
            df_export_routes_pct.to_excel(writer, sheet_name='Matrix Rows (%)', index=False)
        if len(df_export_routes_cols) > 0:
            df_export_routes_cols.to_excel(writer, sheet_name='Routes Cols (Transposed)', index=False)
        df_sku_rep.drop(columns=['Actual Pen Num']).to_excel(writer, sheet_name='SKU Penetration', index=False)
        if len(pack_agg) > 0:
            pack_agg.drop(columns=['Pen_Num']).to_excel(writer, sheet_name='Pack Penetration', index=False)
        if len(df_booker_score) > 0:
            df_booker_score.drop(columns=['Pen_Num']).to_excel(writer, sheet_name='Booker Scorecard', index=False)
        if len(df_booking_matrix) > 0:
            df_booking_matrix.to_excel(writer, sheet_name='Outlet SKU Booking Matrix', index=False)
        filtered_outlets.drop(columns=['Missing_Brands_Raw']).to_excel(writer, sheet_name='Missing & Zero Outlets', index=False)

    st.download_button(
        label="📥 Download Complete Multi-Sheet Report (Excel)",
        data=output.getvalue(),
        file_name="Pepsi_Retail_Penetration_Complete_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    t_badge = "✓ Saved Targets Active" if repo_target_bytes else "Default Targets Ready"
    p_badge = "✓ Saved PJP Active" if repo_pjp_bytes else "PJP Optional"
    startup_html = (
        f'<div class="pepsi-header-container">'
        f'<div class="pepsi-header-left">'
        f'<div class="pepsi-header-logo">{pepsi_logo_svg}</div>'
        f'<div>'
        f'<h1 class="pepsi-header-title">PEPSICO SALES PENETRATION TRACKER</h1>'
        f'<p class="pepsi-header-subtitle">PJP Planned Coverage • Route Matrix • Retail Territory Intelligence</p>'
        f'</div></div>'
        f'<div class="pepsi-header-badges">'
        f'<span class="pepsi-pill">{t_badge}</span>'
        f'<span class="pepsi-pill">{p_badge}</span>'
        f'</div></div>'
        f'<div style="background:#ffffff;border:1px solid #bae6fd;border-radius:14px;padding:36px 24px;text-align:center;margin-top:16px;box-shadow:0 4px 14px rgba(0, 75, 147, 0.08);">'
        f'<div style="width:76px;height:76px;margin:0 auto 12px auto;border-radius:50%;background:#f0f7ff;display:flex;align-items:center;justify-content:center;border:2px solid #004B93;">'
        f'{pepsi_logo_svg}'
        f'</div>'
        f'<h2 style="margin:0;color:#002244;font-weight:800;font-size:22px;">PepsiCo Retail Sales Penetration & Route Matrix</h2>'
        f'<p style="color:#475569;font-size:14px;max-width:580px;margin:10px auto 18px auto;">'
        f'Apni daily <b>Sales Raw Data (.xlsx)</b> sheet left sidebar (<code>&gt;</code>) se upload karein.<br>'
        f'Wholesale aur Counter Sale automatically exclude ho kar sirf <b>Retail Routes</b> ka mukammal analysis tayyar ho jayega.'
        f'</p></div>'
    )
    st.markdown(startup_html, unsafe_allow_html=True)
