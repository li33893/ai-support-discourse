// 引入模块
const express = require("express"); //帮我写能被浏览器访问的程序
const fs      = require("fs"); //文件读写
const path    = require("path");

//造出app
const app        = express(); //调用express，早出一个服务器

// 定好路径
const PORT       = 3000;
const INPUT_FILE = "sampling_first_round.json";
const TEMP_FILE  = "sampling_first_round.tmp";
const INPUT_DIR  = path.join(__dirname, INPUT_FILE);
const TEMP_DIR   = path.join(__dirname, TEMP_FILE);
const PUBLIC     = path.join(__dirname, "public");

//middleware
app.use(express.json({limit:"50mb"})); // app对象的方法use：注册“每个请求都先做什么”；json是启用json解析的功能
app.use(express.static(PUBLIC)); // 把一个目录里的文件对外开放，浏览器按文件名就能取

// route 1: 读数据
app.get("/api/data", (req, res) => {// req 是进来的请求，res 是回话的工具
    const raw = fs.readFileSync(INPUT_DIR, "utf-8"); //读文件
    res.json(JSON.parse(raw));
});

// route 2: 保存数据
app.post("/api/data", (req, res) => {
    const tmp = TEMP_DIR;
    fs.writeFileSync(tmp, JSON.stringify(req.body, null,2), "utf-8");
    fs.renameSync(tmp, INPUT_DIR);
    res.json({ ok: true });
});

app.listen(PORT, () => console.log(`http://localhost:${PORT}`));