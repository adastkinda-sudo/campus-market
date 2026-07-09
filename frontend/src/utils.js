export function money(value) {
  const number = Number(value || 0);
  return `¥${Number.isInteger(number) ? number : number.toFixed(2)}`;
}

export function truncateText(text, length = 60) {
  const value = String(text || "");
  return value.length > length ? `${value.slice(0, length)}...` : value;
}

export function shortTime(value) {
  if (!value) return "";
  return String(value).replace("T", " ").slice(0, 16);
}

export function discountPercent(item) {
  const original = Number(item.originalPrice || 0);
  const sell = Number(item.sellPrice || 0);
  if (!original || sell >= original) return "";
  return `省 ${Math.round((1 - sell / original) * 100)}%`;
}

const categoryImageRules = [
  [["电子阅读器", "kindle", "电纸书"], "/assets/ereader.svg"],
  [["手机平板", "手机", "平板", "iphone", "ipad", "redmi"], "/assets/phone.svg"],
  [["音频设备", "耳机", "音箱", "蓝牙"], "/assets/audio.svg"],
  [["摄影器材", "相机", "镜头", "拍立得", "摄像头"], "/assets/camera.svg"],
  [["打印机", "办公设备"], "/assets/printer.svg"],
  [["实验耗材", "白大褂", "防护镜", "面包板", "实验"], "/assets/lab.svg"],
  [["文具用品", "学习办公", "文具", "文件夹", "资料盒", "便利贴"], "/assets/stationery.svg"],
  [["宿舍电器", "电煮锅", "电饭煲", "水壶", "循环扇", "小锅"], "/assets/kettle.svg"],
  [["收纳清洁", "生活用品", "收纳", "压缩袋", "置物架", "清洁"], "/assets/storage.svg"],
  [["床品家纺", "床帘", "枕", "家纺", "床品"], "/assets/bedding.svg"],
  [["厨具餐具", "咖啡", "饭盒", "厨具", "餐具"], "/assets/kitchen.svg"],
  [["家居装饰", "装饰", "台历", "衣帽架", "台灯"], "/assets/decor.svg"],
  [["滑板轮滑", "滑板", "轮滑"], "/assets/skateboard.svg"],
  [["健身器材", "健身", "哑铃", "瑜伽", "拉力带"], "/assets/fitness.svg"],
  [["球类用品", "运动户外", "球拍", "羽毛球", "乒乓", "球类"], "/assets/sports.svg"],
  [["户外露营", "露营", "野餐", "户外"], "/assets/camping.svg"],
  [["乐器文娱", "乐器", "吉他", "尤克里里", "卡林巴"], "/assets/music.svg"],
  [["桌游手办", "桌游", "手办", "uno", "狼人杀"], "/assets/game.svg"],
  [["服装鞋帽", "美妆服饰", "服装", "鞋", "西服"], "/assets/fashion.svg"],
  [["箱包配饰", "箱包", "行李箱", "背包", "电脑包"], "/assets/bag.svg"],
  [["美妆个护", "美妆", "化妆", "卷发", "个护"], "/assets/beauty.svg"],
  [["饰品手表", "饰品", "手表", "项链"], "/assets/watch.svg"],
  [["电脑整机", "电脑配件", "数码", "电脑", "显示器", "硬盘", "键盘", "鼠标"], "/assets/laptop.svg"],
  [["代步", "自行车", "骑行", "车锁", "头盔"], "/assets/bicycle.svg"],
  [["书", "教材", "资料", "考研", "外语", "文学"], "/assets/book.svg"],
];

export function defaultImageForText(text) {
  const value = String(text || "").toLowerCase();
  for (const [keywords, imageUrl] of categoryImageRules) {
    if (keywords.some((keyword) => value.includes(keyword.toLowerCase()))) return imageUrl;
  }
  return "/assets/kettle.svg";
}

export function defaultImage(item) {
  if (item?.imageUrl) return item.imageUrl;
  return defaultImageForText(`${item?.title || ""} ${item?.categoryName || ""} ${item?.parentCategoryName || ""}`);
}
