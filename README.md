# 校园二手物品交易系统

这是一个面向数据库原理实验的校园二手物品交易系统。项目推荐使用 MySQL 版作为正式实验运行环境，用于展示关系模式、完整性约束、索引、视图、触发器、存储过程以及前后端联动实现。项目同时保留 SQLite 版，作为无需配置数据库服务的快速测试环境，方便进行本地轻量验证。

系统采用 Python 后端、PyMySQL 数据库访问、原生 HTML/CSS/JavaScript 前端。MySQL 版启动时会自动创建 `campus_market` 数据库、执行迁移脚本并写入演示数据。

## 核心结构

```text
campus-market/
├── backend/
│   ├── app.py                # SQLite 快速测试入口，兼容旧启动方式
│   ├── app_mysql.py          # 推荐运行入口：MySQL 版后端和静态页面服务
│   ├── core.py               # 数据库连接、初始化、演示数据和通用校验工具
│   ├── server.py             # HTTP 服务、静态文件服务和业务接口路由
│   ├── schema.sql            # SQLite 快速测试脚本
│   └── schema_mysql.sql      # MySQL 表、索引、触发器、视图、存储过程
├── frontend/
│   ├── index.html            # 页面入口
│   ├── styles.css            # 页面样式
│   ├── app.js                # 前端交互和接口调用
│   └── assets/               # 示例物品图片
├── scripts/
│   └── smoke_sqlite.py       # SQLite 版冒烟测试
├── requirements-mysql.txt    # MySQL 版 Python 依赖
├── data/                     # SQLite 快速测试生成的本地数据库目录，已被 Git 忽略
├── output/                   # 本地产物目录，已被 Git 忽略
├── .gitignore
└── README.md
```

## 推荐运行：MySQL 版

MySQL 版需要本机或远程 MySQL 8.0 服务可连接，并安装 `PyMySQL`：

```bash
python3 -m venv .venv-mysql
source .venv-mysql/bin/activate
python -m pip install -r requirements-mysql.txt
python backend/app_mysql.py
```

启动后默认访问：

```text
http://127.0.0.1:8001
```

默认连接配置：

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=campus_market
MYSQL_CHARSET=utf8mb4
```

如果本地 MySQL 账号或密码不同，可以用环境变量覆盖：

```bash
MYSQL_USER=root MYSQL_PASSWORD=你的密码 python backend/app_mysql.py
```

## 快速测试：SQLite 版

SQLite 版用于快速测试和轻量验证，不需要额外数据库服务：

```bash
python3 backend/app.py
```

启动成功后访问：

```text
http://127.0.0.1:8000
```

首次启动会自动执行 `backend/schema.sql`，并生成：

```text
data/campus_market.db
```

如需重置 SQLite 测试数据，停止服务后删除 `data/campus_market.db`，再重新启动即可。

## 本地检查

项目提供 SQLite 冒烟测试脚本，会在临时目录中初始化数据库并验证核心表、视图、演示账号和订单触发器：

```bash
python3 scripts/smoke_sqlite.py
```

## 演示账号

管理员：

```text
账号：admin
密码：admin123
```

已认证用户：

```text
账号：24010001
密码：123456

账号：24010002
密码：123456
```

待审核用户：

```text
账号：24010003
密码：123456
```

## 已实现功能

- 游客可以浏览物品、搜索物品、按分类筛选、查看求购信息和公告。
- 用户可以注册、登录、提交校园身份认证。
- 认证用户可以发布物品、编辑物品、上架和下架物品。
- 认证用户可以收藏物品、留言、发布求购、下单、取消订单、确认收货和评价交易。
- 卖家可以确认接单、拒绝接单和取消订单。
- 系统会为订单、留言、评价、认证审核和举报处理生成站内通知。
- 管理员可以审核认证、维护分类、维护交易地点、处理举报、强制下架物品、封禁用户、维护公告并查看运营统计。

## MySQL 数据库对象

MySQL 脚本位于 `backend/schema_mysql.sql`，包含 13 张核心业务表：

- `Admin`
- `User`
- `Category`
- `Location`
- `Item`
- `Favorite`
- `Wanted`
- `OrderSheet`
- `Message`
- `Review`
- `Report`
- `Announcement`
- `Notification`

主要视图：

- `V_Item_Detail`：物品详情综合视图。
- `V_Order_Summary`：订单管理汇总视图。
- `V_Risky_User`：信誉异常用户预警视图。

主要触发器：

- `trg_order_no_self_buy`：禁止买家购买自己发布的物品。
- `trg_order_create_lock_item`：创建订单后锁定物品为交易中。
- `trg_order_update_success`：交易成功后将物品标记为已售出。
- `trg_order_update_cancel`：订单取消后恢复物品为在售。
- `trg_review_requires_success`：限制只有交易成功订单才能评价。
- `trg_review_participant`：限制评价人必须是订单买家或卖家。
- `trg_review_credit`：评价后自动更新被评价人信用积分。

主要存储过程：

- `sp_test_ping`：返回数据库连通状态、当前时间、数据库名、用户数、物品数和订单数，可用于验证 MySQL 脚本执行结果。

## 数据库版本说明

项目仅保留 MySQL 和 SQLite 两套数据库实现。正式实验展示建议优先使用 MySQL 版，用于展示关系模式、完整性约束、索引、视图、触发器和存储过程；SQLite 版用于本地快速测试和轻量验证。后续维护数据库结构时，以 `backend/schema_mysql.sql` 作为正式环境的主脚本，`backend/schema.sql` 只同步保留便于本地测试的等价结构。

## 本地文件

`.gitignore` 已忽略本地虚拟环境、运行时数据库、Python 缓存、编辑器配置和本地工具状态。运行过程中生成的本地数据库文件不需要提交。
