import pyodbc as sql
import pandas as pd
import os


class DatabaseHandler:
    def __init__(self):
        self.connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={os.getenv('DB_SERVER', 'localhost,1433')};"
            f"DATABASE={os.getenv('DB_NAME', 'ReportDb')};"
            f"UID={os.getenv('DB_USER', 'sa')};"
            f"PWD={os.getenv('DB_PASSWORD', 'Password123')};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )
        self.conn = None

    def connect(self):
        try:
            self.conn = sql.connect(self.connection_string, timeout=0)
        except Exception as e:
            print(f"Database connection failed: {e}")
            self.conn = None

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    # 確認資料是否重複上傳
    def check_date_exists(self, date):
        self.connect()
        if not self.conn:
            return False
        try:
            df = pd.read_sql(
                "SELECT COUNT(id) AS Num FROM ConvertibleBondDaily WHERE dataDate = ?",
                self.conn,
                params=[date],
            )
            return int(df["Num"][0]) > 0
        except Exception as e:
            print(f"check_date_exists error: {e}")
            return False
        finally:
            self.close()

    def insert_upload_log(self, date):
        self.connect()
        if not self.conn:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO ConvertibleBondDaily_upload_log VALUES (?, GETDATE())",
                (date,),
            )
            self.conn.commit()
        except Exception as e:
            print(f"insert_upload_log error: {e}")
        finally:
            self.close()

    def insert_convertible_bond_daily(self, data, date):
        self.connect()
        if not self.conn:
            return False

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
            return True
        except Exception as e:
            print(f"insert_convertible_bond_daily error: {e}")
            return False
        finally:
            self.close()

    def download_convertible_bond(self, start_date, end_date, bond_id=None, company_name=None):
        self.connect()
        if not self.conn:
            return None

        sql_query = """
            SELECT
                dataDate AS '日期', id AS '代號', name AS '名稱', trade_type AS '交易',
                closing_price AS '收市', change_price AS '漲跌', open_price AS '開市',
                high_price AS '最高', low_price AS '最低', trade_count AS '筆數',
                unit_count AS '單位', total_amount AS '金額', avg_price AS '均價',
                next_ref_price AS '明日參價', next_limit_up AS '明日漲停', next_limit_down AS '明日跌停'
            FROM ConvertibleBondDaily
            WHERE dataDate BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if bond_id:
            sql_query += " AND id = ?"
            params.append(bond_id)
        if company_name:
            sql_query += " AND name LIKE ?"
            params.append(f"%{company_name}%")

        sql_query += " ORDER BY id, dataDate ASC"

        try:
            df = pd.read_sql(sql_query, self.conn, params=params)
            if df.empty:
                return None
            filename = f"ConvertibleBondReport{start_date}_{end_date}.xlsx"
            os.makedirs("app/file", exist_ok=True)
            df.to_excel(os.path.join("app/file", filename), index=False)
            return filename
        except Exception as e:
            print(f"download_convertible_bond error: {e}")
            return None
        finally:
            self.close()

    def query_convertible_bond(self, start_date, end_date, bond_id=None, company_name=None):
        self.connect()
        if not self.conn:
            return []

        sql_query = """
            SELECT
                dataDate, id, name, trade_type, closing_price, change_price, open_price,
                high_price, low_price, trade_count, unit_count, total_amount, avg_price,
                next_ref_price, next_limit_up, next_limit_down
            FROM ConvertibleBondDaily
            WHERE dataDate BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if bond_id:
            sql_query += " AND id = ?"
            params.append(bond_id)
        if company_name:
            sql_query += " AND name LIKE ?"
            params.append(f"%{company_name}%")

        sql_query += " ORDER BY id, dataDate ASC"

        try:
            df = pd.read_sql(sql_query, self.conn, params=params)
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"query_convertible_bond error: {e}")
            return []
        finally:
            self.close()

    def query_recent_status(self, filter_year=None):
        self.connect()
        if not self.conn:
            return []

        year_pattern = (filter_year + '%') if filter_year else '%'

        sql_query = """
            SELECT
                CASE WHEN c.Num > 0 THEN 'Exist' ELSE 'Not Exist' END AS DataStatus,
                CASE WHEN c.Num > 0 THEN '"badge badge-sm bg-gradient-success"'
                     ELSE '"badge badge-sm bg-gradient-secondary"' END AS DataStatus_Class,
                CONVERT(varchar, (CONVERT(float, c.Num) / 330 * 100)) + '%' AS percentage,
                CONVERT(varchar, (CONVERT(float, c.Num) / 330 * 100)) AS percentage_class,
                c.*,
                CASE WHEN c.Num > 0 THEN 'disabled' ELSE '' END AS Show_download_btn,
                CASE WHEN c.Num > 0 THEN 'Secondary' ELSE 'success' END AS Download_btn_class
            FROM (
                SELECT TOP (365)
                    a.[Date],
                    CASE a.[Day]
                        WHEN '0' THEN '(Sun)' WHEN '1' THEN '(Mon)' WHEN '2' THEN '(Tus)'
                        WHEN '3' THEN '(Wed)' WHEN '4' THEN '(Thu)' WHEN '5' THEN '(Fri)'
                        WHEN '6' THEN '(Sat)'
                    END AS Day,
                    'https://www.tpex.org.tw/storage/bond_zone/tradeinfo/cb/'
                        + LEFT(a.[Date], 4) + '/'
                        + REPLACE(LEFT(a.[Date], 7), '-', '') + '/RSta0113.'
                        + REPLACE(a.[Date], '-', '') + '-C.csv' AS Url,
                    ISNULL(b.num, 0) AS Num,
                    CASE WHEN b.Num > 0 THEN '200' ELSE 'Search' END AS Status_code
                FROM [ReportDb].[dbo].[Date] a
                LEFT JOIN (
                    SELECT dataDate, COUNT(id) AS num
                    FROM ConvertibleBondDaily
                    WHERE dataDate <= GETDATE()
                    GROUP BY dataDate
                ) b ON a.[Date] = b.dataDate
                WHERE [Date] <= GETDATE() AND [Date] LIKE ?
                ORDER BY [Date] DESC
            ) c
        """
        try:
            df = pd.read_sql(sql_query, self.conn, params=[year_pattern])
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"query_recent_status error: {e}")
            return []
        finally:
            self.close()

    def get_data_days_count(self):
        self.connect()
        if not self.conn:
            return None
        try:
            df = pd.read_sql(
                "SELECT COUNT(DISTINCT dataDate) AS Num FROM ConvertibleBondDaily",
                self.conn,
            )
            return str(df["Num"][0])
        except Exception as e:
            print(f"get_data_days_count error: {e}")
            return None
        finally:
            self.close()

    def get_latest_upload_date(self):
        self.connect()
        if not self.conn:
            return None
        try:
            df = pd.read_sql(
                "SELECT TOP (1) [Date] FROM [ReportDb].[dbo].[ConvertibleBondDaily_upload_log] ORDER BY [index] DESC",
                self.conn,
            )
            return str(df["Date"][0])
        except Exception as e:
            print(f"get_latest_upload_date error: {e}")
            return None
        finally:
            self.close()

    def get_latest_trading_date(self):
        self.connect()
        if not self.conn:
            return None
        try:
            df = pd.read_sql(
                """
                SELECT TOP (1) CONCAT([Date], CASE [Day]
                    WHEN '1' THEN ' (Mon)' WHEN '2' THEN ' (Tus)' WHEN '3' THEN ' (Wed)'
                    WHEN '4' THEN ' (Thu)' WHEN '5' THEN ' (Fri)'
                END) AS Date
                FROM [ReportDb].[dbo].[Date]
                WHERE [Day] NOT IN ('0', '6') AND [Date] <= GETDATE()
                ORDER BY [Date] DESC
                """,
                self.conn,
            )
            return str(df["Date"][0])
        except Exception as e:
            print(f"get_latest_trading_date error: {e}")
            return None
        finally:
            self.close()

    def get_data_years(self):
        self.connect()
        if not self.conn:
            return []
        try:
            df = pd.read_sql(
                "SELECT DISTINCT LEFT(Date, 4) AS Year FROM Date WHERE [Date] <= GETDATE() ORDER BY Year DESC",
                self.conn,
            )
            return df["Year"].tolist()
        except Exception as e:
            print(f"get_data_years error: {e}")
            return []
        finally:
            self.close()
