SET NOCOUNT ON;
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;

IF DB_NAME() NOT IN (N'sampledb', N'NutriPathDB')
    THROW 51000, 'Refusing migration: the current database must be sampledb or NutriPathDB.', 1;

IF UPPER(CAST(SERVERPROPERTY('MachineName') AS nvarchar(128))) <> N'IMENE'
    THROW 51001, 'Refusing migration: the SQL Server machine must be IMENE.', 1;

IF OBJECT_ID(N'dbo.FoodItems', N'U') IS NULL
   OR OBJECT_ID(N'dbo.UserProfiles', N'U') IS NULL
   OR OBJECT_ID(N'dbo.DietPlans', N'U') IS NULL
   OR OBJECT_ID(N'dbo.weight_history', N'U') IS NULL
    THROW 51002, 'Refusing migration: one or more expected existing tables are missing.', 1;

BEGIN TRANSACTION;

IF COL_LENGTH(N'dbo.UserProfiles', N'Intolerances') IS NULL
    ALTER TABLE dbo.UserProfiles ADD Intolerances nvarchar(max) NULL;
IF COL_LENGTH(N'dbo.UserProfiles', N'FoodsToAvoid') IS NULL
    ALTER TABLE dbo.UserProfiles ADD FoodsToAvoid nvarchar(max) NULL;
IF COL_LENGTH(N'dbo.UserProfiles', N'OtherDietaryRestrictions') IS NULL
    ALTER TABLE dbo.UserProfiles ADD OtherDietaryRestrictions nvarchar(max) NULL;

IF COL_LENGTH(N'dbo.DietPlans', N'IdempotencyKey') IS NULL
    ALTER TABLE dbo.DietPlans ADD IdempotencyKey varchar(64) NULL;

IF COL_LENGTH(N'dbo.weight_history', N'is_baseline') IS NULL
BEGIN
    ALTER TABLE dbo.weight_history
        ADD is_baseline bit NOT NULL
            CONSTRAINT DF_weight_history_is_baseline DEFAULT (0) WITH VALUES;
END;

IF OBJECT_ID(N'dbo.FoodSafetyMetadata', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FoodSafetyMetadata
    (
        FoodID int NOT NULL,
        Ingredients nvarchar(max) NULL,
        Allergens nvarchar(max) NULL,
        DietaryClassifications nvarchar(max) NULL,
        AnimalDerivedIngredients nvarchar(max) NULL,
        CrossContactWarnings nvarchar(max) NULL,
        VerificationSource nvarchar(max) NULL,
        IsVerified bit NOT NULL
            CONSTRAINT DF_FoodSafetyMetadata_IsVerified DEFAULT (0),
        IsVegetarian bit NULL,
        IsVegan bit NULL,
        ContainsEgg bit NULL,
        ContainsDairy bit NULL,
        ContainsHoney bit NULL,
        ContainsFish bit NULL,
        ContainsSeafood bit NULL,
        ContainsMeat bit NULL,
        VerifiedAt datetime2(7) NULL,
        CONSTRAINT PK_FoodSafetyMetadata PRIMARY KEY CLUSTERED (FoodID),
        CONSTRAINT FK_FoodSafetyMetadata_FoodItems
            FOREIGN KEY (FoodID) REFERENCES dbo.FoodItems (FoodID)
    );
END;

IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'Ingredients') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD Ingredients nvarchar(max) NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'Allergens') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD Allergens nvarchar(max) NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'DietaryClassifications') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD DietaryClassifications nvarchar(max) NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'AnimalDerivedIngredients') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD AnimalDerivedIngredients nvarchar(max) NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'CrossContactWarnings') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD CrossContactWarnings nvarchar(max) NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'VerificationSource') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD VerificationSource nvarchar(max) NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'IsVerified') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD IsVerified bit NOT NULL
        CONSTRAINT DF_FoodSafetyMetadata_IsVerified_Existing DEFAULT (0) WITH VALUES;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'IsVegetarian') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD IsVegetarian bit NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'IsVegan') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD IsVegan bit NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'ContainsEgg') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD ContainsEgg bit NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'ContainsDairy') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD ContainsDairy bit NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'ContainsHoney') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD ContainsHoney bit NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'ContainsFish') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD ContainsFish bit NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'ContainsSeafood') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD ContainsSeafood bit NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'ContainsMeat') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD ContainsMeat bit NULL;
IF COL_LENGTH(N'dbo.FoodSafetyMetadata', N'VerifiedAt') IS NULL
    ALTER TABLE dbo.FoodSafetyMetadata ADD VerifiedAt datetime2(7) NULL;

IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = N'FK_FoodSafetyMetadata_FoodItems'
      AND parent_object_id = OBJECT_ID(N'dbo.FoodSafetyMetadata')
)
    ALTER TABLE dbo.FoodSafetyMetadata WITH CHECK
        ADD CONSTRAINT FK_FoodSafetyMetadata_FoodItems
        FOREIGN KEY (FoodID) REFERENCES dbo.FoodItems (FoodID);

EXEC sys.sp_executesql N'
IF EXISTS (
    SELECT user_id
    FROM dbo.weight_history
    WHERE is_baseline = 1
    GROUP BY user_id
    HAVING COUNT(*) > 1
)
    THROW 51003, ''Multiple starting baselines exist for a user; resolve them before adding the uniqueness guard.'', 1;';

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.weight_history')
      AND name = N'UX_weight_history_UserBaseline'
)
    EXEC sys.sp_executesql N'
        CREATE UNIQUE INDEX UX_weight_history_UserBaseline
            ON dbo.weight_history (user_id)
            WHERE is_baseline = 1;';

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.DietPlans')
      AND name = N'UX_DietPlans_UserIdempotencyKey'
)
    EXEC sys.sp_executesql N'
        CREATE UNIQUE INDEX UX_DietPlans_UserIdempotencyKey
            ON dbo.DietPlans (UserID, IdempotencyKey)
            WHERE IdempotencyKey IS NOT NULL;';

COMMIT TRANSACTION;
