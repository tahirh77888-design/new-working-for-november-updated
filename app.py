import io
import os
import math
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="PepsiCo Retail Sales Penetration & Route Matrix",
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

def generate_route_matrix_png(df_matrix, display_mode, title_text, subtitle_text, target_map, ordered_skus):
    try:
        import matplotlib.pyplot as plt
        if len(df_matrix) == 0:
            return None
        df_sub = df_matrix.head(50)
        n_rows = len(df_sub)
        n_cols = len(df_sub.columns)
        
        fig_w = max(17, n_cols * 0.75)
        fig_h = max(4.5, n_rows * 0.35 + 1.8)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.axis('off')
        fig.patch.set_facecolor('#f8fafc')
        
        plt.text(0.01, 0.965, title_text, fontsize=14, fontweight='bold', color='#002244', transform=fig.transFigure)
        plt.text(0.01, 0.935, subtitle_text, fontsize=9.5, color='#475569', transform=fig.transFigure)
        
        cols = list(df_sub.columns)
        table_data = df_sub.values.tolist()
        
        col_widths = []
        for idx, c in enumerate(cols):
            if idx == 0:
                col_widths.append(0.045)
            elif idx == 1:
                col_widths.append(0.14)
            elif idx == 2:
                col_widths.append(0.065)
            elif idx == n_cols - 1:
                col_widths.append(0.05)
            else:
                col_widths.append((1.0 - 0.30) / max(1, (n_cols - 4)))
                
        table = ax.table(
            cellText=table_data,
            colLabels=cols,
            colWidths=col_widths,
            loc='center',
            cellLoc='center',
            bbox=[0.0, 0.0, 1.0, 0.90]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7.5)
        
        short_to_full = {s_lbl: f_key for s_lbl, f_key in ordered_skus}
        
        for (row_idx, col_idx), cell in table.get_celld().items():
            cell.set_edgecolor('#cbd5e1')
            if row_idx == 0:
                cell.set_facecolor('#0b132b')
                cell.set_text_props(color='white', fontweight='bold')
            else:
                if col_idx == 1:
                    cell.get_text().set_ha('left')
                if col_idx in [0, 1, 2, n_cols - 1]:
                    cell.set_facecolor('#ffffff' if row_idx % 2 == 1 else '#f8fafc')
                    if col_idx == n_cols - 1:
                        cell.set_text_props(color='#4338ca', fontweight='bold')
                else:
                    raw_val = str(table_data[row_idx - 1][col_idx])
                    mapped_cnt = float(table_data[row_idx - 1][2].split('/')[1].strip())
                    col_name = cols[col_idx]
                    full_k = short_to_full.get(col_name, "")
                    tgt_p = target_map.get(full_k, 0.5) * 100.0
                    
                    if raw_val == "—":
                        cell.set_facecolor('#fff1f2')
                        cell.set_text_props(color='#e11d48', fontweight='bold')
                    else:
                        num_v = float(raw_val.replace('%', ''))
                        pen_p = num_v if display_mode == "Percentage (%)" else (num_v / mapped_cnt * 100.0 if mapped_cnt > 0 else 0.0)
                        if pen_p >= tgt_p:
                            cell.set_facecolor('#dcfce7')
                            cell.set_text_props(color='#15803d', fontweight='bold')
                        elif pen_p >= (tgt_p - 15):
                            cell.set_facecolor('#f0fdf4')
                            cell.set_text_props(color='#166534', fontweight='bold')
                        else:
                            cell.set_facecolor('#fefce8')
                            cell.set_text_props(color='#b45309', fontweight='bold')
                            
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

    # STRICT RETAIL FILTER: Remove Wholesale and Counter Sale completely
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

        # STRICT RETAIL FILTER: Remove Wholesale and Counter Sale completely from PJP
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

# Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: #f1f5f9;
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
    
    /* Dark Pro App Navbar */
    .pro-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #0b132b;
        padding: 12px 22px;
        border-radius: 12px;
        color: white;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(11, 19, 43, 0.2);
    }
    .nav-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .nav-badge-pro {
        background: #10b981;
        color: #ffffff;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 7px;
        border-radius: 6px;
        letter-spacing: 0.5px;
    }
    .nav-title {
        font-size: 19px;
        font-weight: 800;
        color: #38bdf8;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .nav-sub {
        font-size: 11px;
        color: #94a3b8;
        margin: 0;
    }
    .nav-right {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .pill-parsed {
        background: #1e293b;
        border: 1px solid #334155;
        color: #fbbf24;
        font-size: 11px;
        font-weight: 700;
        padding: 5px 12px;
        border-radius: 20px;
    }
    .pill-sync {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
        font-size: 11px;
        font-weight: 800;
        padding: 5px 12px;
        border-radius: 20px;
    }

    /* SaaS KPI Cards */
    .saas-kpi {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
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
        color: #64748b;
        letter-spacing: 0.5px;
    }
    .kpi-main-val {
        font-size: 23px;
        font-weight: 800;
        color: #0f172a;
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

    /* Sticky Filter & Font Container */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(255, 255, 255, 0.98) !important;
        backdrop-filter: blur(8px) !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08) !important;
        position: sticky !important;
        top: 0.3rem !important;
        z-index: 9999 !important;
        pointer-events: auto !important;
    }

    /* Navigation Tabs */
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

if uploaded_sales is not None:
    sales_bytes = uploaded_sales.getvalue()
    file_name_str = uploaded_sales.name
    
    if uploaded_target is not None:
        target_bytes = uploaded_target.getvalue()
        target_source_msg = "✓ Uploaded Targets Active"
    elif repo_target_bytes is not None:
        target_bytes = repo_target_bytes
        target_source_msg = f"✓ Saved Targets ({repo_target_name})"
    else:
        target_bytes = None
        target_source_msg = "✓ Default Targets Active"

    if uploaded_pjp is not None:
        pjp_bytes = uploaded_pjp.getvalue()
        pjp_source_msg = "✓ Uploaded PJP Active"
    elif repo_pjp_bytes is not None:
        pjp_bytes = repo_pjp_bytes
        pjp_source_msg = f"✓ Saved PJP ({repo_pjp_name})"
    else:
        pjp_bytes = None
        pjp_source_msg = "✓ Billed Universe Mode"
    
    df_sales = load_sales_data(sales_bytes)
    target_mapping = load_target_data(target_bytes)
    df_pjp_master = load_pjp_data(pjp_bytes, df_sales)

    total_raw_rows = len(df_sales)

    # 1. PRO DARK TOP NAVBAR
    st.markdown(f"""
    <div class="pro-navbar">
        <div class="nav-left">
            <div style="background:#004B93;width:38px;height:38px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:13px;color:#fff;border:1px solid #38bdf8;">PEPSI</div>
            <div>
                <div class="nav-title">Retail Active Coverage Penetration Tracker <span class="nav-badge-pro">RETAIL ONLY</span></div>
                <div class="nav-sub">Loaded: {file_name_str} • {target_source_msg} • {pjp_source_msg} (Counter & Wholesale Excluded)</div>
            </div>
        </div>
        <div class="nav-right">
            <div class="pill-parsed">✨ Parsed {total_raw_rows:,} retail rows</div>
            <div class="pill-sync">● RETAIL SYNC</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

    # Metrics Calculations (100% Retail Routes Only)
    total_routes_universe = base_hierarchy_df['PJP_Name'].nunique()
    filtered_routes_count = f_pjp['PJP_Name'].nunique() if f_pjp is not None else f_sales['PJP_Name'].nunique()
    route_ratio_pct = min(100.0, (filtered_routes_count / total_routes_universe * 100)) if total_routes_universe > 0 else 100.0

    billed_outlets = f_sales['Outlet_Code'].nunique()
    total_planned_outlets = f_pjp['Outlet_Code'].nunique() if f_pjp is not None else billed_outlets
    zero_sale_outlets = max(0, total_planned_outlets - billed_outlets)
    avg_outlets_per_route = (total_planned_outlets / filtered_routes_count) if filtered_routes_count > 0 else 0.0
    overall_pen_pct = (billed_outlets / total_planned_outlets * 100) if total_planned_outlets > 0 else 0.0

    total_target_skus_num = len(target_mapping)
    route_sku_counts = f_sales[f_sales['Target_Product_Group'].isin(target_mapping.keys())].groupby('PJP_Name', observed=True)['Target_Product_Group'].nunique()
    avg_sku_dist = route_sku_counts.mean() if len(route_sku_counts) > 0 else 0.0
    sku_dist_bar_pct = min(100.0, (avg_sku_dist / total_target_skus_num * 100)) if total_target_skus_num > 0 else 0.0

    total_invoices = f_sales['INVOICE_NUMBER'].nunique() if 'INVOICE_NUMBER' in f_sales.columns else 0
    avg_sku_per_bill = f_sales.groupby('INVOICE_NUMBER')['Product NAME'].nunique().mean() if total_invoices > 0 else 0.0

    # 2. 4 MODERN SAAS KPI CARDS
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="saas-kpi">
            <div class="kpi-top-row"><span class="kpi-lbl">Retail Routes</span><span>🗺️</span></div>
            <div class="kpi-main-val">{filtered_routes_count} <span style="font-size:13px;font-weight:600;color:#64748b;">of {total_routes_universe} retail routes</span></div>
            <div class="kpi-progress-track"><div style="width:{route_ratio_pct}%;height:100%;background:#10b981;"></div></div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="saas-kpi">
            <div class="kpi-top-row"><span class="kpi-lbl">Retail Target Outlets</span><span>🏪</span></div>
            <div class="kpi-main-val" style="color:#1d4ed8;">{total_planned_outlets:,} <span style="font-size:13px;font-weight:600;color:#64748b;">mapped outlets</span></div>
            <div class="kpi-sub-txt">Avg {avg_outlets_per_route:.1f} outlets per retail route</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="saas-kpi">
            <div class="kpi-top-row"><span class="kpi-lbl">SKU Distribution (Avg)</span><span>📈</span></div>
            <div class="kpi-main-val" style="color:#059669;">{avg_sku_dist:.1f} <span style="font-size:13px;font-weight:600;color:#64748b;">of {total_target_skus_num} SKUs</span></div>
            <div class="kpi-progress-track"><div style="width:{sku_dist_bar_pct}%;height:100%;background:#10b981;"></div></div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="saas-kpi">
            <div class="kpi-top-row"><span class="kpi-lbl">Buying Outlets Coverage</span><span>👥</span></div>
            <div class="kpi-main-val" style="color:#d97706;">{overall_pen_pct:.1f}% <span style="font-size:13px;font-weight:600;color:#64748b;">({billed_outlets:,} unique)</span></div>
            <div class="kpi-sub-txt">Avg SKU/Bill: <b>{avg_sku_per_bill:.2f}</b> • Zero-Sale: <b>{zero_sale_outlets:,}</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 3. STICKY HIERARCHY & ROUTE SEARCH FILTERS
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

    # Pre-calculate Data for All Tabs & Exports
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
            "Total Cases": round(data['Total_Cases'], 1),
            "Status": status
        })

    df_sku_rep = pd.DataFrame(sku_records)

    # Shared Active Series & Matrix DataFrames
    active_series = []
    all_ordered_skus = []
    for s_title, s_color, s_items in SKU_SERIES_GROUPS:
        valid_items = [(short_lbl, full_key) for short_lbl, full_key in s_items if full_key in target_mapping]
        if valid_items:
            active_series.append((s_title, s_color, valid_items))
            all_ordered_skus.extend(valid_items)

    sorted_routes = [r for r in sorted(list(route_planned.keys())) if route_planned.get(r, 0) > 0]

    # Build DataFrames for Routes/Rows (Count), Routes/Rows (%), PNG Matrix, and Routes/Cols
    export_rows_count = []
    export_rows_pct = []
    png_matrix_rows = []
    
    current_metric_mode = st.session_state.get('metric_rows_radio', "Count View")

    for r_full in sorted_routes:
        r_mapped = route_planned.get(r_full, 0)
        if " - " in str(r_full):
            r_id_txt, r_nm_txt = str(r_full).split(" - ", 1)
        else:
            r_id_txt, r_nm_txt = "-", str(r_full)
        r_billed_cnt = f_sales[f_sales['PJP_Name'] == r_full]['Outlet_Code'].nunique()
        r_sku_bill_val = round(route_avg_sku_bill.get(r_full, 0.0), 2)

        row_c = {"Route ID": r_id_txt, "Route Name": r_nm_txt, "Covered": r_billed_cnt, "Mapped": r_mapped}
        row_p = {"Route ID": r_id_txt, "Route Name": r_nm_txt, "Covered": r_billed_cnt, "Mapped": r_mapped}
        row_png = {"ID": r_id_txt, "Route Name": r_nm_txt[:22], "Cov/Map": f"{r_billed_cnt} / {r_mapped}"}
        
        for short_lbl, full_key in all_ordered_skus:
            sc = route_sku_billed.get((full_key, r_full), 0)
            pp = round((sc / r_mapped * 100), 1) if r_mapped > 0 else 0.0
            row_c[short_lbl] = sc
            row_p[short_lbl] = f"{pp:.1f}%"
            if sc == 0:
                row_png[short_lbl] = "—"
            else:
                row_png[short_lbl] = f"{sc}" if current_metric_mode == "Count View" else f"{pp:.0f}%"
                
        row_c["SKU / Bill"] = r_sku_bill_val
        row_p["SKU / Bill"] = r_sku_bill_val
        row_png["SKU/Bill"] = f"{r_sku_bill_val:.2f}"
        
        export_rows_count.append(row_c)
        export_rows_pct.append(row_p)
        png_matrix_rows.append(row_png)

    df_export_routes_count = pd.DataFrame(export_rows_count)
    df_export_routes_pct = pd.DataFrame(export_rows_pct)
    df_png_matrix = pd.DataFrame(png_matrix_rows)

    export_cols_list = []
    if len(sorted_routes) > 0:
        row_cov = {"Product / SKU": "Covered / Mapped Outlets"}
        row_sb = {"Product / SKU": "SKU / Bill"}
        for r_full in sorted_routes:
            rm = route_planned.get(r_full, 0)
            rb = f_sales[f_sales['PJP_Name'] == r_full]['Outlet_Code'].nunique()
            row_cov[r_full] = f"{rb} / {rm}"
            row_sb[r_full] = round(route_avg_sku_bill.get(r_full, 0.0), 2)
        row_cov["TOTAL COVERED"] = f"{billed_outlets} / {total_planned_outlets}"
        row_sb["TOTAL COVERED"] = round(avg_sku_per_bill, 2)
        export_cols_list.append(row_cov)
        export_cols_list.append(row_sb)

        for short_lbl, full_key in all_ordered_skus:
            r_dict = {"Product / SKU": full_key}
            tot_sc = 0
            for r_full in sorted_routes:
                sc = route_sku_billed.get((full_key, r_full), 0)
                tot_sc += sc
                r_dict[r_full] = sc
            r_dict["TOTAL COVERED"] = tot_sc
            export_cols_list.append(r_dict)

    df_export_routes_cols = pd.DataFrame(export_cols_list)

    # 4. ALL TABS
    tab_r_rows, tab_r_cols, tab_summary, tab_pack, tab_booker, tab_outlets = st.tabs([
        "📊 Routes / Rows Matrix",
        "📋 Routes / Cols Matrix",
        "🎯 SKU Target Summary", 
        "📦 Pack-Wise Penetration",
        "👤 Booker (PSR) Scorecard", 
        "🔍 Outlets Missing SKU & Brand"
    ])

    # ==============================================================================
    # TAB 1: ROUTES / ROWS MATRIX
    # ==============================================================================
    with tab_r_rows:
        m_top1, m_top2 = st.columns([2.5, 1.5])
        with m_top1:
            st.markdown(f"<div style='padding-top:4px;font-size:13px;font-weight:800;color:#0f172a;'>🗺️ Retail Coverage Matrix <span style='background:#dcfce7;color:#15803d;padding:2px 8px;border-radius:12px;font-size:11px;'>{filtered_routes_count} active retail routes</span></div>", unsafe_allow_html=True)
        with m_top2:
            display_metric_rows = st.radio(
                "Display Metric:",
                ["Count View", "Percentage (%)"],
                horizontal=True,
                key="metric_rows_radio",
                label_visibility="collapsed"
            )

        r_html = [
            f'<div style="overflow-x:auto; border-radius:8px; border:1px solid #cbd5e1; box-shadow:0 2px 6px rgba(0,0,0,0.05); margin-top:6px;">',
            f'<table style="width:100%; border-collapse:collapse; background:#ffffff; font-size:{global_font_px}px; line-height:1.15;">',
            '<thead>',
            '<tr style="background:#0b132b; color:#ffffff; font-weight:800;">',
            f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #1e293b; text-align:center;">ROUTE ID</th>',
            f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #1e293b; text-align:left; min-width:160px;">ROUTE NAME</th>',
            f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #1e293b; text-align:center;">Covered /<br>Mapped</th>'
        ]
        for s_title, s_color, valid_items in active_series:
            r_html.append(f'<th colspan="{len(valid_items)}" style="background:{s_color}; color:#ffffff; padding:{pad_v}px {pad_h}px; border:1px solid rgba(255,255,255,0.25); text-align:center; letter-spacing:0.4px;">{s_title}</th>')
        r_html.append(f'<th rowspan="2" style="padding:{pad_v+2}px {pad_h}px; border:1px solid #1e293b; text-align:center; background:#0f172a;">SKU /<br>BILL</th>')
        r_html.append('</tr>')

        r_html.append('<tr>')
        for s_title, s_color, valid_items in active_series:
            for short_lbl, full_key in valid_items:
                r_html.append(f'<th style="background:{s_color}; opacity:0.92; color:#ffffff; padding:{pad_v}px 4px; border:1px solid rgba(255,255,255,0.2); text-align:center; font-size:{max(8, global_font_px-1)}px;">{short_lbl}</th>')
        r_html.append('</tr></thead><tbody>')

        for r_full in sorted_routes:
            r_mapped = route_planned.get(r_full, 0)
            if " - " in str(r_full):
                r_id_txt, r_nm_txt = str(r_full).split(" - ", 1)
            else:
                r_id_txt, r_nm_txt = "-", str(r_full)

            r_billed_cnt = f_sales[f_sales['PJP_Name'] == r_full]['Outlet_Code'].nunique()
            r_sku_bill_val = route_avg_sku_bill.get(r_full, 0.0)
            
            cells_html = []
            for short_lbl, full_key in all_ordered_skus:
                sold_c = route_sku_billed.get((full_key, r_full), 0)
                pen_p = (sold_c / r_mapped * 100) if r_mapped > 0 else 0.0
                tgt_p = target_mapping.get(full_key, 0.5) * 100.0

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

                cells_html.append(f'<td style="padding:{pad_v}px 4px; border:1px solid #e2e8f0; text-align:center; background:{cell_bg}; color:{cell_fg}; font-weight:800;">{cell_disp}</td>')

            r_html.append(
                f'<tr>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; color:#475569; font-weight:600;">{r_id_txt}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; font-weight:700; color:#0f172a; white-space:nowrap;">{r_nm_txt}</td>'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:700; color:#0f172a; white-space:nowrap;">{r_billed_cnt} / {r_mapped}</td>'
                f'{"".join(cells_html)}'
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:800; color:#4338ca;">{r_sku_bill_val:.2f}</td>'
                f'</tr>'
            )

        r_html.append('</tbody></table></div>')
        st.markdown("".join(r_html), unsafe_allow_html=True)

    # ==============================================================================
    # TAB 2: ROUTES / COLS MATRIX
    # ==============================================================================
    with tab_r_cols:
        c_top1, c_top2 = st.columns([2.5, 1.5])
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

        if len(sorted_routes) > 0:
            c_html = [
                f'<div style="overflow-x:auto; border-radius:8px; border:1px solid #cbd5e1; box-shadow:0 2px 6px rgba(0,0,0,0.05); margin-top:6px;">',
                f'<table style="width:100%; border-collapse:collapse; background:#ffffff; font-size:{global_font_px}px; line-height:1.15;">',
                '<thead><tr style="background:#0b132b; color:#ffffff; font-weight:800;">',
                f'<th style="padding:{pad_v+2}px {pad_h}px; border:1px solid #1e293b; text-align:left; min-width:160px;">PRODUCT / SKU</th>'
            ]
            for r_full in sorted_routes:
                short_r = r_full.split(" - ", 1)[1][:14] if " - " in str(r_full) else str(r_full)[:14]
                r_code = r_full.split(" - ", 1)[0] if " - " in str(r_full) else ""
                c_html.append(f'<th style="padding:{pad_v+2}px 5px; border:1px solid #1e293b; text-align:center; font-size:{max(8, global_font_px-1)}px;">{r_code}<br>{short_r}</th>')
            c_html.append(f'<th style="padding:{pad_v+2}px {pad_h}px; border:1px solid #1e293b; text-align:center; background:#0f172a;">TOTAL<br>COVERED</th>')
            c_html.append('</tr></thead><tbody>')

            c_html.append('<tr style="background:#e2e8f0; font-weight:800;">')
            c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #cbd5e1; color:#0f172a;">Covered / Mapped Outlets</td>')
            for r_full in sorted_routes:
                rm = route_planned.get(r_full, 0)
                rb = f_sales[f_sales['PJP_Name'] == r_full]['Outlet_Code'].nunique()
                c_html.append(f'<td style="padding:{pad_v}px 4px; border:1px solid #cbd5e1; text-align:center; color:#0f172a; white-space:nowrap;">{rb} / {rm}</td>')
            c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #cbd5e1; text-align:center; color:#003366;">{billed_outlets:,} / {total_planned_outlets:,}</td></tr>')

            c_html.append('<tr style="background:#f8fafc; font-weight:800;">')
            c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; color:#4338ca;">SKU / Bill</td>')
            for r_full in sorted_routes:
                sb_v = route_avg_sku_bill.get(r_full, 0.0)
                c_html.append(f'<td style="padding:{pad_v}px 4px; border:1px solid #e2e8f0; text-align:center; color:#4338ca;">{sb_v:.2f}</td>')
            c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; color:#4338ca;">{avg_sku_per_bill:.2f}</td></tr>')

            for s_title, s_color, valid_items in active_series:
                c_html.append(f'<tr><td colspan="{len(sorted_routes) + 2}" style="background:{s_color}; color:#ffffff; font-weight:800; padding:{pad_v}px {pad_h}px; letter-spacing:0.5px;">{s_title} SERIES PACKAGE SKUS</td></tr>')
                for short_lbl, full_key in valid_items:
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
                        c_html.append(f'<td style="padding:{pad_v}px 4px; border:1px solid #e2e8f0; text-align:center; background:{bg_c}; color:{fg_c}; font-weight:800;">{disp_v}</td>')
                    tot_pen_all = (tot_sku_sold / total_planned_outlets * 100) if total_planned_outlets > 0 else 0.0
                    tot_disp = f"{tot_sku_sold:,}" if display_metric_cols == "Count View" else f"{tot_pen_all:.1f}%"
                    c_html.append(f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; font-weight:800; background:#f1f5f9; color:#0f172a;">{tot_disp}</td>')
                    c_html.append('</tr>')

            c_html.append('</tbody></table></div>')
            st.markdown("".join(c_html), unsafe_allow_html=True)

    # ==============================================================================
    # TAB 3: SKU TARGET SUMMARY
    # ==============================================================================
    with tab_summary:
        q_col1, q_col2 = st.columns([2.5, 1.5])
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

        html_lines = [
            f'<table style="width:100%; border-collapse:collapse; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #cbd5e1; font-size:{global_font_px}px; line-height:1.2;">',
            '<thead>',
            '<tr style="background:#0b132b; color:#ffffff; font-weight:800;">',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #1e293b;">SKU / Group Name</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #1e293b;">Target</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #1e293b;">Productive</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #1e293b; min-width:105px;">Actual Pen %</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #1e293b;">Gap</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #1e293b;">Remaining Outlets</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:left; border:1px solid #1e293b;">Lagging Route (Retail)</th>',
            f'<th style="padding:{pad_v+2}px {pad_h}px; text-align:center; border:1px solid #1e293b;">Status</th>',
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
                f'<td style="padding:{pad_v}px {pad_h}px; border:1px solid #e2e8f0; text-align:center; white-space:nowrap;">{badge_html}</td>'
                f'</tr>'
            )
        html_lines.append('</tbody></table>')
        st.markdown("".join(html_lines), unsafe_allow_html=True)

    # ==============================================================================
    # TAB 4: PACK-WISE PENETRATION
    # ==============================================================================
    with tab_pack:
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
            pack_agg = pack_agg.sort_values(by='Productive_Outlets', ascending=False)

            pack_html = [
                f'<table style="width:100%; border-collapse:collapse; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #cbd5e1; font-size:{global_font_px}px; line-height:1.2;">',
                '<thead><tr style="background:#0b132b; color:#ffffff; font-weight:800;">',
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

            bkr_html = [
                f'<table style="width:100%; border-collapse:collapse; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #cbd5e1; font-size:{global_font_px}px; line-height:1.2;">',
                '<thead><tr style="background:#0b132b; color:#ffffff; font-weight:800;">',
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
    # TAB 6: OUTLETS MISSING SKU & BRAND FILTER
    # ==============================================================================
    with tab_outlets:
        st.subheader("🔍 Retail Outlets Missing SKU & Brand Gap Analysis")
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
            selected_missing_brand = st.selectbox("🏷️ Missing Brand:", ["All Brands"] + CORE_BRANDS)
        with f_col2:
            selected_pack = st.selectbox("🎯 Filter Bought SKU:", ["All Outlets (Any SKU)"] + sorted(list(target_mapping.keys())))
        with f_col3:
            selected_day = st.selectbox("📅 Planned Day:", ["All Days"] + DAYS_LIST)
        with f_col4:
            missing_range = st.slider("⚠️ Missing SKUs:", 0, total_sku_count, (1, total_sku_count), 1)
        with f_col5:
            status_filter = st.selectbox("Billing Status:", ["All Outlets", "Billed Outlets Only", "Zero-Sale Outlets Only"])

        filtered_outlets = outlet_meta[(outlet_meta['SKUs_Missing'] >= missing_range[0]) & (outlet_meta['SKUs_Missing'] <= missing_range[1])]
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

        st.markdown(f"**Found {len(filtered_outlets):,} retail outlets** matching filters.")
        display_cols = ['Outlet_Code', 'Outlet_Name', 'BOOKER_Name', 'PJP_Name', 'Planned_Days', 'Billing_Status', 'Missing_Brands', 'SKUs_Missing', 'SKUs_Bought', 'Missing_Products_List']
        st.dataframe(filtered_outlets[display_cols].sort_values(by='SKUs_Missing', ascending=False), use_container_width=True, height=480)

    # BOTTOM EXPORT BAR: 7-SHEET EXCEL + ROUTE MATRIX PNG + SKU SUMMARY PNG
    st.write("")
    dl_col1, dl_col2, dl_col3, _ = st.columns([1.4, 1.5, 1.5, 1.6])
    with dl_col1:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if len(df_export_routes_count) > 0:
                df_export_routes_count.to_excel(writer, sheet_name='Routes Rows (Count)', index=False)
                df_export_routes_pct.to_excel(writer, sheet_name='Routes Rows (%)', index=False)
            if len(df_export_routes_cols) > 0:
                df_export_routes_cols.to_excel(writer, sheet_name='Routes Cols (Transposed)', index=False)
            df_sku_rep.drop(columns=['Actual Pen Num']).to_excel(writer, sheet_name='SKU Penetration', index=False)
            if len(pack_agg) > 0:
                pack_agg.drop(columns=['Pen_Num']).to_excel(writer, sheet_name='Pack Penetration', index=False)
            if len(df_booker_score) > 0:
                df_booker_score.drop(columns=['Pen_Num']).to_excel(writer, sheet_name='Booker Scorecard', index=False)
            filtered_outlets.drop(columns=['Missing_Brands_Raw']).to_excel(writer, sheet_name='Missing & Zero Outlets', index=False)

        st.download_button(
            label="📥 Download Full Report (Excel)",
            data=output.getvalue(),
            file_name="Pepsi_Retail_Penetration_Complete_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with dl_col2:
        matrix_title = f"RETAIL ROUTE COVERAGE MATRIX ({current_metric_mode.upper()}) | {sel_dist} | {sel_sdm}"
        matrix_sub = f"Active Routes: {filtered_routes_count} | Planned Outlets: {total_planned_outlets:,} | Billed: {billed_outlets:,} ({overall_pen_pct:.1f}%) | Avg SKU/Bill: {avg_sku_per_bill:.2f}"
        matrix_png = generate_route_matrix_png(df_png_matrix, current_metric_mode, matrix_title, matrix_sub, target_mapping, all_ordered_skus)
        if matrix_png is not None:
            st.download_button(
                label="🗺️ Download Route Matrix (PNG)",
                data=matrix_png,
                file_name="Pepsi_Route_Coverage_Matrix.png",
                mime="image/png"
            )
    with dl_col3:
        png_title = f"PEPSICO RETAIL COVERAGE SUMMARY | {sel_dist} | {sel_sdm}"
        png_sub = f"Planned: {total_planned_outlets:,} | Billed: {billed_outlets:,} | Coverage: {overall_pen_pct:.1f}% | SKU/Bill: {avg_sku_per_bill:.2f}"
        png_bytes = generate_table_png(df_sku_rep, png_title, png_sub)
        if png_bytes is not None:
            st.download_button(
                label="🖼️ Download SKU Summary (PNG)",
                data=png_bytes,
                file_name="Pepsi_Retail_Coverage_Summary.png",
                mime="image/png"
            )

else:
    st.info("👈 Baraye meharbani sidebar se Sales Raw Data upload karein. (GitHub mein 'targets.xlsx' aur 'pjp.xlsx' maujood hon to woh automatic load ho jayengi).")
