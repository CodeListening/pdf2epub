import os.path

import markdown
from ebooklib import epub

# 每个章节单独保存为 HTML 文件
def md_to_html(md_content):
    # 转换为 HTML
    html_content = markdown.markdown(md_content,
                                      extensions=["mdx_math"],
                                      extension_configs={
                                          "mdx_math": {
                                              "enable_dollar_delimiter": True,
                                          }
                                      })
    # # 保存为 HTML 文件
    # html_file = md_file.replace('.md', '.html')
    return html_content

# html 转换为 epub 章节
def html_to_epub_chapter(title, html_content):
    # print(html_content)
    chapter = epub.EpubHtml(title=title, lang="cn", file_name=title+'.xhtml')
    chapter.content = html_content
    return chapter


def save_md_to_epub(md_file, epub_file):
    # 使用 # 分章节
    # 读取 Markdown 文件内容
    content = open(md_file, 'r', encoding='utf-8').readlines()
    all_chapters = []
    chapter_title = ""
    chapter =[]

    for i in range(len(content)):
        if content[i].startswith('#'):
            # 保存上一章节
            if chapter_title!="" or len(chapter)>-1:
                all_titles = [c[0] for c in all_chapters]
                if chapter_title in all_titles:
                    chapter_title = chapter_title + str(all_titles.count(chapter_title))
                all_chapters.append((chapter_title, chapter))
            chapter_title = content[i].strip('#').strip()
            # 创建章节对象
            chapter = [content[i]]
        else:
            chapter.append(content[i])

    # 保存最后一章节
    if chapter_title!="" or len(chapter)>-1:
        all_titles = [c[0] for c in all_chapters]
        if chapter_title in all_titles:
            chapter_title = chapter_title + str(all_titles.count(chapter_title))
        all_chapters.append((chapter_title, chapter))

    # 转换为 epub 章节
    book = epub.EpubBook()
    book.set_identifier('id123456789')
    book.set_title('金融的哲学')
    book.set_language('zh')
    book.spine = ["nav"]

    # all_chapters = all_chapters[4:5]
    chapters = []


    for chapter_title, chapter in all_chapters:
        # 转换为 HTML
        html_content = md_to_html(''.join(chapter))
        # 保存为 HTML 文件
        html_file = md_file.replace('.md', '.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        # 转换为 epub 章节
        epub_chapter = html_to_epub_chapter(chapter_title, html_content)
        # 添加到 epub 书籍中
        book.add_item(epub_chapter)
        # book.toc.append((epub.Section(chapter_title), epub_chapter))
        if chapter_title!="":
            # print(chapter_title, epub_chapter.file_name, chapter_title)
            book.toc.append(epub.Link(chapter_title, chapter_title, epub_chapter.file_name))
        chapters.append(epub_chapter)

    # 添加图片
    # 获取图片文件夹
    img_folder = os.path.dirname(md_file)
    # print("img_folder:", img_folder)
    img_folder = os.path.join(img_folder, 'images')
    # 遍历所有图片文件
    for img_file in os.listdir(img_folder):
        img_path = os.path.join(img_folder, img_file)
        # print("img_file:", img_file)
        # print("img_path:", img_path)
        # 读取图片内容
        with open(img_path, 'rb') as f:
            img_content = f.read()
        # 添加到 epub 书籍中
        img_file_path = os.path.join('images', img_file)

        book.add_item(epub.EpubItem(
            uid="img"+img_file,
            file_name=img_file_path, media_type='image/jpeg', content=img_content))



    # 保存为 epub 文件
    book.spine = ["nav"] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # 保存为 epub 文件
    style = "BODY {color: white;}"
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style,
    )

    # add CSS file
    book.add_item(nav_css)
    epub.write_epub(epub_file, book, {})


if __name__ == '__main__':
    md_file = r"C:\Users\jerri\work\pythonProject\ocr-pdf\金融的哲学\auto\金融的哲学.md"
    epub_file = r"C:\Users\jerri\work\pythonProject\ocr-pdf\金融的哲学\auto\金融的哲学.epub"
    save_md_to_epub(md_file, epub_file)

