import numpy as np
import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def create_connection():
    connection = sqlite3.connect('sample.sqlite')

    cursor = connection.cursor()
    return cursor,connection

def get_tasks(con):
    account_data = pd.read_sql('SELECT * FROM account',con=con)
    account_date_session = pd.read_sql('SELECT * FROM account_date_session',con=con)
    iap_purchase = pd.read_sql('SELECT * FROM iap_purchase',con=con)
    
    return account_data,account_date_session,iap_purchase


def get_categorical_data(data):
    categorical = data.dtypes[data.dtypes=="object"].index
    
    print(categorical)
    print("")
    print(account_data[categorical].describe())

def view_revenue_to_date(conn):
    df = pd.read_sql_query("SELECT DATE(created_time) AS date, SUM(iap_price_usd_cents) / 100 AS revenue FROM iap_purchase GROUP BY date ORDER BY date ASC", conn)

    plt.figure(figsize=(10,6))

    df.plot(x="date", y="revenue", title="Daily Revenue summarization (2016)", color='r', marker='o', markersize=5, fontsize=12)

    plt.tick_params(axis='both', which='major', labelsize=12)

    plt.title("Daily Revenue Summarization (2016)", fontsize=16, fontweight='bold')
    plt.xlabel("Date", fontsize=14, fontweight='bold')
    plt.ylabel("Revenue (USD)", fontsize=14, fontweight='bold')

    plt.grid(color='grey', linestyle='-', linewidth=0.5)

    plt.legend(["Revenue"], fontsize=12, loc='upper left')

    plt.show()

def revenue_ios_vs_android(conn):
    #double check
    query = '''
        SELECT a.created_platform, SUM(p.iap_price_usd_cents)/100 AS total_revenue
        FROM account a
        JOIN iap_purchase p ON a.account_id = p.account_id
        JOIN account_date_session s ON a.account_id = s.account_id
        WHERE a.created_time BETWEEN '2016-01-01' AND '2016-12-31'
        AND p.created_time BETWEEN '2016-01-01' AND '2016-12-31'
        AND s.date BETWEEN '2016-01-01' AND '2016-12-31'
        GROUP BY a.created_platform
    '''

    df = pd.read_sql_query(query, conn)

    sns.barplot(x='created_platform', y='total_revenue', data=df, palette='PuBuGn_d')
    plt.title('Revenue by Platform (2016)', fontsize=16, fontname='Arial', fontweight='bold')
    plt.ylabel('Total Revenue (USD)', fontsize=12, fontname='Arial')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.show()

##Check if corr
def active_users_ios_vs_android(conn):
    
    # Query the database to get the number of active users for each platform
    query = """
    SELECT created_platform, COUNT(DISTINCT account.account_id) as num_active_users
    FROM account
    INNER JOIN account_date_session ON account.account_id = account_date_session.account_id
    WHERE account_date_session.date BETWEEN '2016-01-01' AND '2016-12-31' AND created_platform IS NOT NULL
    GROUP BY created_platform
    """
    df = pd.read_sql(query, conn)

    df = df.sort_values("num_active_users", ascending=False)

    sns.barplot(x="created_platform", y="num_active_users", data=df, palette='PuBuGn_d')
    plt.title("Number of Active Users by Platform", fontsize=16, fontname='Arial', fontweight='bold')
    plt.xlabel("Platform", fontsize=12, fontname='Arial')
    plt.ylabel("Number of Active Users", fontsize=12, fontname='Arial')
    plt.grid(True)
    plt.show()

def user_growth_vs_revenue_growth(conn):
    #Reads SQL query results into a Pandas dataframe and group the number of user created by month
    user_growth = pd.read_sql_query("SELECT strftime('%Y-%m', created_time) as month, COUNT(DISTINCT account_id) as user_count FROM account GROUP BY month", conn)

    revenue_growth = pd.read_sql_query("SELECT strftime('%Y-%m', created_time) as month, SUM(iap_price_usd_cents)/100 as revenue FROM iap_purchase GROUP BY month", conn)

    df = pd.merge(user_growth, revenue_growth, on='month')

    correlation = df['user_count'].corr(df['revenue'])
    print(correlation)

    #Positive correlation > increasing number of active users leads to increase in revenue. 
    # Set figure size and title font size
    sns.regplot(x='user_count', y='revenue', data=df, color='lightblue', scatter_kws={'s': 50}, line_kws={'color': 'red'})
    plt.title("User Growth vs Revenue Growth (2016)", fontsize=16, fontname='Arial', fontweight='bold')
    plt.xlabel("User Count", fontsize=12, fontname='Arial')
    plt.ylabel("Revenue", fontsize=12, fontname='Arial')
    plt.legend(['Linear Regression', 'Data Points'])
    plt.grid(True)

    r_sq = df[['user_count', 'revenue']].corr()**2
    plt.text(0.6, 0.2, 'Coefficient of Determination: {:.2f}'.format(r_sq.iloc[0, 1]), transform=plt.gcf().transFigure)

    plt.show()

def lifetime_revenue(conn):
    
    lifetime_revenue_query = '''
    SELECT account_id, SUM(iap_price_usd_cents) AS lifetime_revenue
    FROM iap_purchase
    GROUP BY account_id
    '''

    first_week_revenue_query = '''
        SELECT account.account_id, SUM(iap_purchase.iap_price_usd_cents) AS first_week_revenue
        FROM account
        LEFT JOIN iap_purchase ON account.account_id = iap_purchase.account_id
        WHERE iap_purchase.created_time BETWEEN account.created_time AND date(account.created_time, '+7 day')
        GROUP BY account.account_id
    '''
    
    df_lifetime_revenue = pd.read_sql_query(lifetime_revenue_query, conn)
    df_first_week_revenue = pd.read_sql_query(first_week_revenue_query, conn)

    #Merge and calculate the proportion of lifetime revenue generated in the first week
    df_revenue = pd.merge(df_lifetime_revenue, df_first_week_revenue, on='account_id')
    df_revenue['first_week_proportion'] = df_revenue['first_week_revenue'] / df_revenue['lifetime_revenue'] * 100

    # Calculate the number of players who generated more than 50% of their lifetime revenue in the first week
    players_50_proportion = df_revenue[df_revenue['first_week_proportion'] > 50].shape[0] / df_revenue.shape[0]

    colors = sns.color_palette("PuBuGn_d")
    font = {'family': 'Arial', 'size': 14}

    # Create a pie chart to visualize the proportion of players who generated more than 50% of LTV first week
    labels = ['Less than 50%', 'Greater than 50%']
    sizes = [1 - players_50_proportion, players_50_proportion]

    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', pctdistance=0.7, labeldistance=1.05, shadow=True)
    plt.axis('equal')
    plt.title('Proportion of Players Who Generated More Than 50% of Their Lifetime Revenue in First Week', fontdict=font)
    plt.legend(title='Lifetime Revenue', prop={'size': 14})
    plt.show()


    overall_proportion = df_revenue['first_week_proportion'].mean()

    print("Overall proportion of lifetime revenue generated in the first week:", overall_proportion)
    print("Proportion of players who generate more than 50% of their lifetime revenue in the first week:", players_50_proportion)

def ltv_january_vs_december(conn):
    # Calculate the LTV at the beginning of January
    january_ltv_query = '''
        SELECT AVG(iap_total) AS january_ltv
        FROM (
            SELECT account_id, SUM(iap_price_usd_cents) AS iap_total
            FROM iap_purchase
            WHERE created_time BETWEEN '2016-01-01' AND '2016-01-31'
            GROUP BY account_id
        )
    '''

    # Calculate the LTV at the end of December
    december_ltv_query = '''
        SELECT AVG(iap_total) AS december_ltv
        FROM (
            SELECT account_id, SUM(iap_price_usd_cents) AS iap_total
            FROM iap_purchase
            WHERE created_time BETWEEN '2016-12-01' AND '2016-12-31'
            GROUP BY account_id
        )
    '''

    df_january_ltv = pd.read_sql_query(january_ltv_query, conn)
    df_december_ltv = pd.read_sql_query(december_ltv_query, conn)

    # Compare the LTV at the end of December and beg of january
    if df_december_ltv['december_ltv'][0] < df_january_ltv['january_ltv'][0]:
        print("The LTV has gone down from January to December.")
        print(df_december_ltv['december_ltv'][0])
        print(df_january_ltv['january_ltv'][0])
    else:
        print("The LTV has not gone down from January to December.") 
    

    # Set the x/y-axis values (the months of the year)
    x = ['January', 'December']

    # Set the y-axis values (the LTV per player)
    y = [df_january_ltv['january_ltv'][0], df_december_ltv['december_ltv'][0]]

    colors = ['#1f77b4', '#ff7f0e']

    # Create a bar chart to visualize the comparison
    plt.bar(x, y, color=colors)
    plt.xlabel('Month', fontsize=14, fontweight='bold')
    plt.ylabel('LTV per Player', fontsize=14, fontweight='bold')
    plt.title('LTV Comparison: January vs. December', fontsize=18, fontweight='bold')
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()

if __name__ == "__main__":
    dirname = os.path.dirname(__file__)
    data_file_path = os.path.join(dirname, "sample.sqlite")
    cursor,conn = create_connection()
    account_data,account_date_session,iap_purchase = get_tasks(conn)

    #warmup
    view_revenue_to_date(conn)
    revenue_ios_vs_android(conn)
    active_users_ios_vs_android(conn)
    user_growth_vs_revenue_growth(conn)
    #Task 1
    lifetime_revenue(conn)
    ltv_january_vs_december(conn)