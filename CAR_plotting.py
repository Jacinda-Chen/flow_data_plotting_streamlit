# import libraries
import numpy as np
import pandas as pd
import seaborn as sns
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
from adjustText import adjust_text

# import streamlit (website browser) and st_aggrid (aesthetic table)
import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

st.markdown("<h1 style = 'text-align: center;'>Plotting CAR Screen Data</h1>", unsafe_allow_html=True)

# upload file
uploaded_file = st.file_uploader("Upload a CSV/Excel file!", type=['.xlsx', '.xls', '.csv'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None)

if uploaded_file is not None:
    # Store uploaded file into df
    df=pd.read_csv(uploaded_file)

    # Store groups
    groups = ['None']
    y_groups = []
    # Store groups for categorical labels of groups less than or equal to 10
    for column in df.columns.tolist():
        if str(df.dtypes[column]) == "object":
            if len(set(df[column])) <= 10:
                groups.append(column)
        else:
            y_groups.append(column)

    # Build Streamlit Ag-Grid
    # Set grid height to 300 (enough for 9 rows)
    grid_height = 300

    #features
    enable_selection=True
    if enable_selection:
        st.sidebar.subheader("Plotting Options")
        selection_mode = st.sidebar.radio("Selection Mode", ['single','multiple'], index=1)
        
        use_checkbox = True

        if ((selection_mode == 'multiple') & (not use_checkbox)):
            rowMultiSelectWithClick = st.sidebar.checkbox("Multiselect with click (instead of holding CTRL)", value=False)
            if not rowMultiSelectWithClick:
                suppressRowDeselection = st.sidebar.checkbox("Suppress deselection (while holding CTRL)", value=False)
            else:
                suppressRowDeselection=False
        st.sidebar.text("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    
 
  #Infer basic colDefs from dataframe types
    gb = GridOptionsBuilder.from_dataframe(df)

    enable_sidebar=True
    if enable_sidebar:
        gb.configure_side_bar()

    if enable_selection:
        gb.configure_selection(selection_mode)
        if use_checkbox:
            gb.configure_selection(selection_mode, use_checkbox=True)
        if ((selection_mode == 'multiple') & (not use_checkbox)):
            gb.configure_selection(selection_mode, use_checkbox=False, rowMultiSelectWithClick=rowMultiSelectWithClick, suppressRowDeselection=suppressRowDeselection)

    gb.configure_grid_options(domLayout='normal')
    gb.configure_column(df.columns.tolist()[0], headerCheckboxSelection = True)
    gridOptions = gb.build()
    
    #Display the grid
    st.header("Streamlit Ag-Grid")

    grid_response = AgGrid(
        df, 
        gridOptions=gridOptions,
        height=grid_height, 
        width='100%',
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True #Set it to True to allow jsfunction to be injected
        )

    df = grid_response['data']
    selected = grid_response['selected_rows']
    selected_df = pd.DataFrame(selected)

    # Create sidebar options for axes and grouping 
    with st.sidebar:
        plot_option = st.selectbox('Plot Option', ['Scatter', 'Bar', 'Box', 'Histogram'])
        figure_size_option = st.slider('Figure Size Option', 5, 15, 5)
        if plot_option == "Box":
            x_axis_option = st.selectbox('X-Axis', groups[1:])
        elif plot_option == "Histogram":
            x_axis_option = st.selectbox('X-Axis', y_groups)
        else:
            x_axis_option = st.selectbox('X-Axis', df.columns.tolist())
        if plot_option != "Histogram":
            y_axis_option = st.selectbox('Y-Axis', y_groups)
        if plot_option == "Box":
            palette_option = st.selectbox('Palette Option', ['Set1', 'Set2', 'Set1_r', 'Set2_r', 'Paired', 'Accent'])
        if plot_option != "Histogram" and plot_option != "Box":
            grouping_option = st.selectbox('Grouping Option', groups)
            palette_option = st.selectbox('Palette Option', ['Set1', 'Set2', 'Set1_r', 'Set2_r', 'Paired', 'Accent'])
        if plot_option != "Histogram" and plot_option != "Bar":
            annotation_option = st.selectbox('Annotation Option', groups[1:])
        number = st.number_input("Insert max y-axis", value = 0)

    # Plotting with seaborn

    # Plot scatter plot
    if plot_option == 'Scatter':
        if grouping_option == 'None':
            hue = None
        else:
            hue = grouping_option
        fig, ax = plt.subplots()
        sns.scatterplot(ax=ax, data=df, x = x_axis_option, y = y_axis_option, hue = hue, palette = palette_option)
        
        # Annotate
        adjusttext = []

        def label_point(x, y, val, ax):
            a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
            for i, point in a.iterrows():
                adjusttext.append(ax.text(point['x'], point['y'], str(point['val'])))

        if not selected_df.empty:
            label_point(selected_df[x_axis_option], selected_df[y_axis_option], selected_df[annotation_option], ax)
            adjust_text(adjusttext)

        plt.legend(bbox_to_anchor=(1.02, 1), loc = 'upper left', borderaxespad=0)
        plt.rcParams['figure.figsize'] = (figure_size_option, figure_size_option)
        plt.ylim(0, None)
        plt.xlim(0, None)
        # Rotate x tick labels by 90 degrees
        plt.xticks(rotation=90)
        st.pyplot(fig)

    # Plot Bar
    elif plot_option == 'Bar':
        if grouping_option == 'None':
            hue = None
        else:
            hue = grouping_option
        fig, ax = plt.subplots()
        ax = sns.barplot(ax=ax, data=df, x = x_axis_option, y = y_axis_option, hue = hue, palette = palette_option, dodge = False)
        ax.set_xticklabels(ax.get_xticklabels(),rotation = 90)
        plt.legend(bbox_to_anchor=(1.02, 1), loc = 'upper left', borderaxespad=0)
        plt.rcParams['figure.figsize'] = (figure_size_option, figure_size_option)
        plt.ylim(0, None)
        st.pyplot(fig)

    # Plot Box Plot
    elif plot_option == 'Box':
        fig, ax = plt.subplots()
        sns.boxplot(color = "white", ax=ax, data=df, x = x_axis_option, y = y_axis_option, dodge = False)
        ax2 = sns.swarmplot(ax=ax, data=df, x = x_axis_option, y = y_axis_option, linewidth = 2, palette = palette_option)

        tick_labels = ax.get_xticklabels()
        tick_dict = {}
        for i in tick_labels:
                tick_dict[i.get_text()] = i.get_position()[0]

        # Annotate data points
        anno_ls = []
        selected = grid_response['selected_rows']
        selected_df = pd.DataFrame(selected)
        for k, v in selected_df.iterrows():
                if v[x_axis_option] != 'nan':
                        anno = ax.text(x = tick_dict[v[x_axis_option]], y = v[y_axis_option],
                                        s = v[annotation_option], size = 10)
                        anno_ls.append(anno)
                
        adjust_text(anno_ls, ax = ax)

        plt.rcParams['figure.figsize'] = (figure_size_option, figure_size_option)
        plt.xticks(rotation=90)
        st.pyplot(fig)

    elif plot_option == "Histogram":
        fig, ax = plt.subplots()
        sns.histplot(ax=ax, data=df, x = x_axis_option)
        ax.set_xlim(0, None)
        plt.rcParams['figure.figsize'] = (figure_size_option, figure_size_option)
        plt.xticks(rotation=90)
        st.pyplot(fig)
