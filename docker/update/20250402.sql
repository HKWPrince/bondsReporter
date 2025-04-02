
-- 新增ConvertibleBondDaily_upload_log 
-- 儲存最近一筆上傳日期

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConvertibleBondDaily_upload_log](
	[index] [int] IDENTITY(1,1) NOT NULL,
	[Date] [nvarchar](10) NOT NULL,
	[Day] [datetime] NOT NULL
) ON [PRIMARY]

GO
