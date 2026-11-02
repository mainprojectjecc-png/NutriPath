SET XACT_ABORT ON;

IF COL_LENGTH('dbo.FoodItems', 'CatalogID') IS NULL
    THROW 51000, 'dbo.FoodItems.CatalogID is required; review a schema change separately.', 1;

DECLARE @FoodCatalog TABLE (
    CatalogID varchar(80) NOT NULL PRIMARY KEY,
    FoodName nvarchar(150) NOT NULL,
    Category nvarchar(50) NOT NULL,
    Calories decimal(8, 2) NOT NULL,
    Protein decimal(8, 2) NOT NULL,
    Carbs decimal(8, 2) NOT NULL,
    Fat decimal(8, 2) NOT NULL,
    ServingSize nvarchar(50) NOT NULL
);

INSERT INTO @FoodCatalog (
    CatalogID, FoodName, Category, Calories, Protein, Carbs, Fat, ServingSize
)
VALUES
    ('idli', N'Idli', N'Breakfast', 58, 2, 12, 0.2, N'1 piece'),
    ('masala-dosa', N'Masala dosa', N'Breakfast', 290, 6, 44, 10, N'1 dosa'),
    ('poha', N'Poha', N'Breakfast', 250, 5, 42, 7, N'1 bowl'),
    ('upma', N'Upma', N'Breakfast', 220, 6, 38, 5, N'1 bowl'),
    ('plain-dosa', N'Plain dosa', N'Breakfast', 168, 4, 29, 4, N'1 dosa'),
    ('paratha', N'Aloo paratha', N'Breakfast', 260, 6, 38, 9, N'1 paratha'),
    ('besan-chilla', N'Besan chilla', N'Breakfast', 180, 9, 22, 6, N'1 chilla'),
    ('oats', N'Oats porridge', N'Breakfast', 160, 6, 27, 4, N'1 bowl'),
    ('chapati', N'Chapati', N'Lunch', 120, 3, 20, 3, N'1 piece'),
    ('brown-rice', N'Cooked brown rice', N'Lunch', 165, 4, 35, 1.4, N'1 cup'),
    ('white-rice', N'Cooked white rice', N'Lunch', 195, 4, 43, 0.4, N'1 cup'),
    ('dal', N'Dal tadka', N'Lunch', 190, 11, 25, 5, N'1 bowl'),
    ('rajma', N'Rajma curry', N'Lunch', 210, 12, 32, 4, N'1 bowl'),
    ('chole', N'Chole', N'Lunch', 240, 12, 34, 7, N'1 bowl'),
    ('paneer', N'Paneer bhurji', N'Lunch', 265, 18, 9, 18, N'1 bowl'),
    ('palak-paneer', N'Palak paneer', N'Lunch', 280, 15, 14, 19, N'1 bowl'),
    ('mixed-veg', N'Mixed vegetable sabzi', N'Lunch', 140, 4, 19, 6, N'1 bowl'),
    ('curd', N'Plain curd', N'Lunch', 92, 5, 7, 5, N'1 bowl'),
    ('samosa', N'Samosa', N'Snacks', 190, 4, 23, 9, N'1 piece'),
    ('dhokla', N'Dhokla', N'Snacks', 160, 7, 25, 4, N'2 pieces'),
    ('roasted-chana', N'Roasted chana', N'Snacks', 120, 6, 18, 2, N'1 handful'),
    ('makhana', N'Roasted makhana', N'Snacks', 90, 3, 17, 1, N'1 bowl'),
    ('banana', N'Banana', N'Snacks', 105, 1.3, 27, 0.4, N'1 medium'),
    ('apple', N'Apple', N'Snacks', 95, 0.5, 25, 0.3, N'1 medium'),
    ('almonds', N'Almonds', N'Snacks', 164, 6, 6, 14, N'1 handful'),
    ('sprouts', N'Moong sprouts chaat', N'Snacks', 130, 10, 22, 1, N'1 bowl'),
    ('chicken-curry', N'Chicken curry', N'Dinner', 290, 27, 8, 16, N'1 bowl'),
    ('grilled-chicken', N'Grilled chicken', N'Dinner', 248, 39, 0, 9, N'1 serving'),
    ('tofu', N'Tofu bhurji', N'Dinner', 190, 18, 8, 10, N'1 bowl'),
    ('khichdi', N'Moong dal khichdi', N'Dinner', 260, 11, 45, 5, N'1 bowl'),
    ('roti', N'Whole wheat roti', N'Dinner', 110, 3.5, 22, 1, N'1 piece'),
    ('raita', N'Vegetable raita', N'Dinner', 100, 5, 10, 4, N'1 bowl');

BEGIN TRANSACTION;

IF EXISTS (
    SELECT 1
    FROM @FoodCatalog AS source
    JOIN dbo.FoodItems AS existing WITH (UPDLOCK, HOLDLOCK)
        ON existing.CatalogID = source.CatalogID
        OR existing.FoodName = source.FoodName
    WHERE ISNULL(existing.CatalogID, '') <> source.CatalogID
        OR existing.FoodName <> source.FoodName
        OR ISNULL(existing.Category, '') <> source.Category
        OR existing.Calories <> source.Calories
        OR existing.Protein <> source.Protein
        OR existing.Carbs <> source.Carbs
        OR existing.Fat <> source.Fat
        OR ISNULL(existing.ServingSize, '') <> source.ServingSize
)
BEGIN
    ROLLBACK TRANSACTION;
    THROW 51001, 'A catalog ID or food name already exists with different catalog data; review before seeding.', 1;
END;

INSERT INTO dbo.FoodItems (
    CatalogID, FoodName, Category, Calories, Protein, Carbs, Fat, ServingSize, IsActive, CreatedAt
)
SELECT
    source.CatalogID,
    source.FoodName,
    source.Category,
    source.Calories,
    source.Protein,
    source.Carbs,
    source.Fat,
    source.ServingSize,
    1,
    SYSUTCDATETIME()
FROM @FoodCatalog AS source
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.FoodItems AS existing WITH (UPDLOCK, HOLDLOCK)
    WHERE existing.CatalogID = source.CatalogID
);

COMMIT TRANSACTION;
