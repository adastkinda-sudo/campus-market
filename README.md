[简体中文](README.md) | [English](README.en.md)

# 理物 — 华东理工大学校园二手物品交易平台

**理物**是面向华东理工大学的校园二手物品交易平台。"理"取自"华理"，"理物"有"整理物品"之意，又与"礼物"谐音——寓意每收到一个新的物品，都可以是一份礼物。

平台采用 Python 后端 + Vue 3 / Vite 前端架构，支持 MySQL 和 SQLite 两种数据库后端。MySQL 版用于正式部署运行，SQLite 版用于本地快速启动和测试。

## 界面预览

以下截图来自前端构建产物与 SQLite 本地演示环境，桌面窗口宽度为 1440 像素。账号资料、商品、订单和私信均为演示数据。

### 平台首页

展示平台介绍、交易入口、校园公告、热门商品和平台统计。

![理物平台首页：平台介绍、校园公告、热门商品和平台统计](docs/screenshots/home.png)

<details>
<summary>交易市场与商品详情</summary>

### 交易市场

通过关键词、分类、校区和排序浏览物品，查看价格、品相、卖家信用和在售状态。

![交易市场：搜索筛选与商品列表](docs/screenshots/marketplace.png)

### 商品详情

查看商品图片、描述、卖家信息和留言；认证用户可收藏物品、提交订单或私聊卖家。

![商品详情：商品信息、交易操作和留言](docs/screenshots/item-detail.png)

</details>

<details>
<summary>登录与个人中心</summary>

### 登录

提供登录、注册和密码重置入口。

![登录界面：账号登录、注册和密码重置入口](docs/screenshots/login.png)

### 个人中心

集中查看收藏、订单、私信、通知和浏览记录，编辑个人资料并提交校园身份认证。

![个人中心：功能入口、个人资料和校园身份认证](docs/screenshots/account.png)

</details>

<details>
<summary>发布管理与求购市场</summary>

### 发布管理

填写物品分类、校区、价格、品相、图片和描述，并查看自己发布的闲置物品。

![发布管理：物品发布表单与我的发布](docs/screenshots/publish.png)

### 求购市场

发布求购需求，浏览需求描述、预期价格和发布者信息。

![求购市场：求购表单与需求列表](docs/screenshots/wanted.png)

</details>

<details>
<summary>订单与私信</summary>

### 我的订单

区分买入和卖出订单，展示交易金额、面交安排、订单状态及对应操作。

![我的订单：买入、卖出、待确认和待面交的演示订单](docs/screenshots/orders.png)

### 私信

围绕商品与交易对象沟通细节，确认品相、时间和面交地点。

![私信界面：会话列表与演示交易对话](docs/screenshots/chats.png)

</details>

<details>
<summary>管理后台</summary>

### 后台管理

查看运营统计、审核校园身份认证并管理用户状态。

![管理后台：运营统计、身份认证审核和用户管理](docs/screenshots/admin.png)

### 物品管理

查看平台物品、卖家和交易状态，处理违规或不适合展示的物品。

![后台物品管理：物品列表与管理操作](docs/screenshots/admin-items.png)

</details>

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
│   ├── index.html            # Vite 页面入口
│   ├── app.js                # 前端主逻辑（未构建时直接使用）
│   ├── styles.css            # 全局样式（未构建时直接使用）
│   ├── package.json          # Vue 3 + Vite 前端依赖和脚本
│   ├── vite.config.js        # Vite 开发代理配置
│   ├── assets/               # 静态 SVG 图标
│   ├── public/               # 构建后静态资源目录
│   └── src/                  # Vue 页面、组件、路由、状态管理和接口封装
├── scripts/
│   ├── smoke_sqlite.py       # SQLite 版冒烟测试
│   └── sync_mysql_to_sqlite.py  # MySQL → SQLite 结构同步脚本
├── docs/screenshots/         # README 界面截图
├── requirements-mysql.txt    # MySQL 版 Python 依赖
├── data/                     # SQLite 快速测试生成的本地数据库目录，已被 Git 忽略
├── output/                   # 本地产物目录，已被 Git 忽略
├── .gitignore
├── README.en.md              # 英文文档
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

## 前端开发：Vue 3 + Vite

首次开发前安装前端依赖：

```bash
cd frontend
npm install
```

开发联调时，先启动 SQLite 或 MySQL 后端，再启动 Vite：

```bash
npm run dev
```

Vite 默认访问：

```text
http://127.0.0.1:5173
```

`vite.config.js` 会把 `/api` 和 `/uploads` 代理到 `http://127.0.0.1:8000`。如使用 MySQL 后端 `8001`，可临时修改代理目标或通过后端构建产物方式访问。

构建前端：

```bash
cd frontend
npm run build
```

构建产物位于 `frontend/dist/`。Python 后端会优先服务 `frontend/dist/index.html`；如果未构建，则仍保留源码目录用于前端开发。

注意：直接访问 Python 后端地址（SQLite 默认 `8000`，MySQL 默认 `8001`）前，必须先执行一次 `npm run build` 生成 `frontend/dist/`。如果没有构建产物，后端会显示构建提示页，而不会直接加载 Vite 源码。

## 快速测试：SQLite 版

SQLite 版用于快速测试和轻量验证，不需要额外数据库服务：

```bash
python backend/app.py
```

启动成功后访问：

```text
http://127.0.0.1:8000
```

首次启动会自动执行 `backend/schema.sql`，并生成：

```text
data/campus_market.db
```

用户上传的头像、商品图片和校园卡照片会保存到：

```text
data/uploads/
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
- 游客可以搜索用户昵称并查看公开主页，主页展示身份认证、公开商品和商品留言。
- 用户可以注册、登录、编辑头像、性别、入学年份、个性签名、手机号和微信号，并上传校园卡照片提交认证。
- 认证用户可以发布物品、编辑物品和下架物品；下架会隐藏商品，视为删除。
- 认证用户可以收藏物品、留言、发布求购、下单、取消订单、确认收货和评价交易。
- 认证用户可以互相私聊，私信页会定时刷新当前会话。
- 登录用户可以通过"联系我们"向管理员提交平台建议和使用反馈。
- 卖家可以确认接单、拒绝接单和取消订单。
- 系统会为订单、留言、评价、私聊、认证审核、举报处理和反馈回复生成站内通知。
- 管理员可以审核认证资料、查看校园卡照片、回复用户反馈、维护分类、维护交易校区、处理举报、强制下架物品、封禁用户、维护公告并查看运营统计。

## MySQL 数据库对象

MySQL 脚本位于 `backend/schema_mysql.sql`，包含 16 张核心业务表：

- `Admin`
- `User`
- `Category`
- `Location`
- `Item`
- `Favorite`
- `Wanted`
- `OrderSheet`
- `Message`
- `PrivateConversation`
- `PrivateMessage`
- `Review`
- `Report`
- `Feedback`
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

- `sp_system_health`：返回数据库连通状态、当前时间、数据库名、用户数、物品数和订单数。

## 数据库版本说明

项目支持 MySQL 和 SQLite 两套数据库实现。正式部署建议使用 MySQL 版，具备完整的关系模式、完整性约束、索引、视图、触发器和存储过程支持；SQLite 版用于本地快速测试和轻量验证。数据库结构的维护以 `backend/schema_mysql.sql` 作为正式环境主脚本，`backend/schema.sql` 同步保留便于本地测试的等价结构。

## 本地文件

`.gitignore` 已忽略本地虚拟环境、运行时数据库、Python 缓存、编辑器配置和本地工具状态。运行过程中生成的本地数据库文件不需要提交。
