# 校园二手物品交易系统

这是一个面向数据库原理实验的校园二手物品交易系统。项目包含前端页面、Python 后端接口、数据库建表脚本、视图、触发器和演示数据，可以用于本地运行、功能演示和实验报告支撑。

默认推荐使用 SQLite 版运行：不需要安装额外依赖，启动后会自动创建本地数据库文件。项目同时保留 MySQL 版后端和 SQL Server 版数据库脚本，便于展示不同关系数据库下的表结构、约束、视图和触发器实现。

## 项目结构

```text
campus-market/
├── backend/
│   ├── app.py                # SQLite 版后端入口，同时提供静态页面服务
│   ├── app_mysql.py          # MySQL 版后端入口，复用主要业务接口
│   ├── app_sqlserver.py      # SQL Server 连接入口，需按本机环境调整
│   ├── schema.sql            # SQLite 表、索引、触发器、视图
│   ├── schema_mysql.sql      # MySQL 表、索引、触发器、视图
│   └── schema_sqlserver.sql  # SQL Server 表、索引、触发器、视图和演示数据
├── frontend/
│   ├── index.html            # 页面入口
│   ├── styles.css            # 页面样式
│   ├── app.js                # 前端交互逻辑
│   └── assets/               # 示例物品图片
├── data/                     # 运行时生成的数据库文件目录，已被 Git 忽略
├── requirements-mysql.txt    # MySQL 版 Python 依赖
├── .gitignore
└── README.md
```

## 快速运行 SQLite 版

SQLite 版只依赖 Python 标准库，适合最快速的本地演示。

```bash
cd campus-market
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

如果想重新初始化演示数据，停止服务后删除 `data/campus_market.db`，再重新启动即可。

## 运行 MySQL 版

MySQL 版需要本机或远程 MySQL 8.0 服务可连接，并安装 `PyMySQL`。

```bash
cd campus-market
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-mysql.txt
python backend/app_mysql.py
```

启动成功后访问：

```text
http://127.0.0.1:8001
```

默认连接配置如下：

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=campus_market
MYSQL_CHARSET=utf8mb4
```

如果账号或密码不同，可以用环境变量覆盖：

```bash
MYSQL_USER=root MYSQL_PASSWORD=你的密码 python backend/app_mysql.py
```

MySQL 版启动时会自动创建 `campus_market` 数据库，执行 `backend/schema_mysql.sql`，并写入演示数据。

## SQL Server 脚本

SQL Server 版主要用于展示数据库对象实现，脚本位于：

```text
backend/schema_sqlserver.sql
```

使用方式：

1. 在 SQL Server 中新建数据库，例如 `CampusMarket`。
2. 使用 SSMS 或 Azure Data Studio 打开 `backend/schema_sqlserver.sql`。
3. 执行脚本，创建表、索引、触发器、视图和演示数据。

如果要运行或调试 `backend/app_sqlserver.py`，需要先安装 `pyodbc` 和 Microsoft ODBC Driver，并通过 `SQL_SERVER_CONN_STR` 配置连接字符串。

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

- 游客可以浏览在售物品、搜索物品、按分类筛选、查看求购信息和公告。
- 用户可以注册、登录、提交校园身份认证、发布物品、编辑物品、上架和下架物品。
- 认证用户可以收藏物品、留言、发布求购、下单、取消订单、确认收货和评价交易。
- 卖家可以处理订单，支持确认接单、拒绝接单和取消订单。
- 系统会为订单、留言、评价、认证审核和举报处理生成站内通知。
- 管理员可以审核认证、维护分类、维护交易地点、处理举报、强制下架物品、封禁用户、维护公告并查看运营统计。

## 数据库实现点

主要关系模式包括：

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

已实现的视图：

- `V_Item_Detail`：物品详情综合视图。
- `V_Order_Summary`：订单管理汇总视图。
- `V_Risky_User`：信誉异常用户预警视图。

已落地的关键约束和触发逻辑：

- 用户类型限制为学生、教职工、校友。
- 管理员使用独立 `Admin` 表，与普通用户分离。
- 买家不能购买自己发布的物品。
- 同一物品同一时刻只能存在一个进行中或成功订单。
- 创建订单后，物品状态自动从在售变为交易中。
- 订单取消后，物品状态自动恢复为在售。
- 交易成功后，物品状态自动变为已售出。
- 只有交易成功的订单才能评价。
- 评价星级限制在 1 到 5。
- 评价完成后自动更新被评价人的信用积分。
- 用户不能收藏自己发布的物品。
- 订单、留言、评价、认证和举报处理动作会写入通知表。

## 本地文件说明

`.gitignore` 已忽略本地虚拟环境、运行时数据库、Python 缓存和本地编辑器配置。其中包括已经创建的 `.venv/` 环境，以及 `.venv-mysql/` 这类以 `.venv-` 开头的本地环境目录。
