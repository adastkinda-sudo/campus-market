-- Campus Market - SQL Server 版数据库脚本
-- 使用方法：在 SSMS 中新建数据库（例如 CampusMarket），然后执行本脚本。
-- 注意：本脚本假设使用 SQL Server 2016 或更高版本（支持 DROP IF EXISTS）。

USE [CampusMarket];
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- ============================================================
-- 1. 删除旧对象（如果存在）
-- ============================================================
DROP TRIGGER IF EXISTS trg_review_credit;
DROP TRIGGER IF EXISTS trg_review_participant;
DROP TRIGGER IF EXISTS trg_review_requires_success;
DROP TRIGGER IF EXISTS trg_order_update_cancel;
DROP TRIGGER IF EXISTS trg_order_update_success;
DROP TRIGGER IF EXISTS trg_order_create_lock_item;
DROP TRIGGER IF EXISTS trg_order_no_self_buy;
GO

DROP VIEW IF EXISTS V_Risky_User;
DROP VIEW IF EXISTS V_Order_Summary;
DROP VIEW IF EXISTS V_Item_Detail;
GO

DROP INDEX IF EXISTS idx_notification_user_read ON Notification;
DROP INDEX IF EXISTS idx_favorite_user ON Favorite;
DROP INDEX IF EXISTS idx_report_status ON Report;
DROP INDEX IF EXISTS idx_message_item_time ON Message;
DROP INDEX IF EXISTS idx_order_buyer ON OrderSheet;
DROP INDEX IF EXISTS idx_item_title ON Item;
DROP INDEX IF EXISTS idx_item_status_category ON Item;
DROP INDEX IF EXISTS idx_order_active_item ON OrderSheet;
GO

DROP TABLE IF EXISTS Report;
DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS Message;
DROP TABLE IF EXISTS OrderSheet;
DROP TABLE IF EXISTS Wanted;
DROP TABLE IF EXISTS Favorite;
DROP TABLE IF EXISTS Item;
DROP TABLE IF EXISTS Announcement;
DROP TABLE IF EXISTS Notification;
DROP TABLE IF EXISTS Location;
DROP TABLE IF EXISTS Category;
DROP TABLE IF EXISTS [User];
DROP TABLE IF EXISTS Admin;
GO

-- ============================================================
-- 2. 创建表
-- ============================================================
CREATE TABLE Admin (
    adminNo INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(50) NOT NULL UNIQUE,
    [password] NVARCHAR(255) NOT NULL,
    createdTime DATETIME2 NOT NULL DEFAULT GETDATE()
);
GO

CREATE TABLE [User] (
    userNo INT PRIMARY KEY IDENTITY(1,1),
    studentNo NVARCHAR(50) NOT NULL UNIQUE,
    realName NVARCHAR(50) NOT NULL,
    [password] NVARCHAR(255) NOT NULL,
    nickname NVARCHAR(50) NOT NULL,
    userType NVARCHAR(20) NOT NULL DEFAULT N'学生'
        CHECK (userType IN (N'学生', N'教职工', N'校友')),
    phone NVARCHAR(20),
    wechat NVARCHAR(50),
    authStatus NVARCHAR(20) NOT NULL DEFAULT N'未认证'
        CHECK (authStatus IN (N'未认证', N'待审核', N'已认证', N'认证驳回')),
    creditScore INT NOT NULL DEFAULT 100 CHECK (creditScore BETWEEN 0 AND 120),
    [status] NVARCHAR(20) NOT NULL DEFAULT N'正常' CHECK ([status] IN (N'正常', N'封禁')),
    registerTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    adminNo INT,
    FOREIGN KEY (adminNo) REFERENCES Admin(adminNo)
);
GO

CREATE TABLE Category (
    categoryNo INT PRIMARY KEY IDENTITY(1,1),
    categoryName NVARCHAR(50) NOT NULL,
    parentCategoryNo INT,
    FOREIGN KEY (parentCategoryNo) REFERENCES Category(categoryNo) ON DELETE SET NULL,
    UNIQUE (categoryName, parentCategoryNo)
);
GO

CREATE TABLE Location (
    locationNo INT PRIMARY KEY IDENTITY(1,1),
    locationName NVARCHAR(50) NOT NULL,
    campusName NVARCHAR(50) NOT NULL,
    UNIQUE (locationName, campusName)
);
GO

CREATE TABLE Announcement (
    announcementNo INT PRIMARY KEY IDENTITY(1,1),
    adminNo INT NOT NULL,
    title NVARCHAR(200) NOT NULL,
    content NVARCHAR(MAX) NOT NULL,
    publishTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (adminNo) REFERENCES Admin(adminNo)
);
GO

CREATE TABLE Notification (
    notificationNo INT PRIMARY KEY IDENTITY(1,1),
    userNo INT NOT NULL,
    title NVARCHAR(200) NOT NULL,
    content NVARCHAR(MAX) NOT NULL,
    linkType NVARCHAR(50),
    linkNo INT,
    isRead INT NOT NULL DEFAULT 0 CHECK (isRead IN (0, 1)),
    createTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (userNo) REFERENCES [User](userNo)
);
GO

CREATE TABLE Item (
    itemNo INT PRIMARY KEY IDENTITY(1,1),
    sellerNo INT NOT NULL,
    categoryNo INT NOT NULL,
    title NVARCHAR(200) NOT NULL,
    [description] NVARCHAR(MAX) NOT NULL,
    originalPrice DECIMAL(10,2) NOT NULL CHECK (originalPrice >= 0),
    sellPrice DECIMAL(10,2) NOT NULL CHECK (sellPrice >= 0),
    [condition] NVARCHAR(20) NOT NULL
        CHECK ([condition] IN (N'全新', N'九成新', N'八成新', N'七成新', N'使用痕迹明显')),
    imageUrl NVARCHAR(500),
    viewCount INT NOT NULL DEFAULT 0 CHECK (viewCount >= 0),
    [status] NVARCHAR(20) NOT NULL DEFAULT N'在售'
        CHECK ([status] IN (N'在售', N'交易中', N'已售出', N'已下架')),
    visible INT NOT NULL DEFAULT 1 CHECK (visible IN (0, 1)),
    publishTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (sellerNo) REFERENCES [User](userNo),
    FOREIGN KEY (categoryNo) REFERENCES Category(categoryNo)
);
GO

CREATE TABLE Favorite (
    favoriteNo INT PRIMARY KEY IDENTITY(1,1),
    userNo INT NOT NULL,
    itemNo INT NOT NULL,
    createTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (userNo) REFERENCES [User](userNo),
    FOREIGN KEY (itemNo) REFERENCES Item(itemNo),
    UNIQUE (userNo, itemNo)
);
GO

CREATE TABLE Wanted (
    wantedNo INT PRIMARY KEY IDENTITY(1,1),
    buyerNo INT NOT NULL,
    categoryNo INT,
    title NVARCHAR(200) NOT NULL,
    [description] NVARCHAR(MAX) NOT NULL,
    expectedPrice DECIMAL(10,2) CHECK (expectedPrice IS NULL OR expectedPrice >= 0),
    [status] NVARCHAR(20) NOT NULL DEFAULT N'有效' CHECK ([status] IN (N'有效', N'已关闭')),
    publishTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (buyerNo) REFERENCES [User](userNo),
    FOREIGN KEY (categoryNo) REFERENCES Category(categoryNo) ON DELETE SET NULL
);
GO

CREATE TABLE OrderSheet (
    orderNo INT PRIMARY KEY IDENTITY(1,1),
    buyerNo INT NOT NULL,
    itemNo INT NOT NULL,
    locationNo INT NOT NULL,
    orderAmount DECIMAL(10,2) NOT NULL CHECK (orderAmount >= 0),
    meetTime DATETIME2 NOT NULL,
    orderStatus NVARCHAR(20) NOT NULL DEFAULT N'待卖家确认'
        CHECK (orderStatus IN (N'待卖家确认', N'待面交', N'交易成功', N'已取消')),
    createTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    finishTime DATETIME2,
    FOREIGN KEY (buyerNo) REFERENCES [User](userNo),
    FOREIGN KEY (itemNo) REFERENCES Item(itemNo),
    FOREIGN KEY (locationNo) REFERENCES Location(locationNo)
);
GO

CREATE TABLE Message (
    messageNo INT PRIMARY KEY IDENTITY(1,1),
    itemNo INT NOT NULL,
    userNo INT NOT NULL,
    content NVARCHAR(MAX) NOT NULL,
    msgTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    parentMessageNo INT,
    FOREIGN KEY (itemNo) REFERENCES Item(itemNo),
    FOREIGN KEY (userNo) REFERENCES [User](userNo),
    FOREIGN KEY (parentMessageNo) REFERENCES Message(messageNo) ON DELETE SET NULL
);
GO

CREATE TABLE Review (
    reviewNo INT PRIMARY KEY IDENTITY(1,1),
    orderNo INT NOT NULL,
    reviewerNo INT NOT NULL,
    revieweeNo INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    content NVARCHAR(MAX) NOT NULL,
    reviewTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (orderNo) REFERENCES OrderSheet(orderNo),
    FOREIGN KEY (reviewerNo) REFERENCES [User](userNo),
    FOREIGN KEY (revieweeNo) REFERENCES [User](userNo),
    UNIQUE (orderNo, reviewerNo)
);
GO

CREATE TABLE Report (
    reportNo INT PRIMARY KEY IDENTITY(1,1),
    reporterNo INT NOT NULL,
    targetType NVARCHAR(20) NOT NULL CHECK (targetType IN (N'物品', N'用户')),
    targetNo INT NOT NULL,
    reason NVARCHAR(MAX) NOT NULL,
    reportStatus NVARCHAR(20) NOT NULL DEFAULT N'未处理' CHECK (reportStatus IN (N'未处理', N'已处理')),
    handleResult NVARCHAR(MAX),
    handleAdminNo INT,
    createTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    handleTime DATETIME2,
    FOREIGN KEY (reporterNo) REFERENCES [User](userNo),
    FOREIGN KEY (handleAdminNo) REFERENCES Admin(adminNo)
);
GO

-- ============================================================
-- 3. 索引
-- ============================================================
CREATE UNIQUE INDEX idx_order_active_item
ON OrderSheet(itemNo)
WHERE orderStatus IN (N'待卖家确认', N'待面交', N'交易成功');
GO

CREATE INDEX idx_item_status_category ON Item([status], categoryNo);
CREATE INDEX idx_item_title ON Item(title);
CREATE INDEX idx_order_buyer ON OrderSheet(buyerNo, orderStatus);
CREATE INDEX idx_message_item_time ON Message(itemNo, msgTime);
CREATE INDEX idx_report_status ON Report(reportStatus);
CREATE INDEX idx_favorite_user ON Favorite(userNo, createTime);
CREATE INDEX idx_notification_user_read ON Notification(userNo, isRead, createTime);
GO

-- ============================================================
-- 4. 触发器
-- ============================================================
-- 4.1 禁止买家购买自己的物品
CREATE TRIGGER trg_order_no_self_buy
ON OrderSheet
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted o
        JOIN Item i ON i.itemNo = o.itemNo
        WHERE i.sellerNo = o.buyerNo
    )
    BEGIN
        THROW 50001, N'买家不能购买自己发布的物品', 1;
    END
END;
GO

-- 4.2 创建订单后锁定物品状态为“交易中”
CREATE TRIGGER trg_order_create_lock_item
ON OrderSheet
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Item
    SET [status] = N'交易中'
    FROM Item i
    JOIN inserted o ON o.itemNo = i.itemNo
    WHERE o.orderStatus IN (N'待卖家确认', N'待面交');
END;
GO

-- 4.3 订单交易成功后物品状态变为“已售出”
CREATE TRIGGER trg_order_update_success
ON OrderSheet
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Item
    SET [status] = N'已售出'
    FROM Item i
    JOIN inserted o ON o.itemNo = i.itemNo
    WHERE o.orderStatus = N'交易成功';
END;
GO

-- 4.4 订单取消后恢复物品状态为“在售”（交易成功取消除外）
CREATE TRIGGER trg_order_update_cancel
ON OrderSheet
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Item
    SET [status] = N'在售'
    FROM Item i
    JOIN inserted o ON o.itemNo = i.itemNo
    JOIN deleted d ON d.orderNo = o.orderNo
    WHERE o.orderStatus = N'已取消'
      AND d.orderStatus <> N'交易成功'
      AND i.[status] = N'交易中';
END;
GO

-- 4.5 只有交易成功的订单才能评价
CREATE TRIGGER trg_review_requires_success
ON Review
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted r
        JOIN OrderSheet o ON o.orderNo = r.orderNo
        WHERE o.orderStatus <> N'交易成功'
    )
    BEGIN
        THROW 50002, N'只有交易成功的订单才能评价', 1;
    END
END;
GO

-- 4.6 评价人必须是订单买家或卖家
CREATE TRIGGER trg_review_participant
ON Review
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted r
        JOIN OrderSheet o ON o.orderNo = r.orderNo
        JOIN Item i ON i.itemNo = o.itemNo
        WHERE NOT (
            (r.reviewerNo = o.buyerNo AND r.revieweeNo = i.sellerNo)
            OR
            (r.reviewerNo = i.sellerNo AND r.revieweeNo = o.buyerNo)
        )
    )
    BEGIN
        THROW 50003, N'评价人必须是订单买家或卖家', 1;
    END
END;
GO

-- 4.7 评价后自动更新被评价人信用积分
CREATE TRIGGER trg_review_credit
ON Review
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE [User]
    SET creditScore = CASE
        WHEN creditScore + (i.rating - 3) * 2 > 120 THEN 120
        WHEN creditScore + (i.rating - 3) * 2 < 0 THEN 0
        ELSE creditScore + (i.rating - 3) * 2
    END
    FROM [User] u
    JOIN inserted i ON i.revieweeNo = u.userNo;
END;
GO

-- ============================================================
-- 5. 视图
-- ============================================================
CREATE VIEW V_Item_Detail AS
SELECT
    i.itemNo,
    i.sellerNo,
    u.nickname AS sellerName,
    u.realName AS sellerRealName,
    u.userType AS sellerUserType,
    u.creditScore,
    u.authStatus AS sellerAuthStatus,
    i.categoryNo,
    c.categoryName,
    c.parentCategoryNo,
    pc.categoryName AS parentCategoryName,
    i.title,
    i.[description],
    i.originalPrice,
    i.sellPrice,
    i.[condition],
    i.imageUrl,
    i.viewCount,
    (SELECT COUNT(*) FROM Favorite f WHERE f.itemNo = i.itemNo) AS favoriteCount,
    i.[status],
    i.visible,
    i.publishTime
FROM Item i
JOIN [User] u ON u.userNo = i.sellerNo
JOIN Category c ON c.categoryNo = i.categoryNo
LEFT JOIN Category pc ON pc.categoryNo = c.parentCategoryNo;
GO

CREATE VIEW V_Order_Summary AS
SELECT
    o.orderNo,
    o.buyerNo,
    bu.nickname AS buyerName,
    i.sellerNo,
    su.nickname AS sellerName,
    o.itemNo,
    i.title AS itemTitle,
    i.imageUrl,
    i.[status] AS itemStatus,
    o.locationNo,
    l.locationName,
    l.campusName,
    o.orderAmount,
    o.meetTime,
    o.orderStatus,
    o.createTime,
    o.finishTime
FROM OrderSheet o
JOIN [User] bu ON bu.userNo = o.buyerNo
JOIN Item i ON i.itemNo = o.itemNo
JOIN [User] su ON su.userNo = i.sellerNo
JOIN Location l ON l.locationNo = o.locationNo;
GO

CREATE VIEW V_Risky_User AS
WITH report_count AS (
    SELECT userNo, SUM(reportCount) AS totalReports
    FROM (
        SELECT targetNo AS userNo, COUNT(*) AS reportCount
        FROM Report
        WHERE targetType = N'用户'
        GROUP BY targetNo
        UNION ALL
        SELECT i.sellerNo AS userNo, COUNT(*) AS reportCount
        FROM Report r
        JOIN Item i ON r.targetType = N'物品' AND r.targetNo = i.itemNo
        GROUP BY i.sellerNo
    ) t
    GROUP BY userNo
)
SELECT
    u.userNo,
    u.studentNo,
    u.realName,
    u.nickname,
    u.userType,
    u.phone,
    u.authStatus,
    u.creditScore,
    u.[status],
    COALESCE(rc.totalReports, 0) AS reportCount
FROM [User] u
LEFT JOIN report_count rc ON rc.userNo = u.userNo
WHERE u.creditScore < 70 OR COALESCE(rc.totalReports, 0) >= 2 OR u.[status] = N'封禁';
GO

-- ============================================================
-- 6. 演示数据
-- ============================================================
INSERT INTO Admin(username, [password])
VALUES (N'admin', N'4f88518261f305fb2d4eed5df6b9d2d03f074bcecda7912a919e50bad36a3f0d');
GO

DECLARE @adminNo INT = SCOPE_IDENTITY();

INSERT INTO [User](studentNo, realName, [password], nickname, userType, phone, wechat, authStatus, creditScore, adminNo)
VALUES
    (N'24010001', N'张一凡', N'56f1c541a21d3c7a40b4eda7ce4a310e63abb1f9bf06758f412bd014726c52a1', N'一凡同学', N'学生', N'13800010001', N'zhang_yf', N'已认证', 98, @adminNo),
    (N'24010002', N'李思雨', N'56f1c541a21d3c7a40b4eda7ce4a310e63abb1f9bf06758f412bd014726c52a1', N'雨天出清', N'学生', N'13800010002', N'lisi_yu', N'已认证', 92, @adminNo),
    (N'24010003', N'王明泽', N'56f1c541a21d3c7a40b4eda7ce4a310e63abb1f9bf06758f412bd014726c52a1', N'明泽', N'校友', N'13800010003', N'wmz_03', N'待审核', 88, @adminNo),
    (N'24010004', N'陈可', N'56f1c541a21d3c7a40b4eda7ce4a310e63abb1f9bf06758f412bd014726c52a1', N'可可买书', N'教职工', N'13800010004', N'chenke', N'已认证', 76, @adminNo);
GO

-- 插入分类（使用临时表保存自增 ID）
DECLARE @cat_book INT, @cat_book_major INT, @cat_book_exam INT;
DECLARE @cat_digital INT, @cat_digital_phone INT, @cat_digital_pc INT;
DECLARE @cat_life INT, @cat_vehicle INT;

INSERT INTO Category(categoryName, parentCategoryNo) VALUES (N'书籍教材', NULL); SET @cat_book = SCOPE_IDENTITY();
INSERT INTO Category(categoryName, parentCategoryNo) VALUES (N'专业课教材', @cat_book); SET @cat_book_major = SCOPE_IDENTITY();
INSERT INTO Category(categoryName, parentCategoryNo) VALUES (N'考试资料', @cat_book); SET @cat_book_exam = SCOPE_IDENTITY();
INSERT INTO Category(categoryName, parentCategoryNo) VALUES (N'数码产品', NULL); SET @cat_digital = SCOPE_IDENTITY();
INSERT INTO Category(categoryName, parentCategoryNo) VALUES (N'手机平板', @cat_digital); SET @cat_digital_phone = SCOPE_IDENTITY();
INSERT INTO Category(categoryName, parentCategoryNo) VALUES (N'电脑配件', @cat_digital); SET @cat_digital_pc = SCOPE_IDENTITY();
INSERT INTO Category(categoryName, parentCategoryNo) VALUES (N'生活用品', NULL); SET @cat_life = SCOPE_IDENTITY();
INSERT INTO Category(categoryName, parentCategoryNo) VALUES (N'代步工具', NULL); SET @cat_vehicle = SCOPE_IDENTITY();
GO

INSERT INTO Location(locationName, campusName)
VALUES
    (N'南门', N'主校区'),
    (N'一食堂门口', N'主校区'),
    (N'图书馆北门', N'主校区'),
    (N'信息楼大厅', N'主校区'),
    (N'东区宿舍楼下', N'东校区');
GO

DECLARE @adminNo INT;
SELECT @adminNo = adminNo FROM Admin WHERE username = N'admin';

INSERT INTO Announcement(adminNo, title, content)
VALUES
    (@adminNo, N'毕业季二手交易提醒', N'请优先选择校内公共区域面交，贵重物品当面确认成色和配件。'),
    (@adminNo, N'平台试运行公告', N'本系统用于数据库原理实验演示，已支持浏览、下单、留言、评价、举报和后台审核。');
GO

-- 插入物品（需要先查询用户和分类编号）
DECLARE @u1 INT, @u2 INT, @u4 INT;
SELECT @u1 = userNo FROM [User] WHERE studentNo = N'24010001';
SELECT @u2 = userNo FROM [User] WHERE studentNo = N'24010002';
SELECT @u4 = userNo FROM [User] WHERE studentNo = N'24010004';

DECLARE @cat_book_major INT, @cat_digital_pc INT, @cat_vehicle INT, @cat_life INT, @cat_book_exam INT;
SELECT @cat_book_major = categoryNo FROM Category WHERE categoryName = N'专业课教材' AND parentCategoryNo IS NOT NULL;
SELECT @cat_digital_pc = categoryNo FROM Category WHERE categoryName = N'电脑配件' AND parentCategoryNo IS NOT NULL;
SELECT @cat_vehicle = categoryNo FROM Category WHERE categoryName = N'代步工具' AND parentCategoryNo IS NULL;
SELECT @cat_life = categoryNo FROM Category WHERE categoryName = N'生活用品' AND parentCategoryNo IS NULL;
SELECT @cat_book_exam = categoryNo FROM Category WHERE categoryName = N'考试资料' AND parentCategoryNo IS NOT NULL;

INSERT INTO Item(sellerNo, categoryNo, title, [description], originalPrice, sellPrice, [condition], imageUrl)
VALUES
    (@u1, @cat_book_major, N'数据库系统概论第五版', N'课堂用书，内页有少量标注，适合数据库原理课程复习。', 59, 24, N'八成新', N'/assets/book.svg'),
    (@u2, @cat_digital_pc, N'罗技无线键鼠套装', N'键盘和鼠标均可正常使用，适合宿舍台式机或笔记本外接。', 139, 55, N'九成新', N'/assets/laptop.svg'),
    (@u1, @cat_vehicle, N'校园折叠自行车', N'车况稳定，适合通勤，支持信息楼附近看车。', 499, 180, N'七成新', N'/assets/bicycle.svg'),
    (@u4, @cat_life, N'宿舍小电煮锅', N'低功率小锅，已清洗，适合煮面和热汤。', 89, 30, N'八成新', N'/assets/kettle.svg');
GO

DECLARE @u2 INT;
DECLARE @cat_book_exam INT;
SELECT @u2 = userNo FROM [User] WHERE studentNo = N'24010002';
SELECT @cat_book_exam = categoryNo FROM Category WHERE categoryName = N'考试资料' AND parentCategoryNo IS NOT NULL;

INSERT INTO Wanted(buyerNo, categoryNo, title, [description], expectedPrice)
VALUES (@u2, @cat_book_exam, N'求购 Java 或数据库复习资料', N'希望是近两年的资料，最好有重点标注。', 35);
GO

-- 留言
DECLARE @u1 INT, @u2 INT, @itemDb INT, @parentNo INT;
SELECT @u1 = userNo FROM [User] WHERE studentNo = N'24010001';
SELECT @u2 = userNo FROM [User] WHERE studentNo = N'24010002';
SELECT @itemDb = itemNo FROM Item WHERE title LIKE N'数据库系统概论%';

INSERT INTO Message(itemNo, userNo, content)
VALUES (@itemDb, @u2, N'请问这本书配套习题册还在吗？');
SET @parentNo = SCOPE_IDENTITY();

INSERT INTO Message(itemNo, userNo, content, parentMessageNo)
VALUES (@itemDb, @u1, N'习题册不在了，只有教材本体。', @parentNo);
GO
