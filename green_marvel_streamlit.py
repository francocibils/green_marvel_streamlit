import pandas as pd
import streamlit as st

from io import BytesIO
from xlsxwriter import Workbook
from helper_functions import *

st.title('DKS - Green Marvel')
st.header('File upload')
st.markdown('Upload file to obtain orders and revenue for Green Marvel specific codes.')
st.markdown('Relevant codes used in the app are: ')

data = {
    "ID": ["961555", "516058", "775379", "406753", "748898", "872878"],
    "Product": ["Green Marvel 250g", "Green Marvel 250g  2 PZS", "Green Marvel 250g 3 PZS", "Green Marvel 120g", "Green Marvel 120g  2 PZS", "Green Marvel 120g 3 PZS"]
}

codes_df = pd.DataFrame(data)
st.table(codes_df)

raw_mow = st.file_uploader('Upload DKS - MOW file', type = ['xlsx', 'xls', 'csv'])
raw_tkm = st.file_uploader('Upload DKS - TKM file', type = ['xlsx', 'xls', 'csv'])

if raw_mow is not None:
    file_type = get_file_type(raw_mow)
    
    if file_type == 'csv':
        mow_df = pd.read_csv(raw_mow, encoding = 'latin-1')
    elif file_type == 'xlsx' or file_type == 'xls':
        mow_df = pd.read_excel(raw_mow, encoding = 'latin-1')
    
    st.success('DKS - MOW file uploaded successfully.')

if raw_tkm is not None:
    file_type = get_file_type(raw_tkm)
    
    if file_type == 'csv':
        tmk_df = pd.read_csv(raw_tkm, encoding = 'latin-1')
    elif file_type == 'xlsx' or file_type == 'xls':
        tmk_df = pd.read_excel(raw_tkm, encoding = 'latin-1')
    
    st.success('DKS - TKM file uploaded successfully.')

if st.button('Process file'):
    # Concat DKS
    dks = pd.concat([mow_df, tmk_df])
    dks['Orden'] = dks['Orden'].astype(float)
    dks['Fecha'] = pd.to_datetime(dks['Fecha'], errors = 'coerce')

    # Process
    dfs_dict = {}

    for prod in range(1, 11):

        keep_cols = ['Orden', 'Status', 'Channel', 'Fecha', f'Cant{prod}', f'Cod{prod}', f'Prod{prod}', f'Cost{prod}', f'Prec{prod}', f'Desc{prod}', f'Tax{prod}', f'Envio{prod}', f'Tax Envio{prod}']
        temp = dks[keep_cols]
        temp.columns = ['Orden', 'Status', 'Channel', 'Fecha', 'Cant', 'Cod', 'Prod', 'Cost', 'Prec', 'Desc', 'Tax', 'Envio', 'Tax Envio']
        dfs_dict[prod] = temp

    pivot = pd.concat(dfs_dict).reset_index().drop(['level_0', 'level_1'], axis = 1)
    pivot['Code'] = pivot['Cod'].str.replace('-', '').str[-6:]
    pivot = pivot.dropna(subset = ['Cod'])

    # Keep codes
    codes = ['961555', '516058', '775379', '406753', '748898', '872878']

    filtered_df = pivot[pivot['Code'].isin(codes)]
    filtered_df['Total'] = filtered_df['Prec'] - filtered_df['Desc']

    # Get orders, items quantity and revenue
    output_df = filtered_df.groupby(['Fecha']).agg(
        orders = ('Orden', 'nunique'),
        items = ('Code', 'count'),
        revenue = ('Total', 'sum')
    ).reset_index()

    st.header('Processed data')

    if output_df.shape[0] == 0:
        st.warning('There were no products found with these codes.')
    else:
        st.success('DKS files have been processed successfully.')

        output = BytesIO()
        with pd.ExcelWriter(output, engine = 'xlsxwriter') as writer:
            output_df.to_excel(writer, index = False, sheet_name = 'Green Marvel - Sales')
            writer.close()

        # Rewind the buffer
        output.seek(0)

        # Create a download button
        st.download_button(
            label = "Download Excel file",
            data = output,
            file_name = "DKS - Green Marvel.xlsx",
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
