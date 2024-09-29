# 序言
项目的起因是因为在Zlibrary找书的时候，发现一些PDF扫描格式的书，在阅读做笔记的时候特别不方便。
因此，我想开发一个软件，能够将PDF扫描格式的书转换为电子书格式，并提供便捷的阅读方式。

# 使用的技术
项目使用了Python语言，主要使用了以下技术：
- [MinerU](https://github.com/opendatalab/MinerU) 把PDF转换成Markdown格式
- markdown 解析markdown文件,转换成HTML格式
- EbookLib   生成电子书

# 使用过程
1. 下载MinerU，并安装好依赖 详见MinerU的安装说明
```shell
pip install -U magic-pdf[full] --extra-index-url https://wheels.myhloli.com
pip install -r requirements.txt
```
    - 下载模型
    - 配置环境变量

2. 把PDF转换成Markdown格式
```shell
magic-pdf -p "C:\Users\jerri\Downloads\金融的哲学.pdf" -o ./ -m auto
```
3. 把转换好的Markdown文件转换成HTML格式