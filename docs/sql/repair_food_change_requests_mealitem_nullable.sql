IF EXISTS (
    SELECT 1
    FROM sys.columns
    WHERE object_id = OBJECT_ID(N'[dbo].[FoodChangeRequests]')
      AND name = N'MealItemID'
      AND is_nullable = 0
)
BEGIN
    ALTER TABLE [dbo].[FoodChangeRequests]
    ALTER COLUMN [MealItemID] int NULL;
END;
