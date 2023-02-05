# mkdocs-statistics-plugin

一个用于 mkdocs 文档统计的插件，包括全局页面数、字数、代码块行数，单页字数、代码行数、预计阅读时间等。

预览：<https://note.tonycrane.cc/>（只有带评论的页面有单页统计）

## 安装
可以通过 pypi 直接安装：
```shell
$ pip install mkdocs-statistics-plugin
```

也可以从源码安装

```shell
$ git clone https://github.com/TonyCrane/mkdocs-statistics-plugin.git
$ cd mkdocs-statistics-plugin
$ pip install . # or pip install -e .
```

## 使用
- 在 mkdocs.yml 中启用插件：
    ```yaml
    plugins:
      - statistics
    ```

配置选项及解释：

| 选项 | 类型 | 默认值 | 解释 |
|:----|:----|:----|:----|
|`pages_placeholder`|str|`\{\{\s*pages\s*\}\}`|全局统计页面中页面数占位符（正则）|
|`words_placeholder`|str|`\{\{\s*words\s*\}\}`|全局统计页面中字数占位符（正则）|
|`codes_placeholder`|str|`\{\{\s*codes\s*\}\}`|全局统计页面中代码行数占位符（正则）|
|`page_statistics`|bool|`True`|是否在单页中显示统计信息|
|`page_check_metadata`|str||如果为空，则所有页面都显示；否则包含指定 metadata 才显示单页统计信息|
|`page_read_time`|bool|`True`|是否显示单页预计阅读时间|
|`page_template`|str||单页统计信息模板相对路径（相对 docs）|
|`words_per_minute`|int|`300`|每分钟预计阅读字数|
|`codelines_per_minute`|int|`80`|每分钟预计阅读代码行数|

### 几种使用方式
#### 全局统计页
例如在首页显示全局统计信息。需要在该页面的元数据中添加：
```yaml
---
statistics: True
---
```
然后在该页中需要的部分添加占位符，例如：
```markdown
本站共有 {{ pages }} 个页面，{{ words }} 个字，{{ codes }} 行代码。
```

#### 单页统计
需要按照上述选项填写好配置（默认开启单页统计，且~~应该可以~~适配 material 主题）。

如果 `page_check_metadata` 为空，则所有页面都显示单页统计信息；否则包含指定 metadata 才显示单页统计信息。例如在我自己的设置中，包含 `comment` 的页面才显示单页统计信息（且包含 `nostatistics` 的页面不显示统计信息）：
```yaml
plugins:
  - statistics:
      page_check_metadata: comment
```

### 高级用法
#### 自定义单页统计模板
可以通过 `page_template` 选项指定单页统计模板的相对路径（相对 docs）。这个模板会被插入到 markdown 源码的一级标题下方，会传入 `words` `code_lines` `read_time`（可选）三个模板参数。

自定义的话可以参考提供的模板。

#### 阅读时间
可以通过 `page_read_time` 选项控制是否显示单页预计阅读时间。默认开启。

阅读时间的计算方式是分别计算字数和代码行数的阅读时间，然后取二者之和。可以通过 `words_per_minute` 和 `codelines_per_minute` 选项分别设置每分钟预计阅读字数和代码行数。默认情况下分别为 300 和 80，对于技术类文章这样的设置基本合理，对于其他类型例如文学类文章每分钟阅读字数应该提高到 400~600 左右较为合理。

~~计划添加页面元信息选项来为单页设置特定的阅读时间。（咕咕咕）~~

#### 字数统计细节
本插件的字数统计细节为：一个英文单词（包括数字）算一个字，一个中文汉字算一个字，标点都不算字；代码块（带语言的三反引号语法）中所有内容都不计入字数，而是计入代码块行数统计。

具体细节见 plugin.py 中的 \_clean\_markdown 方法。

## 开发
可能很不稳定（反正至少我能跑起来），有任何问题欢迎 issue 提出。同时页欢迎任何 PR，尽管提就好。