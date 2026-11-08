# Li Hu · Academic Homepage

一个采用 Jon Barron 式单页信息结构的学术主页。页首支持个人照片，论文列表使用纯文字。原创页面实现，无外部字体、JavaScript 和前端框架，断网也可浏览。

## GitHub 仓库与当前状态

仓库：<https://github.com/f000x0/f000x0.github.io>，主页项目位于 **`main` 分支**。

此仓库只保存新学术主页，使用独立的提交历史。旧博客、笔记及其全部历史保存在私有仓库 <https://github.com/f000x0/blog-notes-archive>。主页仓库保持 **Private**，尚未启用 GitHub Pages。`Check homepage` 工作流自动构建和检查；`Publish homepage when public` 工作流在私有仓库中跳过发布。

GitHub Pages 网站的可见性与代码仓库的可见性不是同一件事。当前阶段只同步私有代码，继续使用本地预览。

## 本地预览

**macOS：双击 `启动主页.command`。** 终端会显示本地地址，并自动打开默认浏览器。默认地址是 <http://localhost:8765>；端口被占用时会自动使用下一个可用端口。预览仅监听本机地址。

也可以在项目文件夹运行：

```sh
python3 serve.py
```

在终端按 `Ctrl+C` 停止预览。重复运行启动脚本会复用本项目已经运行的服务。

不启动服务也可以双击 `index.html` 查看。建议使用本地服务预览。

## 修改内容

主要编辑 **`data/profile.json`**。预览服务运行时，修改保存后刷新浏览器即可重新生成页面。

| 字段 | 内容 |
| --- | --- |
| `name` / `email` / `slogan` | 姓名、邮箱、主页标语（斜体显示） |
| `photo` / `photo_alt` | 个人照片路径和替代文本；路径留空可隐藏照片 |
| `study_year` / `phd_statement` | 硕士年级与博士求学意向 |
| `research_statement` / `engineering_statement` | 从 CTF pwn 学习经历引出的逆向工程与软件工程研究问题；支持 `**加粗**` |
| `research_interests` | 研究方向资料字段，目前不在页面中单独展示 |
| `advisors` | 导师及其主页 |
| `links` | Google Scholar、GitHub、ORCID；留空的链接不会显示；`cv` 字段不在主页中展示 |
| `publications` | 所有论文及其作者、年份、状态、链接 |
| `services` / `awards` | 审稿服务与荣誉 |
| `security_statement` | 漏洞发现的简短说明 |
| `vulnerabilities` | CVE/CNVD 编号；每项包含 `id` 和可选的 `url` |
| `updated` | 页脚更新月份 |

论文条目中：

- 仅展示已发表／已录用和大修中的论文，显示顺序遵循 `publications` 数组。调整顺序时，移动整个论文对象即可；页面不做自动排序。
- `status: "published"` 表示已发表或已录用；`"major_revision"` 表示大修；`"under_review"` 表示在审，该状态的条目不会展示。后续更新状态并重新生成后，页面会自动调整展示。
- 大修稿件展示完整投稿会议或期刊名称，并明确标记 Submitted to 和 Major revision。
- 每篇仅显示已填写真实链接的 `[paper]` 或 `[code]`；空值对应的选项隐藏。两个链接都有时使用 `/` 分隔；两个都没有时不显示链接行。
- 作者姓名末尾 `*` 和 `†` 分别标记共同一作和通讯作者；姓名 `Li Hu` 自动加粗。
- 论文只展示标题、作者、会议或期刊及 `[paper] / [code]`；不展示 summary 和 BibTeX。旧的 `summary`、`type`、`doi` 字段可保留作资料，不影响页面。
- `venue_full` 填写完整会议或期刊名称，`venue` 填写缩写。页面显示全称及括号内的缩写；已发表论文显示年份。在审或大修稿件也必须填写全称。`doi` 可选。

主页不展示 CV 链接。原 CV 文件保留在 `assets/Li_Hu_CV.pdf`。

替换照片时，覆盖 `assets/profile.jpg`，并设置合适的 `photo_alt`。目前照片来自 Li Hu 的 Google Scholar 主页，已下载为本地图片，无需访问外部服务即可显示。也可以把新照片放进 `assets/` 后修改 `photo` 字段。建议使用方形照片，页面会自动裁剪。

修改视觉样式：编辑 `assets/styles.css`。文件顶部提供纸张色、文字色和强调色变量。

页面统一使用本地托管的 Lato 字体（常规、粗体和斜体），保存在 `assets/fonts/`，附带 SIL Open Font License。无需访问 Google Fonts，也可离线显示。页面宽度上限为 800px；论文部分参考 Jon Barron 的 14px 文字排版：黑色加粗标题、作者（本人加粗）、斜体会议全称与缩写、年份、链接。论文没有图片、编号、summary 和 BibTeX，顺序由资料文件控制。照片置于简介右上方，后续文字使用整行宽度。

Publications、漏洞编号、Academic Service 与 Selected Honors 使用黑色实心方块无序列表。标语使用 Lato 斜体，与正文区分。

联系方式使用内嵌 SVG 图标，无需图标字体或外部 CDN。图标与文字标签一起显示，辅助技术忽略装饰性图标；`build.py` 中的 `icon()` 可调整图形。论文链接使用 `[paper] / [code]` 纯文字形式。

如果不使用预览服务，修改 JSON 后运行：

```sh
python3 build.py
```

这会更新 `index.html`。

## 文件结构

```text
li-hu-homepage/
├── index.html                # 已生成，可直接打开的网页
├── data/profile.json         # 日常维护的个人资料和论文
├── assets/
│   ├── styles.css            # 样式和移动端适配
│   ├── favicon.svg           # 无文字的蓝色几何立方体站点图标
│   ├── profile.jpg           # 个人照片，来自 Google Scholar 主页
│   └── Li_Hu_CV.pdf          # 保留的原 CV 文件，主页不展示链接
├── build.py                  # 静态页面生成器，仅用 Python 标准库
├── serve.py                  # 本地预览服务，仅用 Python 标准库
├── 启动主页.command           # macOS 双击启动入口
└── .local/                   # 本地服务日志与状态，不属于网站
```

## 内容来源与后续完善

个人经历、论文作者及稿件状态依据提供的 `Li_Hu_CV_USTC.pdf` 整理；研究简介和标语为根据研究方向撰写的主页文案。完整 CV 保留原文件。

主页展示 8 篇已发表或录用论文和 2 篇大修稿件，隐藏 Under review 稿件，并严格遵循资料文件中的顺序。当前资料沿用此前的一作优先顺序，可自行调整。Vulnerability Disclosures 以一句话说明漏洞发现总量，按 CVE、CNVD 分组展示 CV 中明确列出的 8 个编号。CV 注明有 10+ 项发现，但没有列出其余编号；补充编号时直接添加到 `vulnerabilities` 即可。Education 不再展示，背景为纯白色。论文链接仅填写能匹配标题和作者的公开记录；没有确认的链接保留空值。GitHub 个人链接已填写；Scholar 和 ORCID 链接可以在 `links` 中补上。

大修稿件展示目标 venue 和明确的稿件状态，不显示为正式发表信息。

## 同步到私有仓库

修改后先运行 `python3 build.py`，再提交并推送：

```sh
git add .
git commit -m "Update academic homepage"
git push origin main
```

`.local/`、Python 缓存和 `_site/` 已忽略。原来的博客历史保存在独立的 `blog-notes-archive` 仓库中。本地 `notes-archive` remote 指向它，`origin` 指向新主页。

## 之后公开并上线 GitHub Pages

目前没有公开网站。准备好公开时再执行以下操作：

1. 将仓库可见性改为 Public。
2. 在仓库 Settings → Pages 中，将 Source 设置为 GitHub Actions。
3. 在 `main` 分支推送一次更新，触发 `Publish homepage when public`。
4. 首次部署如受 environment 分支规则限制，在 Settings → Environments → github-pages 中允许 `main` 分支部署。
5. 发布后的地址为 <https://f000x0.github.io/>。

旧博客的 `CNAME` 不包含在这个分支生成的网站中，因此初次发布使用上面的 GitHub 默认域名。

发布工作流只导出 `index.html`、`assets/` 和 `.nojekyll`，不发布维护用的原始资料、服务脚本或本地状态。手动导出命令为 `python3 build.py --output-dir _site`。

信息结构参考 [Jon Barron 的个人主页](https://jonbarron.info/)。此项目为独立实现。
