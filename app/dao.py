import pyodbc as sql
import pandas as pd

class DatabaseHandler:
    def __init__(self, server='localhost,1433', database='ReportDb', username='sa', password='Password123'):
        self.connection_string = f'''
            DRIVER={{ODBC Driver 18 for SQL Server}};
            SERVER={server};
            DATABASE={database};
            UID={username};
            PWD={password};
            Encrypt=yes;
            TrustServerCertificate=yes;
        '''
        self.conn = None

    #"""建立資料庫連線"""
    def connect(self):
        try:
            self.conn = sql.connect(self.connection_string, timeout=0)
        except Exception as e:
            print(f"Database connection failed: {e}")
    
    #"""關閉資料庫連線"""
    def close(self):
        if self.conn:
            self.conn.close()

    # 確認資料是否重複上傳
    def check_convertible_bond_daily_exist(self,date):
        if not self.conn:
            self.connect()
        else:
            return False  # 無法連接時，直接返回
        
        SQL_STATEMENT = """
                        SELECT 
                        COUNT(id) as 'Num'
                        FROM ConvertibleBondDaily
                        WHERE dataDate = 
                        """
        SQL_STATEMENT += "'"+date+"'"
        try:
            df = pd.read_sql(SQL_STATEMENT, self.conn)
            if ((df["Num"][0])!=0):
                return True
                
            else:
                return False
        
        except Exception as e:
            print(f"Database check_convertible_bond_daily_exist error: {e}")
            return None
        finally:
            self.conn.close()

    #"""加入資料到 ConvertibleBondDaily 資料表"""
    def insert_convertible_bond_daily_upload_log(self, data):
        if self.conn is None or self.conn.closed:
            self.connect() # 無法連接時，直接返回

        SQL_STATEMENT = """
                        INSERT INTO ConvertibleBondDaily_upload_log
                        VALUES ( '"""+data+"""',GETDATE()) 
                        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(SQL_STATEMENT)
            self.conn.commit()
        except Exception as e:
            print(f"Insert convertible_bond_daily_upload_log error: {e}")
        finally:
                cursor.close()
                self.conn.close()


    #"""加入資料到 ConvertibleBondDaily 資料表"""
    def insert_convertible_bond_daily(self, data, date):
        if self.conn is None or self.conn.closed:
            self.connect() # 無法連接時，直接返回

        SQL_STATEMENT = """
                        INSERT INTO ConvertibleBondDaily 
                        (dataDate, id, name, trade_type, closing_price, change_price, open_price, high_price, low_price,
                            trade_count, unit_count, total_amount, avg_price, next_ref_price, next_limit_up, next_limit_down) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
        try:
            for index, row in data.iterrows():
                # print(index,": ",sep="")
                if not (pd.isnull(row[1])):
                    if (row[1] == "合計"):
                        break
                    try:
                        cursor = self.conn.cursor()
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
                        self.conn.commit()
                    except Exception as e:
                        print(f"Error encountered while processing row {index}")
                        print(f"Row data: {row}")
                        print(f"Error: {str(e)}")
                        return False
        except Exception as e:
            print(f"Database insert error: {e}")
            return False
        finally:
                cursor.close()
                self.conn.close()
                return True

    
    #"""查詢符合條件的可轉債交易數據，並匯出Excel file"""
    def download_convertible_bond(self, startDate, endDate, id=None, companyName=None):
        self.connect()
        if not self.conn:
            return None

        sql_query = """
        SELECT 
            dataDate as '日期', 
            id as '代號', 
            name as '名稱', 
            trade_type as '交易', 
            closing_price as '收市', 
            change_price as '漲跌', 
            open_price as '開市', 
            high_price as '最高', 
            low_price as '最低',
            trade_count as '筆數', 
            unit_count as '單位', 
            total_amount as '金額', 
            avg_price as '均價', 
            next_ref_price as '明日參價', 
            next_limit_up as '明日漲停', 
            next_limit_down as '明日跌停'
        FROM ConvertibleBondDaily
        WHERE dataDate BETWEEN """
        
        sql_query += "'"+startDate+"'" + " AND " + "'" +endDate+ "'"

        # 如果有輸入公司 ID
        if id:
            sql_query += " AND id = " + "'" + id + "'"

        # 如果有輸入公司名稱
        if companyName:
            sql_query += " AND name LIKE " + "N'%" + companyName + "%'"

        try:
            sql_query = sql_query + " ORDER By id , dataDate Asc "

            df = pd.read_sql(sql_query, self.conn)

            if df is None or df.empty:
                return None

            # 儲存 Excel 檔案
            filename = "ConvertibleBondReport"+startDate+"_"+endDate+".xlsx"
            df.to_excel("./app/file/"+filename, index=False)

            return filename
        
        except Exception as e:
            print(f"Database query error: {e}")
            return None
        finally:
            self.conn.close()
    
    #"""查詢符合條件的可轉債交易數據，並回傳至前端"""
    def query_convertible_bond(self, startDate, endDate, id=None, companyName=None):
        self.connect()
        if not self.conn:
            return None

        sql_query = """
            SELECT 
            dataDate, 
            id, 
            name, 
            trade_type, 
            closing_price, 
            change_price, 
            open_price, 
            high_price, 
            low_price,
            trade_count, 
            unit_count, 
            total_amount, 
            avg_price, 
            next_ref_price, 
            next_limit_up, 
            next_limit_down
        FROM ConvertibleBondDaily
        WHERE dataDate BETWEEN """
        
        sql_query += "'"+startDate+"'" + " AND " + "'" +endDate+ "'"

        # 如果有輸入公司 ID
        if id:
            sql_query += " AND id = " + "'" + id + "'"

        # 如果有輸入公司名稱
        if companyName:
            sql_query += " AND name LIKE " + "N'%" + companyName + "%'"
    
        result = """<div class="row">
                <div class="col-md-12 mb-lg-0 mb-4">
                    <div class="card">
                        <div class="card-header p-0 position-relative mt-n4 mx-3 z-index-2">
                            <div class="row">
                                    <div class="bg-gradient-dark shadow-dark border-radius-lg pt-4 pb-3">
                                        <h6 class="text-white text-capitalize ps-3">Search Results</h6>
                                    </div>
                            </div>
                        </div>
                        
                        <div class="card-body px-0 pb-2">
                            <div class="table-responsive">
                                <table class="table align-items-center mb-0 table-hover border border-secondary border-start-0 border-end-0">
                                    <thead>
                                        <tr>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                日期</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                代號</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                名稱</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                交易</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                收市</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                漲跌</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                開市</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                最高</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                最低</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                筆數</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                單位</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                金額</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                均價</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                明日參價</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                明日漲停</th>
                                            <th
                                                class="text-center text-uppercase text-secondary text-s opacity-7">
                                                明日跌停</th>
                                        </tr>
                                    </thead>
                                    <tbody class="table-light border border-secondary border-start-0 border-end-0">
                                        """

        try:
            sql_query = sql_query + " ORDER By id , dataDate Asc "
            df = pd.read_sql(sql_query, self.conn)
            result = df.to_dict(orient="records")
            return result
        
        except Exception as e:
            print(f"Database query error: {e}")
            return None
        finally:
            self.conn.close()

    #"""查詢近30天資料狀況"""
    def query_recent_status(self,filter_year=None):
        self.connect()
        if not self.conn:
            return None
        
        Year = '%'
        if filter_year != None:
            Year = filter_year + Year

        sql_query = """
        Select
        (Case
                        When c.[Num] > 0 Then 'Exist'
                        Else 'Not Exist'
                    End) as 'DataStatus'
        , (Case
                        When c.[Num] > 0 Then '"badge badge-sm bg-gradient-success"'
                        Else '"badge badge-sm bg-gradient-secondary"'
                    End) as 'DataStatus_Class'
        , CONVERT(varchar,(CONVERT(float,c.[Num])/330*100))+'%' as 'percentage'
        , CONVERT(varchar,(CONVERT(float,c.[Num])/330*100)) as 'percentage_class'
        , c.*
        ,(Case
                        When c.[Num] > 0 Then 'disabled'
                        Else ''
                    End) as 'Show_download_btn'
        ,(Case
                        When c.[Num] > 0 Then 'Secondary'
                        Else 'success'
                    End) as 'Download_btn_class'
        From(
                SELECT Top(365)
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
                                    , (Case
                                        When b.[Num] > 0 Then '200'
                                        Else 'Search'
                                    End) as 'Status_code'
                        FROM [ReportDb].[dbo].[Date] a
                            LEFT JOIN(
                                        SELECT
                                dataDate,
                                COUNT(id) as 'num'
                            From ConvertibleBondDaily
                            WHERE [dataDate] <= GETDATE()
                            GROUP BY dataDate) b on a.[Date] =b.dataDate
                        Where [Date] <= GETDATE()
                        ORDER BY [Date] DESC) c
                        where c.[Date] like '""" + Year + """'
                    """ 
        try:
            
            df = pd.read_sql(sql_query, self.conn)
            result = df.to_dict(orient="records")
            
            return result
        except Exception as e:
            print(f"Database query error: {e}")
            return None
        finally:
            self.conn.close()
    # 查詢資料庫資料天數
    def get_dataDaysNum(self):
        self.connect()
        if not self.conn:
            return None
        
        try:
            sql_query = """                                                
                        SELECT 
                            count(distinct dataDate) as 'Num'
                        FROM ConvertibleBondDaily
                        """

            df = pd.read_sql(sql_query, self.conn)
            result = df["Num"][0]
            return str(result)
        
        except Exception as e:
            print(f"Database query error: {e}")
            return None
        finally:
            self.conn.close()

    # 查詢ConvertibleBondDaily最近一筆上傳日期
    def get_LatestUpload(self):
        self.connect()
        if not self.conn:
            return None
        
        try:
            sql_query = """                                                
                        SELECT TOP (1) 
                        [Date]
                        FROM [ReportDb].[dbo].[ConvertibleBondDaily_upload_log]
                        ORDER BY [index] Desc
                        """

            df = pd.read_sql(sql_query, self.conn)
            result = df["Date"][0]
            return str(result)
        
        except Exception as e:
            print(f"Database query error: {e}")
            return None
        finally:
            self.conn.close()
    
    # 查詢最近交易日
    def get_TradingDate(self):
        self.connect()
        if not self.conn:
            return None
        
        try:
            sql_query = """                                                
                        SELECT Top(1) Concat([Date],(Case
                            When [Day] = '1' Then ' (Mon)'
                            When [Day] = '2' Then ' (Tus)'
                            When [Day] = '3' Then ' (Wed)'
                            When [Day] = '4' Then ' (Thu)'
                            When [Day] = '5' Then ' (Fri)'
                        End)) as 'Date'
                        FROM [ReportDb].[dbo].[Date]
                        Where [Day] <>  '0' and [Day] <> '6' and [Date] <= GETDATE()
                        ORDER BY [Date] DESC
                        """
            df = pd.read_sql(sql_query, self.conn)
            result = df["Date"][0]
            return str(result)
        
        except Exception as e:
            print(f"Database query error: {e}")
            return None
        finally:
            self.conn.close()

    # 查詢資料庫資料年份
    def get_DataYears(self):
        self.connect()
        if not self.conn:
            return None
        
        try:
            sql_query = """                                                
                        SELECT 
                        Distinct LEFT(Date,4)  AS Year
                        FROM Date
                        Where [Date] <= GETDATE()
                        ORDER BY [Year] DESC
                        """
            df = pd.read_sql(sql_query, self.conn)
            result = df["Year"].tolist()
            return result
        
        except Exception as e:
            print(f"Database query error: {e}")
            return None
        finally:
            self.conn.close()
