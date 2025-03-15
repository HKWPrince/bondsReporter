-- 切換到 master 資料庫，確保可以建立新資料庫
USE master;
GO

-- 如果資料庫已存在，則刪除 (⚠️ 只在開發環境使用)
IF EXISTS (SELECT name FROM sys.databases WHERE name = 'ReportDb')
BEGIN
    DROP DATABASE ReportDb;
END
GO

-- 建立新的資料庫
CREATE DATABASE ReportDb;
GO

-- 使用剛剛建立的資料庫
USE ReportDb;
GO
CREATE TABLE [dbo].[ConvertibleBondDaily](
	[dataDate] [date] NOT NULL,
	[id] [nvarchar](max) NOT NULL,              -- "代號 (股票 ID)"
	[name] [nvarchar](max) NOT NULL,            -- "名稱 (股票名稱)"
	[trade_type] [nvarchar](2) NOT NULL,        -- "交易類型 (等價、議價等)"
	[closing_price] [decimal](10, 2) NULL,      -- "收市價"
	[change_price] [decimal](10, 2) NULL,       -- "漲跌"
	[open_price] [decimal](10, 2) NULL,         -- "開市價"
	[high_price] [decimal](10, 2) NULL,         -- "最高價"
    [low_price] [decimal](10, 2) NULL,          -- "最低價"
	[trade_count] [bigint] NULL,                -- "筆數 (交易筆數)"
	[unit_count] [bigint] NULL,                 -- "單位數 (交易單位)"
	[total_amount] [bigint] NULL,               -- "金額 (總交易額)"
	[avg_price] [decimal](10, 2) NULL,          -- "均價"
	[next_ref_price] [decimal](10, 2) NULL,     -- "明日參考價"
	[next_limit_up] [decimal](10, 2) NULL,      -- "明日漲停價"
	[next_limit_down] [decimal](10, 2) NULL     -- "明日跌停價"
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

GO
CREATE TABLE [dbo].[Date](
	[index] [int] IDENTITY(1,1) NOT NULL,
	[Date] [date] NOT NULL,
	[Day] [nvarchar](1) NULL
) ON [PRIMARY]
GO
