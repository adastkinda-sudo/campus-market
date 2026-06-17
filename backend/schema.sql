PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Admin (
    adminNo INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    createdTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS User (
    userNo INTEGER PRIMARY KEY AUTOINCREMENT,
    studentNo TEXT NOT NULL UNIQUE,
    realName TEXT NOT NULL,
    password TEXT NOT NULL,
    nickname TEXT NOT NULL,
    userType TEXT NOT NULL DEFAULT '学生'
        CHECK (userType IN ('学生', '教职工', '校友')),
    phone TEXT,
    wechat TEXT,
    authStatus TEXT NOT NULL DEFAULT '未认证'
        CHECK (authStatus IN ('未认证', '待审核', '已认证', '认证驳回')),
    creditScore INTEGER NOT NULL DEFAULT 100 CHECK (creditScore BETWEEN 0 AND 120),
    status TEXT NOT NULL DEFAULT '正常' CHECK (status IN ('正常', '封禁')),
    registerTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    adminNo INTEGER,
    FOREIGN KEY (adminNo) REFERENCES Admin(adminNo)
);

CREATE TABLE IF NOT EXISTS Category (
    categoryNo INTEGER PRIMARY KEY AUTOINCREMENT,
    categoryName TEXT NOT NULL,
    parentCategoryNo INTEGER,
    FOREIGN KEY (parentCategoryNo) REFERENCES Category(categoryNo) ON DELETE SET NULL,
    UNIQUE (categoryName, parentCategoryNo)
);

CREATE TABLE IF NOT EXISTS Location (
    locationNo INTEGER PRIMARY KEY AUTOINCREMENT,
    locationName TEXT NOT NULL,
    campusName TEXT NOT NULL,
    UNIQUE (locationName, campusName)
);

CREATE TABLE IF NOT EXISTS Announcement (
    announcementNo INTEGER PRIMARY KEY AUTOINCREMENT,
    adminNo INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    publishTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (adminNo) REFERENCES Admin(adminNo)
);

CREATE TABLE IF NOT EXISTS Notification (
    notificationNo INTEGER PRIMARY KEY AUTOINCREMENT,
    userNo INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    linkType TEXT,
    linkNo INTEGER,
    isRead INTEGER NOT NULL DEFAULT 0 CHECK (isRead IN (0, 1)),
    createTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userNo) REFERENCES User(userNo)
);

CREATE TABLE IF NOT EXISTS Item (
    itemNo INTEGER PRIMARY KEY AUTOINCREMENT,
    sellerNo INTEGER NOT NULL,
    categoryNo INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    originalPrice REAL NOT NULL CHECK (originalPrice >= 0),
    sellPrice REAL NOT NULL CHECK (sellPrice >= 0),
    condition TEXT NOT NULL CHECK (condition IN ('全新', '九成新', '八成新', '七成新', '使用痕迹明显')),
    imageUrl TEXT,
    viewCount INTEGER NOT NULL DEFAULT 0 CHECK (viewCount >= 0),
    status TEXT NOT NULL DEFAULT '在售'
        CHECK (status IN ('在售', '交易中', '已售出', '已下架')),
    visible INTEGER NOT NULL DEFAULT 1 CHECK (visible IN (0, 1)),
    publishTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sellerNo) REFERENCES User(userNo),
    FOREIGN KEY (categoryNo) REFERENCES Category(categoryNo)
);

CREATE TABLE IF NOT EXISTS Favorite (
    favoriteNo INTEGER PRIMARY KEY AUTOINCREMENT,
    userNo INTEGER NOT NULL,
    itemNo INTEGER NOT NULL,
    createTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userNo) REFERENCES User(userNo),
    FOREIGN KEY (itemNo) REFERENCES Item(itemNo),
    UNIQUE (userNo, itemNo)
);

CREATE TABLE IF NOT EXISTS Wanted (
    wantedNo INTEGER PRIMARY KEY AUTOINCREMENT,
    buyerNo INTEGER NOT NULL,
    categoryNo INTEGER,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    expectedPrice REAL CHECK (expectedPrice IS NULL OR expectedPrice >= 0),
    status TEXT NOT NULL DEFAULT '有效' CHECK (status IN ('有效', '已关闭')),
    publishTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyerNo) REFERENCES User(userNo),
    FOREIGN KEY (categoryNo) REFERENCES Category(categoryNo) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS OrderSheet (
    orderNo INTEGER PRIMARY KEY AUTOINCREMENT,
    buyerNo INTEGER NOT NULL,
    itemNo INTEGER NOT NULL,
    locationNo INTEGER NOT NULL,
    orderAmount REAL NOT NULL CHECK (orderAmount >= 0),
    meetTime TEXT NOT NULL,
    orderStatus TEXT NOT NULL DEFAULT '待卖家确认'
        CHECK (orderStatus IN ('待卖家确认', '待面交', '交易成功', '已取消')),
    createTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finishTime TEXT,
    FOREIGN KEY (buyerNo) REFERENCES User(userNo),
    FOREIGN KEY (itemNo) REFERENCES Item(itemNo),
    FOREIGN KEY (locationNo) REFERENCES Location(locationNo)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_order_active_item
ON OrderSheet(itemNo)
WHERE orderStatus IN ('待卖家确认', '待面交', '交易成功');

CREATE TABLE IF NOT EXISTS Message (
    messageNo INTEGER PRIMARY KEY AUTOINCREMENT,
    itemNo INTEGER NOT NULL,
    userNo INTEGER NOT NULL,
    content TEXT NOT NULL,
    msgTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    parentMessageNo INTEGER,
    FOREIGN KEY (itemNo) REFERENCES Item(itemNo),
    FOREIGN KEY (userNo) REFERENCES User(userNo),
    FOREIGN KEY (parentMessageNo) REFERENCES Message(messageNo) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Review (
    reviewNo INTEGER PRIMARY KEY AUTOINCREMENT,
    orderNo INTEGER NOT NULL,
    reviewerNo INTEGER NOT NULL,
    revieweeNo INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    content TEXT NOT NULL,
    reviewTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (orderNo) REFERENCES OrderSheet(orderNo),
    FOREIGN KEY (reviewerNo) REFERENCES User(userNo),
    FOREIGN KEY (revieweeNo) REFERENCES User(userNo),
    UNIQUE (orderNo, reviewerNo)
);

CREATE TABLE IF NOT EXISTS Report (
    reportNo INTEGER PRIMARY KEY AUTOINCREMENT,
    reporterNo INTEGER NOT NULL,
    targetType TEXT NOT NULL CHECK (targetType IN ('物品', '用户')),
    targetNo INTEGER NOT NULL,
    reason TEXT NOT NULL,
    reportStatus TEXT NOT NULL DEFAULT '未处理' CHECK (reportStatus IN ('未处理', '已处理')),
    handleResult TEXT,
    handleAdminNo INTEGER,
    createTime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    handleTime TEXT,
    FOREIGN KEY (reporterNo) REFERENCES User(userNo),
    FOREIGN KEY (handleAdminNo) REFERENCES Admin(adminNo)
);

CREATE INDEX IF NOT EXISTS idx_item_status_category ON Item(status, categoryNo);
CREATE INDEX IF NOT EXISTS idx_item_title ON Item(title);
CREATE INDEX IF NOT EXISTS idx_order_buyer ON OrderSheet(buyerNo, orderStatus);
CREATE INDEX IF NOT EXISTS idx_message_item_time ON Message(itemNo, msgTime);
CREATE INDEX IF NOT EXISTS idx_report_status ON Report(reportStatus);
CREATE INDEX IF NOT EXISTS idx_favorite_user ON Favorite(userNo, createTime);
CREATE INDEX IF NOT EXISTS idx_notification_user_read ON Notification(userNo, isRead, createTime);

CREATE TRIGGER IF NOT EXISTS trg_order_no_self_buy
BEFORE INSERT ON OrderSheet
WHEN (SELECT sellerNo FROM Item WHERE itemNo = NEW.itemNo) = NEW.buyerNo
BEGIN
    SELECT RAISE(ABORT, '买家不能购买自己发布的物品');
END;

CREATE TRIGGER IF NOT EXISTS trg_order_create_lock_item
AFTER INSERT ON OrderSheet
WHEN NEW.orderStatus IN ('待卖家确认', '待面交')
BEGIN
    UPDATE Item SET status = '交易中' WHERE itemNo = NEW.itemNo;
END;

CREATE TRIGGER IF NOT EXISTS trg_order_update_success
AFTER UPDATE OF orderStatus ON OrderSheet
WHEN NEW.orderStatus = '交易成功'
BEGIN
    UPDATE Item SET status = '已售出' WHERE itemNo = NEW.itemNo;
END;

CREATE TRIGGER IF NOT EXISTS trg_order_update_cancel
AFTER UPDATE OF orderStatus ON OrderSheet
WHEN NEW.orderStatus = '已取消' AND OLD.orderStatus <> '交易成功'
BEGIN
    UPDATE Item SET status = '在售' WHERE itemNo = NEW.itemNo AND status = '交易中';
END;

CREATE TRIGGER IF NOT EXISTS trg_review_requires_success
BEFORE INSERT ON Review
WHEN (SELECT orderStatus FROM OrderSheet WHERE orderNo = NEW.orderNo) <> '交易成功'
BEGIN
    SELECT RAISE(ABORT, '只有交易成功的订单才能评价');
END;

CREATE TRIGGER IF NOT EXISTS trg_review_participant
BEFORE INSERT ON Review
WHEN NOT EXISTS (
    SELECT 1
    FROM OrderSheet o
    JOIN Item i ON i.itemNo = o.itemNo
    WHERE o.orderNo = NEW.orderNo
      AND (
        (NEW.reviewerNo = o.buyerNo AND NEW.revieweeNo = i.sellerNo)
        OR
        (NEW.reviewerNo = i.sellerNo AND NEW.revieweeNo = o.buyerNo)
      )
)
BEGIN
    SELECT RAISE(ABORT, '评价人必须是订单买家或卖家');
END;

CREATE TRIGGER IF NOT EXISTS trg_review_credit
AFTER INSERT ON Review
BEGIN
    UPDATE User
       SET creditScore = CASE
           WHEN creditScore + (NEW.rating - 3) * 2 > 120 THEN 120
           WHEN creditScore + (NEW.rating - 3) * 2 < 0 THEN 0
           ELSE creditScore + (NEW.rating - 3) * 2
       END
     WHERE userNo = NEW.revieweeNo;
END;

DROP VIEW IF EXISTS V_Item_Detail;
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
    i.description,
    i.originalPrice,
    i.sellPrice,
    i.condition,
    i.imageUrl,
    i.viewCount,
    (SELECT COUNT(*) FROM Favorite f WHERE f.itemNo = i.itemNo) AS favoriteCount,
    i.status,
    i.visible,
    i.publishTime
FROM Item i
JOIN User u ON u.userNo = i.sellerNo
JOIN Category c ON c.categoryNo = i.categoryNo
LEFT JOIN Category pc ON pc.categoryNo = c.parentCategoryNo;

DROP VIEW IF EXISTS V_Order_Summary;
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
    i.status AS itemStatus,
    o.locationNo,
    l.locationName,
    l.campusName,
    o.orderAmount,
    o.meetTime,
    o.orderStatus,
    o.createTime,
    o.finishTime
FROM OrderSheet o
JOIN User bu ON bu.userNo = o.buyerNo
JOIN Item i ON i.itemNo = o.itemNo
JOIN User su ON su.userNo = i.sellerNo
JOIN Location l ON l.locationNo = o.locationNo;

DROP VIEW IF EXISTS V_Risky_User;
CREATE VIEW V_Risky_User AS
WITH report_count AS (
    SELECT userNo, SUM(reportCount) AS totalReports
    FROM (
        SELECT targetNo AS userNo, COUNT(*) AS reportCount
        FROM Report
        WHERE targetType = '用户'
        GROUP BY targetNo
        UNION ALL
        SELECT i.sellerNo AS userNo, COUNT(*) AS reportCount
        FROM Report r
        JOIN Item i ON r.targetType = '物品' AND r.targetNo = i.itemNo
        GROUP BY i.sellerNo
    )
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
    u.status,
    COALESCE(rc.totalReports, 0) AS reportCount
FROM User u
LEFT JOIN report_count rc ON rc.userNo = u.userNo
WHERE u.creditScore < 70 OR COALESCE(rc.totalReports, 0) >= 2 OR u.status = '封禁';
