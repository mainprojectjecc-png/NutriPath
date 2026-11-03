SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'NutriPathDB'
    THROW 51000, 'Refusing migration: the current database must be NutriPathDB.', 1;

IF OBJECT_ID(N'dbo.weight_history', N'U') IS NULL
    THROW 51001, 'Refusing migration: dbo.weight_history does not exist.', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    IF COL_LENGTH(N'dbo.weight_history', N'is_baseline') IS NULL
    BEGIN
        ALTER TABLE dbo.weight_history
            ADD is_baseline bit NOT NULL
                CONSTRAINT DF_weight_history_is_baseline DEFAULT (0) WITH VALUES;
    END;

    EXEC sys.sp_executesql N'
        IF EXISTS (
            SELECT user_id
            FROM dbo.weight_history
            WHERE is_baseline = 1
            GROUP BY user_id
            HAVING COUNT(*) > 1
        )
            THROW 51002, ''Multiple starting baselines exist for a user; resolve them before adding the uniqueness guard.'', 1;

        IF NOT EXISTS (
            SELECT 1
            FROM sys.indexes
            WHERE object_id = OBJECT_ID(N''dbo.weight_history'')
              AND name = N''UX_weight_history_UserBaseline''
        )
            CREATE UNIQUE INDEX UX_weight_history_UserBaseline
                ON dbo.weight_history (user_id)
                WHERE is_baseline = 1;';

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
