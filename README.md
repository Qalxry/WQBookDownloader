# WQBookDownloader

WQBookDownloader 项目旨在自动化下载文泉书局的***已付费电子书***内容，并将其生成为 PDF 文件，附带目录。

不是破解！不是破解！不是破解！你还是要付费的！只不过这里制裁了一下文泉书局费尽心思不让下载PDF的sb行为。

**注意：本程序仅用于学习交流，禁止用于商业用途。**

> #### 如果您使用个人账户
>
> 请确保您购买了该电子书，否则，只能下载前30页的预览内容，无法下载完整电子书。
>
> 如果您未购买该电子书，代码依然会下载前文泉书局提供的30页的内容，但不会生成PDF文件。
>
> #### 如果您使用校园机构账户，并且能够在网页端查看到完整电子书
>
> 请查看您网页的URL是否具有学校特定的域名前缀，例如：`lib-xxx.wqxuetang` 。
>
> 如果是，则需要修改 js 文件中硬编码的URL前缀。
>
> 详细信息可查看 @RessMatthew 提供的信息 [issue #1](https://github.com/Qalxry/WQBookDownloader/issues/1) 。
>
> 再次声明：下载的PDF文件仅供您个人学习使用，请勿将下载的PDF进行传播，以免造成侵权行为。

## 目录

- [项目介绍](#项目介绍)
- [安装依赖](#安装依赖)
- [使用说明](#使用说明)
  - [准备工作](#准备工作)
  - [运行步骤](#运行步骤)

## 项目介绍

该项目包含两个主要文件：

- `WQBookDownloader.js`: 使用 Puppeteer 库进行网页自动化操作，下载图片并生成基础的 PDF 文件。
- `add_toc.py`: 使用 PyMuPDF 库为生成的 PDF 文件添加目录。

## 安装依赖

在运行本项目前，你需要安装一些依赖项。确保你已经安装了 [Node.js](https://nodejs.org/) 和 [Python](https://www.python.org/)，以及谷歌浏览器（Chrome）。

> 如果您没有安装 Chrome ，希望使用 Edge ，可以参考 @June-Lang 提供的解决方案：[issue #2](https://github.com/Qalxry/WQBookDownloader/issues/2)。

1. 克隆本仓库：

   ```bash
   git clone https://github.com/Qalxry/WQBookDownloader.git
   cd WQBookDownloader
   ```

2. 安装 Node.js 依赖：

   ```bash
   npm install puppeteer pdf-lib
   ```

   如果 `npm install` 卡在 `sill idealTree buildDeps` 不动，可以尝试使用淘宝镜像安装依赖，或者科学上网。

   ```bash
   npm install puppeteer pdf-lib --registry=https://registry.npmmirror.com
   ```

3. 安装 Python 依赖：

   ```bash
   pip install pymupdf
   ```

## 使用说明

### 准备工作

1. 获取要下载的电子书的 `bid`，你可以从目标网站的 URL 中找到该参数。

例如：

![alt text](./asserts/711a88fad7b6aa2d7c47ebc508efcad0.png)

### 运行步骤

1. **执行 JavaScript 程序**

   运行以下命令启动 `WQBookDownloader.js` 脚本：

   ```bash
   node WQBookDownloader.js
   ```

   运行后，会提示你输入 `bid`：

   ```
   请输入bid:
   ```

   输入 `bid` 后，请按以下步骤操作：

   - 如果是初次运行，程序会使浏览器打开，并提示你手动完成登录操作，然后保存登录状态。
   - 登录完成后，程序会继续运行，并自动截图每一页内容，保存到指定文件夹中。
   - 如果之前已经保存了登录状态，程序会自动加载已保存的登录状态，并跳过登录步骤。

2. **生成初步的 PDF**

   - 程序会将截图保存为 PNG 格式，并生成一个初步的 PDF 文件（未包含目录）。

3. **添加目录**

   生成初步 PDF 文件后，程序会自动运行 `add_toc.py` 脚本，为 PDF 文件添加目录。你也可以手动运行以下命令：

   ```bash
   python add_toc.py "./<bid>_<bookName>.pdf" "./<bid>_<bookName>_images/catalog.json" "./<bid>_<bookName>_toc.pdf"
   ```

   - `<bid>`: 你输入的 bid。
   - `<bookName>`: 自动获取的书名。

4. **查看结果**

   最终的 PDF 文件会带有目录，并保存在当前目录下：

   ```
   ./<bid>_<bookName>_toc.pdf
   ```

## 注意事项

- 本程序仅用于个人学习和交流，禁止用于商业用途。
- 如果出现任何问题，可以在 Github 仓库中提交 issue，共同讨论解决方案。不过大概率本人没时间维护这个随便写的项目 🥹

您现在已经完成了基本的设置，并了解了如何使用 WQBookDownloader 项目。希望这个项目对您的学习有所帮助！如果有任何问题或建议，请随时联系我。
