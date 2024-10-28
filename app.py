import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash.dependencies import Input, Output, State
import datetime

# 读取随机生成的交易数据（已保存的CSV文件）
commbank_df = pd.read_csv('commbank_transactions.csv')
anz_df = pd.read_csv('anz_transactions.csv')
boc_df = pd.read_csv('boc_transactions.csv')

# 修正列名（确保 Category 列名正确）
commbank_df.columns = [col.strip() for col in commbank_df.columns]
anz_df.columns = [col.strip() for col in anz_df.columns]
boc_df.columns = [col.strip() for col in boc_df.columns]

# 添加本人账户信息
personal_accounts = {
    'CommBank': '111111-0000',
    'ANZ': '222222-0000',
    'BOC': '333333-0000'
}

# 添加一列“Bank”用于区分不同银行的数据
commbank_df['Bank'] = 'CommBank'
anz_df['Bank'] = 'ANZ'
boc_df['Bank'] = 'BOC'

# 将 'Transaction Time' 列转换为 datetime 对象
commbank_df['Transaction Time'] = pd.to_datetime(commbank_df['Transaction Time'])
anz_df['Transaction Time'] = pd.to_datetime(anz_df['Transaction Time'])
boc_df['Transaction Time'] = pd.to_datetime(boc_df['Transaction Time'])

# 合并所有交易数据
all_transactions = pd.concat([commbank_df, anz_df, boc_df])

# 标记交易为收入或支出
def categorize_transactions(df, bank_name):
    personal_account = personal_accounts[bank_name]
    df['Category'] = df.apply(lambda x: 'income' if x['To Account'] == personal_account else 'expense', axis=1)
    return df

# 为每个银行的交易数据添加收入/支出标记
commbank_df = categorize_transactions(commbank_df, 'CommBank')
anz_df = categorize_transactions(anz_df, 'ANZ')
boc_df = categorize_transactions(boc_df, 'BOC')

# 合并所有处理后的交易数据
all_transactions = pd.concat([commbank_df, anz_df, boc_df])

# 设置初始账户余额
initial_balance = 1000

# 支出分类，确保所有实际使用到的类别都包含在内
expense_categories = ['Groceries', 'Eating out', 'Transport', 'Entertainment', 'Education', 
                      'Health', 'Cash', 'Uncategorised', 'Fee & Interest', 'Other']

# 预算默认值（每周预算，用户可以调整）
default_budget = {cat: 50 for cat in expense_categories}

# 计算总收入和支出
def calculate_summary(df):
    total_income = df[df['Category'] == 'income']['Amount'].sum()
    total_expense = df[df['Category'] == 'expense']['Amount'].sum()
    balance = initial_balance + total_income - total_expense
    return balance, total_income, total_expense

# 创建Dashboard应用
app = dash.Dash(__name__)

server = app.server

# 布局设计
app.layout = html.Div(children=[
    # 问候语
    html.H1(children='Hello, Zeno', style={'textAlign': 'left', 'marginLeft': '20px'}),

    # 银行选择下拉菜单
    html.Div([
        dcc.Dropdown(
            id='bank-selector',
            options=[
                {'label': 'All Banks', 'value': 'all'},
                {'label': 'CommBank', 'value': 'CommBank'},
                {'label': 'ANZ', 'value': 'ANZ'},
                {'label': 'BOC', 'value': 'BOC'}
            ],
            value='all',  # 默认选择显示所有银行
            clearable=False
        )
    ], className='bank-dropdown'),

    # 日期选择器
    html.Div([
        dcc.DatePickerRange(
            id='date-picker',
            min_date_allowed=all_transactions['Transaction Time'].min().date(),
            max_date_allowed=all_transactions['Transaction Time'].max().date(),
            start_date=all_transactions['Transaction Time'].min().date(),
            end_date=all_transactions['Transaction Time'].max().date()
        )
    ], className='date-picker'),

    # 总账户信息展示
    html.Div([
        html.H3(id='balance-display'),
        html.H3(id='income-display'),
        html.H3(id='expense-display')
    ], className='summary-container'),

    # 收入与支出的分类饼图
    html.Div([
        dcc.Graph(id='income-breakdown'),
        dcc.Graph(id='expense-breakdown')
    ], className='pie-chart'),

    # 周收入与支出的柱状图，添加标题
    html.Div([
        dcc.Graph(id='income-expense-weekly', config={'displayModeBar': False})
    ], className='bar-chart'),

    # 预算设置控件（只能设置预算值，不能选择类别）
    html.Div([
        html.H4('Weekly Budget for Expense Categories'),
        dcc.Dropdown(
            id='category-selector',
            options=[{'label': cat, 'value': cat} for cat in expense_categories],
            placeholder='Select a category'
        ),
        dcc.Input(id='budget-input', type='number', placeholder='Enter budget amount'),
        html.Button('Set Budget', id='set-budget-btn', n_clicks=0),
        html.Div(id='budget-status', style={'marginTop': '10px'})
    ], className='budget-controls'),

    # 预算计划的柱状图
    html.Div([
        dcc.Graph(id='budget-plan')
    ], className='budget-plan'),
    
    # 交易记录
    html.Div([
        html.H4('Transaction Records'),
        html.Div(id='transaction-table')
    ], className='transaction-records')
])

# 回调函数：根据选择的银行、日期范围和预算设置更新所有图表和数据
@app.callback(
    [Output('balance-display', 'children'),
     Output('income-display', 'children'),
     Output('expense-display', 'children'),
     Output('income-breakdown', 'figure'),
     Output('expense-breakdown', 'figure'),
     Output('income-expense-weekly', 'figure'),
     Output('budget-plan', 'figure'),
     Output('transaction-table', 'children')],
    [Input('bank-selector', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('set-budget-btn', 'n_clicks')],
    [State('category-selector', 'value'),
     State('budget-input', 'value')]
)
def update_dashboard(selected_bank, start_date, end_date, n_clicks, selected_category, budget_value):
    # 更新预算设置
    if n_clicks > 0 and selected_category and budget_value is not None:
        default_budget[selected_category] = budget_value

    # 根据选择的银行和日期范围过滤数据
    filtered_transactions = all_transactions[
        (all_transactions['Transaction Time'] >= pd.to_datetime(start_date)) &
        (all_transactions['Transaction Time'] <= pd.to_datetime(end_date))
    ]
    
    if selected_bank != 'all':
        filtered_transactions = filtered_transactions[filtered_transactions['Bank'] == selected_bank]

    # 计算余额、收入和支出
    balance, total_income, total_expense = calculate_summary(filtered_transactions)

    # 收入分类饼图
    income_breakdown = px.pie(
        filtered_transactions[filtered_transactions['Category'] == 'income'], 
        names='Transaction Type', 
        values='Amount', 
        title='Income Breakdown'
    )

    # 支出分类饼图
    expense_breakdown = px.pie(
        filtered_transactions[filtered_transactions['Category'] == 'expense'], 
        names='Transaction Type', 
        values='Amount', 
        title='Expense Breakdown'
    )

    # 周收入与支出柱状图
    weekly_chart = go.Figure(data=[
        go.Bar(name='Income', x=filtered_transactions['Transaction Time'], 
               y=filtered_transactions[filtered_transactions['Category'] == 'income']['Amount']),
        go.Bar(name='Expense', x=filtered_transactions['Transaction Time'], 
               y=abs(filtered_transactions[filtered_transactions['Category'] == 'expense']['Amount']))
    ])
    weekly_chart.update_layout(title='Weekly Income & Expense')

    # 计算所选日期范围的长度（天数），并根据每7天预算等比例调整预算柱
    date_range_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
    adjustment_factor = date_range_days / 7

    # 在所选日期范围内的实际支出数据
    actual_expenses = filtered_transactions[filtered_transactions['Category'] == 'expense']

    # 汇总支出总额并确保与默认预算的类别顺序一致
    expense_totals = actual_expenses.groupby('Transaction Type')['Amount'].sum()

    # 预算计划柱状图
    budget_chart = go.Figure(data=[
        go.Bar(name='Budget', 
               x=list(default_budget.keys()), 
               y=[budget * adjustment_factor for budget in default_budget.values()]),
        go.Bar(name='Actual Expense', 
               x=list(default_budget.keys()), 
               y=expense_totals.values)
    ])
    budget_chart.update_layout(title="Adjusted Budget vs. Actual Expense", barmode='group')

    # 交易记录表格
    recent_transactions = filtered_transactions.sort_values(by='Transaction Time', ascending=False).head(10)

    # 交易记录表格
    transaction_rows = [html.Tr([html.Th(col) for col in recent_transactions.columns])] + \
                       [html.Tr([html.Td(recent_transactions.iloc[i][col]) for col in recent_transactions.columns]) 
                        for i in range(len(recent_transactions))]

    return (f'Balance: AU${balance:.2f}',
            f'Total income: AU${total_income:.2f}',
            f'Total expense: AU${total_expense:.2f}',
            income_breakdown,
            expense_breakdown,
            weekly_chart,
            budget_chart,
            html.Table(transaction_rows))

# 运行应用
if __name__ == '__main__':
    app.run_server(debug=True)


