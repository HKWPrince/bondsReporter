import pandas as pd
import pyodbc as sql
import requests
import time
import os

server = 'localhost,1433' 
database = 'ReportDb' 
username = 'sa' 
password = 'Password123' 
connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;'
try:
    conn = sql.connect(connectionString, timeout=0)
except Exception as e:
    print(f"Database connection failed: {e}")


def insert_convertible_bond_daily(filepath, date):
    server = 'localhost,1433' 
    database = 'ReportDb' 
    username = 'sa' 
    password = 'Password123' 
    connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;'

    df_file = pd.read_csv(filepath, encoding='cp950',skiprows=2, header=None)
    # 確認日期
    with open(filepath, 'r', encoding='cp950') as f:
        lines = f.readlines()
        date = lines[1].split(',')[1].strip()
        date = date.replace('日期:','').replace('年','/').replace('月','/').replace('日','')
        date_list = date.split('/')
        year=str(int(date_list[0])+1911)
        date = year+'/'+date_list[1]+'/'+date_list[2]
        
    df_file = df_file.iloc[2:,1:]
    try:
        conn = sql.connect(connectionString, timeout=0)
    except Exception as e:
        print(f"Database connection failed: {e}")

    if conn is None or conn.closed:
        try:
            conn = sql.connect(connectionString, timeout=0)
        except Exception as e:
            print(f"Database connection failed: {e}")

    SQL_STATEMENT = """
                    INSERT INTO ConvertibleBondDaily 
                    (dataDate, id, name, trade_type, closing_price, change_price, open_price, high_price, low_price,
                        trade_count, unit_count, total_amount, avg_price, next_ref_price, next_limit_up, next_limit_down) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
    try:
        for index, row in df_file.iterrows():
            if not (pd.isnull(row[1])):
                if (row[1] == "合計"):
                    break
                try:
                    cursor = conn.cursor()
                    cursor.execute(SQL_STATEMENT,
                    date,
                    row[1],  # id
                    row[2].strip() if pd.notnull(row[2]) else None,  # name
                    row[3] if pd.notnull(row[3]) else None,  # trade_type
                    float(row[4]) if pd.notnull(row[4]) else None,  # closing_price
                    float(row[5]) if pd.notnull(row[5]) else None,  # change_price
                    float(row[6]) if pd.notnull(row[6]) else None,  # open_price
                    float(row[7]) if pd.notnull(row[7]) else None,  # high_price
                    float(row[8]) if pd.notnull(row[8]) else None,  # low_price
                    int(row[9].strip().replace(",","")) if pd.notnull(row[9]) else None,  # trade_count
                    int(row[10].strip().replace(",","")) if pd.notnull(row[10]) else None,  # unit_count
                    int(row[11].strip().replace(",","")) if pd.notnull(row[11]) else None,  # total_amount
                    float(row[12]) if pd.notnull(row[12]) else None,  # avg_price
                    float(row[13]) if pd.notnull(row[13]) else None,  # next_ref_price
                    float(row[14]) if pd.notnull(row[14]) else None,  # next_limit_up
                    float(row[15]) if pd.notnull(row[15]) else None  # next_limit_down
                    )
                    conn.commit()
                except Exception as e:
                    print(f"Error encountered while processing row {index}")
                    print(f"Row data: {row}")
                    print(f"Error: {str(e)}")
                    return False
        cursor.close()
    except Exception as e:
        print(f"Database insert error: {e}")
        return False
    finally:
        conn.close()
        print(date+" ✅ 檔案已成功匯入DB！")
        return True






sql_query = """
            SELECT Top(10)
            a.[Date]
                            , (Case
                                When a.[Day] = '0' Then '(Sun)'
                                When a.[Day] = '1' Then '(Mon)'
                                When a.[Day] = '2' Then '(Tus)'
                                When a.[Day] = '3' Then '(Wed)'
                                When a.[Day] = '4' Then '(Thu)'
                                When a.[Day] = '5' Then '(Fri)'
                                When a.[Day] = '6' Then '(Sat)'
                            End) as 'Day',
            'https://www.tpex.org.tw/storage/bond_zone/tradeinfo/cb/'+Left(a.[Date],4)+'/'+Replace(LEFT(a.[Date],7),'-','')+'/RSta0113.'+Replace(a.[Date],'-','')+'-C.csv' as 'Url'
                            -- https://www.tpex.org.tw/storage/bond_zone/tradeinfo/cb/2025/202504/RSta0113.20250407-C.csv
                            , ISNULL(b.num,0) as 'Num'
                            , 'X' as 'Status_code'
                            , '' as 'process'
                            , '' as 'filepath'
            FROM [ReportDb].[dbo].[Date] a
                LEFT JOIN(
                                    SELECT
                    dataDate,
                    COUNT(id) as 'num'
                From ConvertibleBondDaily
                WHERE [dataDate] <= GETDATE()
                GROUP BY dataDate) b on a.[Date] =b.dataDate
            Where  [Date] <= GETDATE()
            ORDER BY [Date] DESC
        """
df = pd.read_sql(sql_query,conn)
table = df.to_dict(orient="records")
if not (os.path.exists("csvFile")):
    os.mkdir("csvFile")

url=""
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

for element in table:
    url = element['Url']
    response = requests.get(url, headers=headers)
    element['Status_code'] = response.status_code
    # 送出 GET 請求
    fileName=str(element['Date']).replace("-","")+".csv"
    # 檢查回應狀態
    if response.status_code == 200 and response.headers['Content-Type'] != 'text/html':
        # 將內容存成本地檔案
        filepath = os.path.join("csvFile", fileName)
        with open(filepath, "wb") as f:
            f.write(response.content)
        print( fileName+" ✅ 檔案已成功下載！")
        element['filepath'] = filepath
        element['Status_code'] = '200'
    elif response.headers['Content-Type'] == 'text/html':
        element['Status_code'] = '404'
    else:
        print( fileName+" ❌ 檔案下載失敗")
    
    time.sleep(1)
    
    log = pd.DataFrame.from_dict(table)
    log.to_csv(os.path.join("csvFile","log.csv"))

if not (os.path.exists(os.path.join("csvFile","clear"))):
    os.mkdir(os.path.join("csvFile","clear"))



# 寫入DB
for element in table:
    status_code = element['Status_code']
    filepath = element['filepath']
    process = element['process'] 
    date=str(element['Date']).replace("-","/")
    # 檢查回應狀態
    if status_code == '200':
        # 將內容存成本地檔案
        if insert_convertible_bond_daily(filepath, date):
            element['process'] = '2'
            log = pd.DataFrame.from_dict(table)
            log.to_csv(os.path.join("csvFile","log.csv"))