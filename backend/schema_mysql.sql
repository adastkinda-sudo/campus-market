-- Campus Market - MySQL 8.0 版数据库脚本
-- 使用方法：
--   1. CREATE DATABASE campus_market CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
--   2. USE campus_market;
--   3. SOURCE backend/schema_mysql.sql;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TRIGGER IF EXISTS trg_review_credit;
DROP TRIGGER IF EXISTS trg_review_participant;
DROP TRIGGER IF EXISTS trg_review_requires_success;
DROP TRIGGER IF EXISTS trg_order_update_cancel;
DROP TRIGGER IF EXISTS trg_order_update_success;
DROP TRIGGER IF EXISTS trg_order_create_lock_item;
DROP TRIGGER IF EXISTS trg_order_no_self_buy;

DROP VIEW IF EXISTS V_Risky_User;
DROP VIEW IF EXISTS V_Order_Summary;
DROP VIEW IF EXISTS V_Item_Detail;

CREATE TABLE IF NOT EXISTS Admin (
    adminNo INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    createdTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `User` (
    userNo INT PRIMARY KEY AUTO_INCREMENT,
    studentNo VARCHAR(50) NOT NULL UNIQUE,
    realName VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    userType VARCHAR(20) NOT NULL DEFAULT '学生',
    phone VARCHAR(20),
    wechat VARCHAR(50),
    authStatus VARCHAR(20) NOT NULL DEFAULT '未认证',
    creditScore INT NOT NULL DEFAULT 100,
    `status` VARCHAR(20) NOT NULL DEFAULT '正常',
    registerTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    adminNo INT,
    CONSTRAINT chk_user_type CHECK (userType IN ('学生', '教职工', '校友')),
    CONSTRAINT chk_user_auth CHECK (authStatus IN ('未认证', '待审核', '已认证', '认证驳回')),
    CONSTRAINT chk_user_credit CHECK (creditScore BETWEEN 0 AND 120),
    CONSTRAINT chk_user_status CHECK (`status` IN ('正常', '封禁')),
    CONSTRAINT fk_user_admin FOREIGN KEY (adminNo) REFERENCES Admin(adminNo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Category (
    categoryNo INT PRIMARY KEY AUTO_INCREMENT,
    categoryName VARCHAR(50) NOT NULL,
    parentCategoryNo INT,
    CONSTRAINT fk_category_parent FOREIGN KEY (parentCategoryNo)
        REFERENCES Category(categoryNo) ON DELETE SET NULL,
    UNIQUE KEY uk_category_parent (categoryName, parentCategoryNo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Location (
    locationNo INT PRIMARY KEY AUTO_INCREMENT,
    locationName VARCHAR(50) NOT NULL,
    campusName VARCHAR(50) NOT NULL,
    UNIQUE KEY uk_location_campus (locationName, campusName)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Announcement (
    announcementNo INT PRIMARY KEY AUTO_INCREMENT,
    adminNo INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    publishTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_announcement_admin FOREIGN KEY (adminNo) REFERENCES Admin(adminNo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Notification (
    notificationNo INT PRIMARY KEY AUTO_INCREMENT,
    userNo INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    linkType VARCHAR(50),
    linkNo INT,
    isRead TINYINT(1) NOT NULL DEFAULT 0,
    createTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_notification_read CHECK (isRead IN (0, 1)),
    CONSTRAINT fk_notification_user FOREIGN KEY (userNo) REFERENCES `User`(userNo),
    INDEX idx_notification_user_read (userNo, isRead, createTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Item (
    itemNo INT PRIMARY KEY AUTO_INCREMENT,
    sellerNo INT NOT NULL,
    categoryNo INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    `description` TEXT NOT NULL,
    originalPrice DECIMAL(10,2) NOT NULL,
    sellPrice DECIMAL(10,2) NOT NULL,
    `condition` VARCHAR(20) NOT NULL,
    imageUrl VARCHAR(500),
    viewCount INT NOT NULL DEFAULT 0,
    `status` VARCHAR(20) NOT NULL DEFAULT '在售',
    visible TINYINT(1) NOT NULL DEFAULT 1,
    publishTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_item_original_price CHECK (originalPrice >= 0),
    CONSTRAINT chk_item_sell_price CHECK (sellPrice >= 0),
    CONSTRAINT chk_item_condition CHECK (`condition` IN ('全新', '九成新', '八成新', '七成新', '使用痕迹明显')),
    CONSTRAINT chk_item_view_count CHECK (viewCount >= 0),
    CONSTRAINT chk_item_status CHECK (`status` IN ('在售', '交易中', '已售出', '已下架')),
    CONSTRAINT chk_item_visible CHECK (visible IN (0, 1)),
    CONSTRAINT fk_item_seller FOREIGN KEY (sellerNo) REFERENCES `User`(userNo),
    CONSTRAINT fk_item_category FOREIGN KEY (categoryNo) REFERENCES Category(categoryNo),
    INDEX idx_item_status_category (`status`, categoryNo),
    INDEX idx_item_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Favorite (
    favoriteNo INT PRIMARY KEY AUTO_INCREMENT,
    userNo INT NOT NULL,
    itemNo INT NOT NULL,
    createTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_favorite_user FOREIGN KEY (userNo) REFERENCES `User`(userNo),
    CONSTRAINT fk_favorite_item FOREIGN KEY (itemNo) REFERENCES Item(itemNo),
    UNIQUE KEY uk_favorite_user_item (userNo, itemNo),
    INDEX idx_favorite_user (userNo, createTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Wanted (
    wantedNo INT PRIMARY KEY AUTO_INCREMENT,
    buyerNo INT NOT NULL,
    categoryNo INT,
    title VARCHAR(200) NOT NULL,
    `description` TEXT NOT NULL,
    expectedPrice DECIMAL(10,2),
    `status` VARCHAR(20) NOT NULL DEFAULT '有效',
    publishTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_wanted_price CHECK (expectedPrice IS NULL OR expectedPrice >= 0),
    CONSTRAINT chk_wanted_status CHECK (`status` IN ('有效', '已关闭')),
    CONSTRAINT fk_wanted_buyer FOREIGN KEY (buyerNo) REFERENCES `User`(userNo),
    CONSTRAINT fk_wanted_category FOREIGN KEY (categoryNo)
        REFERENCES Category(categoryNo) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS OrderSheet (
    orderNo INT PRIMARY KEY AUTO_INCREMENT,
    buyerNo INT NOT NULL,
    itemNo INT NOT NULL,
    locationNo INT NOT NULL,
    orderAmount DECIMAL(10,2) NOT NULL,
    meetTime DATETIME NOT NULL,
    orderStatus VARCHAR(20) NOT NULL DEFAULT '待卖家确认',
    createTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finishTime DATETIME,
    activeItemNo INT GENERATED ALWAYS AS (
        CASE
            WHEN orderStatus IN ('待卖家确认', '待面交', '交易成功') THEN itemNo
            ELSE NULL
        END
    ) STORED,
    CONSTRAINT chk_order_amount CHECK (orderAmount >= 0),
    CONSTRAINT chk_order_status CHECK (orderStatus IN ('待卖家确认', '待面交', '交易成功', '已取消')),
    CONSTRAINT fk_order_buyer FOREIGN KEY (buyerNo) REFERENCES `User`(userNo),
    CONSTRAINT fk_order_item FOREIGN KEY (itemNo) REFERENCES Item(itemNo),
    CONSTRAINT fk_order_location FOREIGN KEY (locationNo) REFERENCES Location(locationNo),
    UNIQUE KEY idx_order_active_item (activeItemNo),
    INDEX idx_order_buyer (buyerNo, orderStatus)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Message (
    messageNo INT PRIMARY KEY AUTO_INCREMENT,
    itemNo INT NOT NULL,
    userNo INT NOT NULL,
    content TEXT NOT NULL,
    msgTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    parentMessageNo INT,
    CONSTRAINT fk_message_item FOREIGN KEY (itemNo) REFERENCES Item(itemNo),
    CONSTRAINT fk_message_user FOREIGN KEY (userNo) REFERENCES `User`(userNo),
    CONSTRAINT fk_message_parent FOREIGN KEY (parentMessageNo)
        REFERENCES Message(messageNo) ON DELETE SET NULL,
    INDEX idx_message_item_time (itemNo, msgTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Review (
    reviewNo INT PRIMARY KEY AUTO_INCREMENT,
    orderNo INT NOT NULL,
    reviewerNo INT NOT NULL,
    revieweeNo INT NOT NULL,
    rating INT NOT NULL,
    content TEXT NOT NULL,
    reviewTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_review_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT fk_review_order FOREIGN KEY (orderNo) REFERENCES OrderSheet(orderNo),
    CONSTRAINT fk_review_reviewer FOREIGN KEY (reviewerNo) REFERENCES `User`(userNo),
    CONSTRAINT fk_review_reviewee FOREIGN KEY (revieweeNo) REFERENCES `User`(userNo),
    UNIQUE KEY uk_review_order_reviewer (orderNo, reviewerNo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Report (
    reportNo INT PRIMARY KEY AUTO_INCREMENT,
    reporterNo INT NOT NULL,
    targetType VARCHAR(20) NOT NULL,
    targetNo INT NOT NULL,
    reason TEXT NOT NULL,
    reportStatus VARCHAR(20) NOT NULL DEFAULT '未处理',
    handleResult TEXT,
    handleAdminNo INT,
    createTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    handleTime DATETIME,
    CONSTRAINT chk_report_target_type CHECK (targetType IN ('物品', '用户')),
    CONSTRAINT chk_report_status CHECK (reportStatus IN ('未处理', '已处理')),
    CONSTRAINT fk_report_reporter FOREIGN KEY (reporterNo) REFERENCES `User`(userNo),
    CONSTRAINT fk_report_admin FOREIGN KEY (handleAdminNo) REFERENCES Admin(adminNo),
    INDEX idx_report_status (reportStatus)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

DELIMITER $$

CREATE TRIGGER trg_order_no_self_buy
BEFORE INSERT ON OrderSheet
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1
        FROM Item
        WHERE itemNo = NEW.itemNo
          AND sellerNo = NEW.buyerNo
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '买家不能购买自己发布的物品';
    END IF;
END$$

CREATE TRIGGER trg_order_create_lock_item
AFTER INSERT ON OrderSheet
FOR EACH ROW
BEGIN
    IF NEW.orderStatus IN ('待卖家确认', '待面交') THEN
        UPDATE Item
           SET `status` = '交易中'
         WHERE itemNo = NEW.itemNo;
    END IF;
END$$

CREATE TRIGGER trg_order_update_success
AFTER UPDATE ON OrderSheet
FOR EACH ROW
BEGIN
    IF NEW.orderStatus = '交易成功' THEN
        UPDATE Item
           SET `status` = '已售出'
         WHERE itemNo = NEW.itemNo;
    END IF;
END$$

CREATE TRIGGER trg_order_update_cancel
AFTER UPDATE ON OrderSheet
FOR EACH ROW
BEGIN
    IF NEW.orderStatus = '已取消'
       AND OLD.orderStatus <> '交易成功' THEN
        UPDATE Item
           SET `status` = '在售'
         WHERE itemNo = NEW.itemNo
           AND `status` = '交易中';
    END IF;
END$$

CREATE TRIGGER trg_review_requires_success
BEFORE INSERT ON Review
FOR EACH ROW
BEGIN
    IF (SELECT orderStatus FROM OrderSheet WHERE orderNo = NEW.orderNo) <> '交易成功' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '只有交易成功的订单才能评价';
    END IF;
END$$

CREATE TRIGGER trg_review_participant
BEFORE INSERT ON Review
FOR EACH ROW
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM OrderSheet o
        JOIN Item i ON i.itemNo = o.itemNo
        WHERE o.orderNo = NEW.orderNo
          AND (
            (NEW.reviewerNo = o.buyerNo AND NEW.revieweeNo = i.sellerNo)
            OR
            (NEW.reviewerNo = i.sellerNo AND NEW.revieweeNo = o.buyerNo)
          )
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '评价人必须是订单买家或卖家';
    END IF;
END$$

CREATE TRIGGER trg_review_credit
AFTER INSERT ON Review
FOR EACH ROW
BEGIN
    UPDATE `User`
       SET creditScore = GREATEST(0, LEAST(120, creditScore + (NEW.rating - 3) * 2))
     WHERE userNo = NEW.revieweeNo;
END$$

DELIMITER ;

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
    i.`description`,
    i.originalPrice,
    i.sellPrice,
    i.`condition`,
    i.imageUrl,
    i.viewCount,
    (SELECT COUNT(*) FROM Favorite f WHERE f.itemNo = i.itemNo) AS favoriteCount,
    i.`status`,
    i.visible,
    i.publishTime
FROM Item i
JOIN `User` u ON u.userNo = i.sellerNo
JOIN Category c ON c.categoryNo = i.categoryNo
LEFT JOIN Category pc ON pc.categoryNo = c.parentCategoryNo;

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
    i.`status` AS itemStatus,
    o.locationNo,
    l.locationName,
    l.campusName,
    o.orderAmount,
    o.meetTime,
    o.orderStatus,
    o.createTime,
    o.finishTime
FROM OrderSheet o
JOIN `User` bu ON bu.userNo = o.buyerNo
JOIN Item i ON i.itemNo = o.itemNo
JOIN `User` su ON su.userNo = i.sellerNo
JOIN Location l ON l.locationNo = o.locationNo;

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
    ) report_source
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
    u.`status`,
    COALESCE(rc.totalReports, 0) AS reportCount
FROM `User` u
LEFT JOIN report_count rc ON rc.userNo = u.userNo
WHERE u.creditScore < 70 OR COALESCE(rc.totalReports, 0) >= 2 OR u.`status` = '封禁';
