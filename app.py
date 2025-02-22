from collections import defaultdict
import streamlit as st
import pandas as pd

from rebarcalc import *


st.set_page_config(
    page_title="QCKRebar",
    page_icon=":material/function:"
)


if "cut_schedule" not in st.session_state:
    st.session_state.cut_schedule = defaultdict(int)


def clear_cache():
    """Helper function to clear cut schedule."""

    st.session_state.cut_schedule.clear()


st.title("QCKRebar")
header_container = st.container(border=True)
header_container.write("Web application for optimized estimation of steel reinforcing bars.")


# Input cut length and its quantity
st.subheader("Input")
cin_col1, cin_col2 = st.columns(2)

cin_col1.markdown("**Insert cut length**")
input_cut_length = cin_col1.number_input(
    "Cut length (m or ft)", 
    min_value=0.0, 
    format="%.3f", 
    step=0.01, 
    value=0.01
)
input_qty_cut_length = cin_col1.number_input("Quantity of cut length", min_value=0,)
add_cut_schedule = cin_col1.button("**Add Schedule**", use_container_width=True)
clear_cut_schedule = cin_col1.button("**Clear Schedule**", on_click=clear_cache, use_container_width=True)
start_estimate = cin_col1.button(
    "**Get Estimate**", 
    key="start_calc",
    use_container_width=True
)

# Section for length and unit system options
length_options = {
    "Use default lengths": "mode1",
    "Select from default lengths": "mode2",
}
select_length_settings = cin_col2.radio(
    "**Length Options**", 
    tuple(length_options.keys()),
    key="option_length",
)

unit_system_options = {
    "Metric (m)": "metric",
    "English (ft)": "english"
}
select_unit_system = cin_col2.radio(
    "**Unit System**",
    tuple(unit_system_options.keys()),
    key="option_unit_system",
    horizontal=True
)

length_option_mode = length_options[select_length_settings]
unit_system_mode = unit_system_options[select_unit_system]

match unit_system_mode:
    case "metric":
        ref_clengths = clengths_metric
        disp_unit = "(m)"
    case "english":
        ref_clengths = clengths_english
        disp_unit = "(ft)"

match length_option_mode:
    case "mode1":
        wclengths = ref_clengths
    case "mode2":
        wclengths = cin_col2.multiselect("Select from default length", ref_clengths)

disp_wclengths = pd.Series(wclengths, name=f"Length {disp_unit}")
with cin_col2.expander("Show stock lengths"):
    st.dataframe(disp_wclengths, use_container_width=True)

# Process and display cut schedule from input
st.subheader("Cutting List")
if add_cut_schedule and input_cut_length > 0 and input_qty_cut_length > 0:
    st.session_state.cut_schedule[round(input_cut_length, 3)] += input_qty_cut_length

if st.session_state.cut_schedule:
    wcut_schedule = st.session_state.cut_schedule.items()
    disp_cut_schedule = pd.DataFrame(wcut_schedule, columns=["cut_length", "quantity"])
    st.dataframe(disp_cut_schedule, use_container_width=True)
else:
    st.markdown("`Cutting list is empty`")
    st.table()


# Return and display result
st.subheader("Output")

st.markdown("**Estimate Result**")
disp_result = st.container()
disp_excess = st.expander("**Show Unused Excess**")

st.markdown("**Cutting Process Log**")
disp_log = st.container()

columns_estimate = ["rebar_length", "quantity"]
columns_excess = ["excess_length", "quantity"]
columns_log = ["produced_length",
                   "produced_qty",
                   "produced_type",
                   "from_length",
                   "from_length_type"]

if st.session_state.cut_schedule and wclengths and start_estimate:
    result = get_estimate(cut_schedule=wcut_schedule, wclengths=wclengths)
    
    # Display estimate result
    disp_estimate_result = pd.DataFrame(sorted(result[0].items()), columns=columns_estimate)
    with disp_result:
        st.dataframe(disp_estimate_result, use_container_width=True)

    # Display unused excess lengths from estimate
    disp_excess_inventory = pd.DataFrame(result[1].items(), columns=columns_excess)
    with disp_excess:
        st.dataframe(disp_excess_inventory, use_container_width=True)

    # Display cutting process log
    disp_cut_record = pd.DataFrame(result[2])
    with disp_log:
        st.dataframe(disp_cut_record, use_container_width=True)
else:
    with disp_result:
        st.markdown("`No results to show`")
        st.table()
    with disp_excess:
        st.markdown("`No excess lengths to show`")
        st.table()
    with disp_log:
        st.markdown("`No logs to show`")
        st.table()


with st.container(border=True):
    st.markdown("Version 1.0.0 | &copy; 2025 [jcdcustodio](https://github.com/jcdcustodio)")

