SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'NutriPathDB'
    THROW 51000, 'Refusing migration: the current database must be NutriPathDB.', 1;

IF OBJECT_ID(N'dbo.UserProfiles', N'U') IS NULL
    THROW 51001, 'Refusing migration: dbo.UserProfiles does not exist.', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    IF COL_LENGTH(N'dbo.UserProfiles', N'Intolerances') IS NULL
        ALTER TABLE dbo.UserProfiles ADD Intolerances nvarchar(max) NULL;
    IF COL_LENGTH(N'dbo.UserProfiles', N'FoodsToAvoid') IS NULL
        ALTER TABLE dbo.UserProfiles ADD FoodsToAvoid nvarchar(max) NULL;
    IF COL_LENGTH(N'dbo.UserProfiles', N'OtherDietaryRestrictions') IS NULL
        ALTER TABLE dbo.UserProfiles ADD OtherDietaryRestrictions nvarchar(max) NULL;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
