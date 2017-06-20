USE Polaris
GO
sp_change_users_login 'AUTO_FIX', 'sopac'
GRANT EXECUTE ON Polaris.Cat_GetBibHoldRequestCount TO sopac
GRANT EXECUTE ON Polaris.Circ_GetPatronReadingHistory TO sopac
USE PolarisTransactions
GO
sp_change_users_login 'AUTO_FIX', 'sopac'