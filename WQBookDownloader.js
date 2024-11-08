
var wq_domain = "wqbook.wqxuetang.com";

// npm install puppeteer
const puppeteer = require("puppeteer");
const sleep = (ms) => new Promise((res) => setTimeout(res, ms));

// 创建文件夹
const fs = require("fs");

// 保存登录状态
async function saveLoginState(page) {
    // 获取所有 cookies
    const cookies = await page.cookies();
    fs.writeFileSync("./cookies.json", JSON.stringify(cookies, null, 2));
    console.log("登录状态已保存");
}

// 加载登录状态
async function loadLoginState(page) {
    // 检查是否有保存的 cookies
    if (fs.existsSync("./cookies.json")) {
        const cookies = JSON.parse(fs.readFileSync("./cookies.json"));
        await page.setCookie(...cookies);
        console.log("已加载 cookies");
        return true;
    }
    return false;
}

const readline = require("readline");

// 创建一个 readline 接口，用于等待用户输入
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

// 等待用户确认
const waitForUserConfirmation = () => {
    return new Promise((resolve) => {
        rl.question("请完成后按下回车键继续...", () => {
            resolve();
        });
    });
};

const USERCONFIRMATION_BROWSER_OPTIONS = {
    headless: false,
    defaultViewport: null,
    args: ["--start-maximized"],
};

const LAUNCH_USE_OLD_COOKIES = 0;
const LAUNCH_LOGIN = 1;
const LAUNCH_USE_NEW_COOKIES = 2;

var launchFlag = LAUNCH_USE_OLD_COOKIES;

(async () => {
    console.log("WARNING: 注意，本程序仅用于学习交流，禁止用于商业用途。");

    let browser = undefined;
    let page = undefined;
    let bookName = undefined;


    // 检查是否使用校园机构域名
    let domain_ans = await new Promise((resolve) => {
        rl.question(`是否使用校园机构账号？\n\t- 如果不使用，回车跳过即可。此时使用通用域名：${wq_domain}\n\t- 否则，请输入您的校园机构域名，详见README。示例：lib-ustc.wqxuetang.com\n请输入：`, (answer) => {
            resolve(answer);
        });
    });
    // 去除首尾空格
    domain_ans = domain_ans.trim();
    if (domain_ans !== "") {
        wq_domain = domain_ans;
    } else {
        console.log("使用通用域名: ", wq_domain);
    }
    
    // 输入bid
    const bid = await new Promise((resolve) => {
        rl.question("\n请输入bid: ", (bid) => {
            resolve(bid);
        });
    });
    // const bid = '3251198';
    // console.log("注意这里为了方便测试，直接使用了一个bid: ", bid);
    // console.log("bid: ", bid);

    // -------------------------------------------
    // 截取网页图片
    // -------------------------------------------
    // 启动浏览器
    while (true) {
        const innerBrowser = await puppeteer.launch(
            launchFlag == LAUNCH_LOGIN ? USERCONFIRMATION_BROWSER_OPTIONS : undefined
        );
        const innerPage = await innerBrowser.newPage();

        // 设置用户代理
        await innerPage.setUserAgent(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
        );

        if (launchFlag == LAUNCH_LOGIN) {
            // 设置视口大小，以确保能够完整显示登录页面
            await innerPage.setViewport({
                width: 375,
                height: 667,
            });
            await innerPage.goto(`https://${wq_domain}/deep/m/read/pdf?bid=${bid}`);

            // 自动化操作
            // console.log("请点击右上角书签，完成登录操作。");
            // 等待 class=".e_tip" 元素出现并点击（点击屏幕中央出现的指导页）
            const eTipSelector = ".e_tip";
            await innerPage.waitForSelector(eTipSelector, { visible: true });
            await innerPage.click(eTipSelector);
            await sleep(200);

            // 点击书签按钮 .page-m-mark
            await innerPage.waitForSelector(".page-m-mark", { visible: true });
            await innerPage.click(".page-m-mark");
            console.log("点击书签按钮成功");
            await sleep(200);

            // 查找所有 .fui-button 的元素
            await innerPage.evaluate(() => {
                const buttons = document.querySelectorAll(".fui-button");
                for (let button of buttons) {
                    const text = button.innerText;
                    if (text === "确定") {
                        button.click();
                        break;
                    }
                }
            });
            console.log("点击确定按钮成功");

            console.log("等待用户手动登录完成...");

            // 循环检测页面，如果跳转回来了，说明登录成功
            while (true) {
                await sleep(2000);
                const url = innerPage.url();
                if (url.startsWith("https://${wq_domain}/deep/m/read/pdf")) {
                    break;
                }
            }

            // 保存登录状态
            await saveLoginState(innerPage);
            console.log("登录状态已保存!");
            launchFlag = LAUNCH_USE_NEW_COOKIES;
            console.log("关闭浏览器...");
            await innerBrowser.close();
            continue;
        } else {
            // 设置视口大小，以确保获取的图片清晰
            await innerPage.setViewport({
                width: 1200 * 2,
                height: 2000 * 2,
            });
            // 加载登录状态
            const cookiesLoaded = await loadLoginState(innerPage);

            if (!cookiesLoaded) {
                console.log("未加载登录状态，等待用户手动登录...");
                launchFlag = LAUNCH_LOGIN;
                innerBrowser.close();
                continue;
            }

            // 访问目标网页
            await innerPage.goto(`https://${wq_domain}/deep/m/read/pdf?bid=${bid}`);
            console.log("访问目标网页成功");

            let answer = "y";
            if (launchFlag == LAUNCH_USE_OLD_COOKIES) {
                answer = await new Promise((resolve) => {
                    rl.question("是否使用本地cookies登录？（如果间隔超过15min，建议重新登录）(y/n)", (answer) => {
                        resolve(answer);
                    });
                });
                if (answer !== "n") {
                    console.log("检查是否存在可用的cookies...");
                }
            } else {
                console.log("检查是否存在可用的cookies...");
            }

            if (answer === "n") {
                console.log("不使用本地cookies登录，等待用户手动登录...");
                launchFlag = LAUNCH_LOGIN;
                innerBrowser.close();
                continue;
            } else {
                console.log("已加载完整登录状态!");
                browser = innerBrowser;
                page = innerPage;
            }
        }
        break;
    }
    // 等待 class=".e_tip" 元素出现并点击（点击屏幕中央出现的指导页）
    const eTipSelector = ".e_tip";
    await page.waitForSelector(eTipSelector, { visible: true });
    await page.click(eTipSelector);
    console.log("点击 e_tip 元素成功");

    // 等待 class=".perc" 元素出现并获取页码字符串
    await page.waitForSelector(".perc", { visible: true });
    await sleep(2000);
    const pageNumStr = await page.$eval(".perc", (el) => el.getElementsByTagName("span")[0].innerText);
    console.log("页码字符串: ", pageNumStr);
    var totalPageNum = parseInt(pageNumStr.split("/")[1]);
    console.log("总页数: ", totalPageNum);
    if (totalPageNum == 0) {
        console.log("总页数为 0，退出程序");
        await innerBrowser.close();
        return;
    }

    // 获取书名 .e_title 元素里的 span 元素的文本
    bookName = await page.$eval(".e_title", (el) => el.getElementsByTagName("span")[0].innerText);
    console.log("书名: ", bookName);

    // 创建图片文件夹
    const dir = `./${bid}_${bookName}_images`;
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir);
    }

    // totalPageNum = 1; // 测试用
    // 保存登录状态
    for (let pageNum = 1; pageNum <= totalPageNum; pageNum++) {
        // 检查图片是否已经存在
        const imagePath = `${dir}/image${pageNum}.png`;
        if (fs.existsSync(imagePath)) {
            console.log(`第 ${pageNum} 页截图已存在，跳过`);
            continue;
        }

        console.log(`开始截图第 ${pageNum}/${totalPageNum} 页`);

        // 滚动到 #pageImgBox1 元素
        const result = await page.evaluate((pageNum) => {
            const element = document.querySelector(`#pageImgBox${pageNum}`);
            if (element) {
                element.scrollIntoView({ behavior: "instant", block: "center", inline: "nearest" });
                return `滚动到第 ${pageNum} 页`;
            } else {
                return `未找到第 ${pageNum} 页指定的元素`;
            }
        }, pageNum);
        console.log(result);

        // 选择 id="pageImgBox1" 的元素
        const element = await page.$(`#pageImgBox${pageNum}`);

        if (element) {
            // 等待元素内的 uni-view 标签中的 uni-image 标签出现
            await page.waitForSelector(`#pageImgBox${pageNum} uni-view.page-lmg img`);
            await sleep(2000);  // 等待一段时间确保图片加载完成，否则容易出现空白块
            // 截图该元素并保存为 image.png
            await element.screenshot({ path: `${dir}/image${pageNum}.png` });
            console.log(`第 ${pageNum} 页截图保存成功`);
        } else {
            console.log(`未找到第 ${pageNum} 页指定的元素`);
            console.log("可能您未购买该电子书，或者登录状态已失效。如果您已购买，请重新登录。");

            browser.close();
            rl.close();
            return;
        }
    }

    // 读取电子书的目录文件
    // https://wqbook.wqxuetang.com/deep/book/v1/catatree?bid=${bid}
    // 检测是否存在目录文件
    if (fs.existsSync(`${dir}/catalog.json`)) {
        console.log("目录文件已存在，跳过下载目录文件步骤");
    } else {
        console.log("下载目录文件...");
        const catalogUrl = `https://${wq_domain}/deep/book/v1/catatree?bid=${bid}`;
        const response = await page.goto(catalogUrl);
        const catalogData = await response.json();

        // 保存目录数据到文件
        const catalogPath = `${dir}/catalog.json`;
        fs.writeFileSync(catalogPath, JSON.stringify(catalogData, null, 2));
        console.log("目录数据已保存到: ", catalogPath);
    }
    // 关闭浏览器
    await browser.close();

    // -------------------------------------------
    // 将图片合成PDF
    // -------------------------------------------
    // npm install pdf-lib pdf-outline
    const { PDFDocument, rgb } = require("pdf-lib");
    const path = require("path");

    const imagesDir = dir;
    const outputPdfPath = `./${bid}_${bookName}.pdf`;

    async function imagesToPdf() {
        const pdfDoc = await PDFDocument.create();

        // -------------------------------------------
        // 处理图片
        // -------------------------------------------
        // 获取./images文件夹中所有文件
        const files = fs.readdirSync(imagesDir).filter((file) => file.endsWith(".png"));

        // 将文件名按照pageNum排序
        files.sort((a, b) => {
            const numA = parseInt(a.match(/\d+/)[0], 10);
            const numB = parseInt(b.match(/\d+/)[0], 10);
            return numA - numB;
        });

        for (let file of files) {
            console.log(`正在处理 ${file}...`);
            const filePath = path.join(imagesDir, file);
            const imageBytes = fs.readFileSync(filePath);
            const image = await pdfDoc.embedPng(imageBytes);
            const imagePage = pdfDoc.addPage([image.width, image.height]);

            imagePage.drawImage(image, {
                x: 0,
                y: 0,
                width: image.width,
                height: image.height,
            });
        }

        // // -------------------------------------------
        // // 处理PDF目录
        // // -------------------------------------------
        // // 递归函数，用于将 JSON 的目录结构转换为 PDF 大纲
        // function addOutlineItems(outline, children) {
        //     if (children && children.length) {
        //         children.forEach((item) => {
        //             const outlineItem = outline.addItem({
        //                 title: item.label,
        //                 pageNumber: parseInt(item.pnum) - 1, // 注意页码从 0 开始
        //             });
        //             if (item.children) {
        //                 addOutlineItems(outlineItem, item.children);
        //             }
        //         });
        //     }
        // }
        // const outline = pdfOutline(pdfDoc);
        // addOutlineItems(outline, catalogData);

        // 保存PDF到文件系统
        console.log("正在保存PDF...");
        const pdfBytes = await pdfDoc.save();
        fs.writeFileSync(outputPdfPath, pdfBytes);

        console.log(`成功生成${outputPdfPath}`);
    }

    // 检测是否存在PDF
    if (fs.existsSync(outputPdfPath)) {
        console.log("PDF文件已存在，跳过生成PDF步骤");
    } else {
        console.log("开始生成PDF...");
        imagesToPdf().catch((err) => console.error("Error: ", err));
    }

    const { exec } = require("child_process");

    // 指定 Python 脚本和工作目录路径
    const scriptPath = path.join(__dirname, "add_toc.py");
    const workDir = __dirname;
    const outputPdfPath2 = `./${bid}_${bookName}_toc.pdf`;

    // 运行 Python 脚本
    exec(
        `python ${scriptPath} "${outputPdfPath}" "${dir}/catalog.json" "${outputPdfPath2}"`,
        { cwd: workDir },
        (error, stdout, stderr) => {
            if (error) {
                console.error(`Error executing script: ${error.message}`);
                return;
            }

            if (stderr) {
                console.error(`Script error output: ${stderr}`);
                return;
            }

            console.log(`Updated PDF saved to: ${outputPdfPath2}`);
        }
    );

    // 关闭 readline 接口
    rl.close();
})();
