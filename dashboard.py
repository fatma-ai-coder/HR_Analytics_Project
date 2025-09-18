import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px


#------------ Database Setup -----------------
DB_PATH = r"C:\Users\Fatma\OneDrive\Desktop\Solutions_by_STC\Tasks\Week_2\HR_Project\src\employees.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")
st.title("HR Analytics Dashboard")

#--------------- Data Loading ---------------------
@st.cache_data
def load_data():
    return pd.read_sql("SELECT * FROM employees", engine)

df = load_data()


#-------------- Interactive Filter -------------
depts = ["All"] + sorted(df["Department"].dropna().unique().tolist())
slc_dept = st.selectbox("Filter by Department", depts)

if slc_dept != "All":
    filt_df = df[df["Department"] == slc_dept].copy()
else:
    filt_df = df.copy()


#-----------   Key Metrics ------------------ 
colk1, colk2, colk3 = st.columns(3)
with colk1:
    st.metric("Total Employees", int(filt_df.shape[0]))
    
with colk2:
    st.metric("Average Monthly Income", f"{filt_df['MonthlyIncome'].mean():.0f}")

with colk3:
    if filt_df.shape[0] > 0:
        attr_rate = (filt_df['Attrition'] == 'Yes').mean() * 100
        st.metric("Attrition Rate (%)", f"{attr_rate:.2f}")
    else:
        st.metric("Attrition Rate (%)", "N/A")

st.markdown("---")



###############################################################
  ###                 Visualization                      ###
###############################################################
col1, col2, col3 = st.columns((1,1,1))

# Bar Chart
with col1:
    dept_cnt = filt_df['Department'].value_counts().reset_index()
    dept_cnt.columns = ['Department', 'Count']
    fig1 = px.bar(dept_cnt, x='Department', y='Count', title='Employee Count for each Department')
    st.plotly_chart(fig1, use_container_width=True)

# Pie Chart
with col2:
    attr = filt_df['Attrition'].value_counts().reset_index()
    attr.columns = ['Attrition', 'Count']
    fig2 = px.pie(attr, names='Attrition', values='Count', title='Attrition Distribution')
    st.plotly_chart(fig2, use_container_width=True)

# Table
with col3:
    top5 = filt_df.sort_values(['PerformanceRating','MonthlyIncome'], ascending=[False, False]).head(5)
    st.subheader("The Top 5 Employees by Performance Rating")
    st.dataframe(top5[['EmployeeNumber','JobRole','PerformanceRating','MonthlyIncome']])

st.markdown("---")



###############################################################
  ###                Add New Employee                    ###
###############################################################

st.subheader("Add a New Employee")

with st.form("add_employee_form"):
    emp_no = st.number_input("Employee Number", min_value=1, step=1)
    age = st.number_input("Age", min_value=18, max_value=90, step=1)
    dept = st.selectbox("Department", df["Department"].unique().tolist())
    job = st.text_input("Job Role")
    inc = st.number_input("Monthly Income", min_value=0, step=100)
    perf = st.slider("Performance Rating", 1, 5, 3)
    ot = st.selectbox("OverTime", ['Yes','No'])
    submit = st.form_submit_button("Add Employee")

    if submit:
        insert_sql = text("""
            INSERT INTO employees 
            (EmployeeNumber, Age, Department, JobRole, MonthlyIncome, PerformanceRating, Attrition, OverTime)
            VALUES (:emp, :age, :dept, :job, :income, :perf, :attr, :ot)
        """)
        try:
            with engine.begin() as conn:
                conn.execute(insert_sql, {
                    "emp": int(emp_no),
                    "age": int(age),
                    "dept": dept,
                    "job": job,
                    "income": float(inc),
                    "perf": int(perf),
                    "attr": 'No',
                    "ot": ot
                })
            st.success(f"New Employee #{emp_no} is successfully added.")
            
            df = pd.read_sql("SELECT * FROM employees", engine)
        except Exception as e:
            st.error(f"Insert failed: {e}")



###############################################################
  ###           Update Employee Monthly Income           ###
###############################################################

st.subheader("Update The Employee Monthly Income")

with st.form("update_income_form"):
    emp_id = st.number_input("Employee ID", min_value=1, step=1)
    new_inc = st.number_input("New Monthly Income", min_value=0, step=100)
    updt_btn = st.form_submit_button("Update")

    if updt_btn:
        updt_sql = text("UPDATE employees SET MonthlyIncome = :income WHERE EmployeeNumber = :emp")
        try:
            with engine.begin() as conn:
                result = conn.execute(updt_sql, {"income": float(new_inc), "emp": int(emp_id)})
            if result.rowcount == 0:
                st.warning(f"No employee found with Employee Number #{emp_id}.")
            else:
                st.success(f"Updated Monthly Income for Employee #{emp_id}.")
                df = pd.read_sql("SELECT * FROM employees", engine)
        except Exception as e:
            st.error(f"Update failed: {e}")