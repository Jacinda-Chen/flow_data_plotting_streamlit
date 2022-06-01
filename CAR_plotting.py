# import libraries
from operator import contains
import numpy as np
import pandas as pd
import seaborn as sns
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import re as re
import collections as co
from adjustText import adjust_text

# import streamlit (website browser) and st_aggrid (aesthetic table)
import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

st.markdown("<h1 style = 'text-align: center;'>Plotting Data</h1>", unsafe_allow_html=True)

# upload file
uploaded_file = st.file_uploader("Upload a CSV/Excel file!", type=['.xlsx', '.xls', '.csv'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None)

if uploaded_file is not None:
    # Store uploaded file into df
    df=pd.read_csv(uploaded_file)
    df.fillna("Unknown", inplace = True)

    # write function to extract sample number from sample name
    def find_number(text):
        num = re.findall(r'[0-9]+',text)
        sorted_num = " ".join(num)
        if sorted_num == '':
            return "0"
        return sorted_num.replace(" ", ".")
    
    # Store groups
    groups = ['None']
    grouping = ['None']
    y_groups = []
    # Store groups for categorical labels of groups less than or equal to 10
    for column in df.columns.tolist():
        if str(df.dtypes[column]) == "object":
            groups.append(column)
            if len(set(df[column])) <= 25:
                grouping.append(column)
        else:
            y_groups.append(column)

    # Build Streamlit Ag-Grid
    # Set grid height to 300 (enough for 9 rows)
    grid_height = 300

    #features
    enable_selection=True
    if enable_selection:
        selection_mode = 'multiple'
        
        use_checkbox = True
    df = df.loc[:, df.columns != 'Sorted Samples']
  #Infer basic colDefs from dataframe types
    gb = GridOptionsBuilder.from_dataframe(df)

    enable_sidebar=True
    if enable_sidebar:
        gb.configure_side_bar()

    if enable_selection:
        gb.configure_selection(selection_mode)
        if use_checkbox:
            gb.configure_selection(selection_mode, use_checkbox=True)

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
        figure_size_option_x = st.slider('Figure Size X Option', 5, 15, 10)
        figure_size_option_y = st.slider('Figure Size Y Option', 5, 15, 5)
        if plot_option == "Box":
            x_axis_option = st.selectbox('X-Axis', groups[1:])
        elif plot_option == "Histogram":
            x_axis_option = st.selectbox('X-Axis', y_groups)
        else:
            x_axis_option = st.selectbox('X-Axis', df.columns.tolist())
        if plot_option != "Histogram":
            y_axis_option = st.selectbox('Y-Axis', y_groups)
        number = st.number_input("Insert max y-axis", value = 0)
        if plot_option == "Box":
            palette_option = st.selectbox('Palette Option', ['Set1', 'Set2', 'Set1_r', 'Set2_r', 'Paired', 'Accent'])
        if plot_option != "Histogram" and plot_option != "Box":
            grouping_option = st.selectbox('Grouping Option', grouping)
            palette_option = st.selectbox('Palette Option', ['Set1', 'Set2', 'Set1_r', 'Set2_r', 'Paired', 'Accent'])
        if plot_option != "Histogram" and plot_option != "Bar":
            annotation_option = st.selectbox('Annotation Option', groups[1:])

    # Plotting with seaborn

    if df[x_axis_option].dtypes == 'object':
            is_alpha_number = False
            for i in range(len(df)):
                if df.iloc[i][x_axis_option][:1].isalpha() and df.iloc[i][x_axis_option][-1:].isdigit():
                    is_alpha_number = True
            if is_alpha_number:
                # apply function to the selected column of the dataframe
                df['Sorted X Samples'] = df[x_axis_option].apply(lambda x: find_number(x)).astype(float)
                # sort by the new column
                df.sort_values(by = 'Sorted X Samples', inplace = True, na_position = 'first')
                #print(df['Sorted X Samples'])
            else: 
                df.sort_values(by = x_axis_option, inplace = True, na_position = 'first')
                #print(x_axis_option)

    # Plot scatter plot
    if plot_option == 'Scatter':
        if grouping_option == 'None':
            hue = None
        else:
            hue = grouping_option
        
        fig, ax = plt.subplots()
        ax = sns.scatterplot(ax=ax, data=df, x = x_axis_option, y = y_axis_option, s = 100, hue = hue, palette = palette_option)
        handles, labels = ax.get_legend_handles_labels()

        # Annotate
        adjusttext = []

        def label_point(x, y, val, ax):
            a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
            for i, point in a.iterrows():
                adjusttext.append(ax.text(point['x'], point['y'], str(point['val'])))

        if not selected_df.empty:
            label_point(selected_df[x_axis_option], selected_df[y_axis_option], selected_df[annotation_option], ax)
            adjust_text(adjusttext)

        if grouping_option == "None":
            plt.legend(bbox_to_anchor=(1.02, 1), loc = 'upper left', borderaxespad=0)
        else:
            # sort labels alphabetically, numerically
            is_alpha_number = False
            for i in range(len(df)):
                if df.iloc[i][grouping_option][:1].isalpha() and df.iloc[i][grouping_option][-1:].isdigit():
                    is_alpha_number = True
            labels_idx_0 = labels[0]
            if (type(labels_idx_0) == int) == True | (type(labels_idx_0) == float) == True:
                num_dict_values = {val: idx for idx, val in enumerate(labels)}
                sorted_dict = co.OrderedDict(sorted(num_dict_values.items()))
                order=list(sorted_dict.values())
            elif is_alpha_number:
                num_dict_values = {val: idx for idx, val in enumerate(labels)}
                sorted_key = sorted(num_dict_values.keys(), key=lambda x: float(0 if ("".join([i for i in x if i.isdigit() or i == '.'])) == '' else ("".join([i for i in x if i.isdigit() or i == '.']))))
               # print(sorted_key)
                sorted_dict = {}
                for i in sorted_key:
                    for key, value in num_dict_values.items():
                        if key == i:
                            sorted_dict[key] = value
                order=list(sorted_dict.values())
            else:
                print("THIS RAN")
                num_dict_values = {val: idx for idx, val in enumerate(labels)}
                sorted_dict = co.OrderedDict(sorted(num_dict_values.items()))
                order=list(sorted_dict.values())
            plt.legend(bbox_to_anchor=(1.02, 1), loc = 'upper left', borderaxespad=0, handles = [handles[idx] for idx in order], labels = [labels[idx] for idx in order], title = grouping_option)

        plt.rcParams['figure.figsize'] = (figure_size_option_x, figure_size_option_y)

        # set x and y axis min 
        ymin = df[y_axis_option].min()
        ymax = df[y_axis_option].max()
        yrange = ymax - ymin

        # Rotate xlabels if data type is string
        if df[x_axis_option].dtypes == 'object':
            plt.xticks(rotation = 90)

        # Set x and y limits
        else:
            xmin = df[x_axis_option].min()
            xmax = df[x_axis_option].max()
            xrange = xmax - xmin

            ax.set_xlim([xmin - 0.2*xrange, xmax + 0.2*xrange])

        if number == 0:
            ax.set_ylim([ymin - 0.2*yrange, ymax + 0.2*yrange])
        else: ax.set_ylim([ymin - 0.2*yrange, number])

        st.pyplot(fig)

    # Plot Bar
    elif plot_option == 'Bar':
        if grouping_option == 'None':
            hue = None
        else:
            hue = grouping_option
        fig, ax = plt.subplots()
        ax = sns.barplot(ax=ax, data=df, x = x_axis_option, y = y_axis_option, hue = hue, palette = palette_option, dodge = False)
        handles, labels = ax.get_legend_handles_labels()

        # set x and y axis min 
        ymin = df[y_axis_option].min()
        ymax = df[y_axis_option].max()
        yrange = ymax - ymin

        # Rotate xlabels 
        plt.xticks(rotation = 90)
            
        if number == 0:
            plt.ylim([0, ymax + 0.2*yrange])
        else: plt.ylim(0, number)
        
        if grouping_option == "None":
            plt.legend(bbox_to_anchor=(1.02, 1), loc = 'upper left', borderaxespad=0)
        else:
            is_alpha_number = False
            for i in range(len(df)):
                if df.iloc[i][grouping_option][:1].isalpha() and df.iloc[i][grouping_option][-1:].isdigit():
                    is_alpha_number = True
            labels_idx_0 = labels[0]
            if (type(labels_idx_0) == int) == True | (type(labels_idx_0) == float) == True:
                num_dict_values = {val: idx for idx, val in enumerate(labels)}
                sorted_dict = co.OrderedDict(sorted(num_dict_values.items()))
                order=list(sorted_dict.values())
            elif is_alpha_number:
                num_dict_values = {val: idx for idx, val in enumerate(labels)}
                sorted_key = sorted(num_dict_values.keys(), key=lambda x: float(0 if ("".join([i for i in x if i.isdigit() or i == '.'])) == '' else ("".join([i for i in x if i.isdigit() or i == '.']))))
                sorted_dict = {}
                for i in sorted_key:
                    for key, value in num_dict_values.items():
                        if key == i:
                            sorted_dict[key] = value
                order=list(sorted_dict.values())
            else:
                num_dict_values = {val: idx for idx, val in enumerate(labels)}
                sorted_dict = co.OrderedDict(sorted(num_dict_values.items()))
                order=list(sorted_dict.values())
            plt.legend(bbox_to_anchor=(1.02, 1), loc = 'upper left', borderaxespad=0, handles = [handles[idx] for idx in order], labels = [labels[idx] for idx in order], title = grouping_option)
        plt.rcParams['figure.figsize'] = (figure_size_option_x, figure_size_option_y)

        st.pyplot(fig)

    # Plot Box Plot
    elif plot_option == 'Box':
        fig, ax = plt.subplots()
        sns.boxplot(color = "white", ax=ax, data=df, x = x_axis_option, y = y_axis_option, dodge = False)
        ax2 = sns.swarmplot(ax=ax, data=df, x = x_axis_option, y = y_axis_option, size = 8, linewidth = 2, palette = palette_option)

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

        plt.rcParams['figure.figsize'] = (figure_size_option_x, figure_size_option_y)
        
        # set x and y axis min 
        ymin = df[y_axis_option].min()
        ymax = df[y_axis_option].max()
        yrange = ymax - ymin

        # Rotate xlabels if data type is string
        if df[x_axis_option].dtypes == 'object':
            plt.xticks(rotation = 90)

        # Set x and y limits
        else:
            xmin = df[x_axis_option].min()
            xmax = df[x_axis_option].max()
            xrange = xmax - xmin

            ax.set_xlim([xmin - 0.2*xrange, xmax + 0.2*xrange])
            
        if number == 0:
            ax.set_ylim([ymin - 0.2*yrange, ymax + 0.2*yrange])
        else: ax.set_ylim([ymin - 0.2*yrange, number])
        st.pyplot(fig)

    elif plot_option == "Histogram":
        fig, ax = plt.subplots()
        sns.histplot(ax=ax, data=df, x = x_axis_option)
       
        plt.rcParams['figure.figsize'] = (figure_size_option_x, figure_size_option_y)
        
        # set x and y axis min 
        # Rotate xlabels if data type is string
        if df[x_axis_option].dtypes == 'object':
            plt.xticks(rotation = 90)

        # Set x and y limits
        else:
            xmin = df[x_axis_option].min()
            xmax = df[x_axis_option].max()
            xrange = xmax - xmin

            ax.set_xlim([xmin - 0.1*xrange, xmax + 0.1*xrange])
            
        if number == 0:
            ax.set_ylim([0, None])
        else: ax.set_ylim(0, number)
        st.pyplot(fig)
