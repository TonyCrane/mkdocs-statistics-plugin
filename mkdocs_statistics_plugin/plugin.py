import os
import re
import logging
from datetime import datetime

from jinja2 import Template

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.pages import Page
from mkdocs.structure.files import Files
from mkdocs.utils.meta import get_data

from typing import Any, Dict, Optional, Tuple

PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(PLUGIN_DIR, 'templates/page_statistics.html')

log = logging.getLogger('mkdocs.mkdocs_statistics_plugin')

class StatisticsPlugin(BasePlugin):
    config_scheme = (
        ('enabled', config_options.Type(bool, default=True)),
        ('pages_placeholder', config_options.Type(str, default=r'\{\{\s*pages\s*\}\}')),
        ('words_placeholder', config_options.Type(str, default=r'\{\{\s*words\s*\}\}')),
        ('codes_placeholder', config_options.Type(str, default=r'\{\{\s*codes\s*\}\}')),
        ('images_placeholder', config_options.Type(str, default=r'\{\{\s*images\s*\}\}')),
        ('page_statistics', config_options.Type(bool, default=True)),
        ('page_check_metadata', config_options.Type(str, default="")),
        ('page_read_time', config_options.Type(bool, default=True)),
        ('page_images', config_options.Type(bool, default=True)),
        ('page_template', config_options.Type(str, default="")),
        ('words_per_minute', config_options.Type(int, default=300)),
        ('codelines_per_minute', config_options.Type(int, default=80)),
        ('ignore_languages', config_options.Type(list, default=["mermaid", "math"])),
        ('include_path', config_options.Type(str, default="")),
        ('exclude_path', config_options.Type(str, default="")),
    )

    enabled = True
    pages = 0
    words = 0
    codes = 0

    is_serving = False
    def on_startup(self, command, **kwargs):
        self.is_serving = command == 'serve'

    def on_config(self, config: config_options.Config, **kwargs) -> Dict[str, Any]:
        page_template = self.config.get("page_template")
        if page_template == "":
            with open(TEMPLATE_DIR, 'r', encoding='utf-8') as file:
                self.template = file.read()
        else:
            with open(config['docs_dir'] + '/' + page_template, 'r', encoding='utf-8') as file:
                self.template = file.read()
        return config
    
    def on_files(self, files: Files, *, config: config_options.Config) -> Optional[Files]:
        self.pages = 0
        self.words = 0
        self.codes = 0
        self.images = 0

        include_path = self.config.get('include_path')
        exclude_path = self.config.get('exclude_path')

        material_blog = config.get('plugins').get('material/blog')
        if material_blog:
            blog_config = material_blog.config
            draft_always = blog_config.get('draft')
            draft_on_serve = blog_config.get('draft_on_serve')
            draft_if_future_date = blog_config.get('draft_if_future_date')

        for file in files.documentation_pages():
            src_path = file.src_path
            
            if include_path and not re.match(include_path, src_path):
                continue
            if exclude_path and re.match(exclude_path, src_path):
                continue

            with open(config['docs_dir'] + '/' + src_path, encoding='utf-8-sig', errors='strict') as f:
                source = f.read()
            markdown, meta = get_data(source)

            post_date = meta.get('date')
            if post_date and material_blog:  # date is require if it's a blog post
                now = datetime.now()
                is_draft = meta.get('draft', False) or (draft_if_future_date and post_date > now)
                if draft_always:
                    {}
                elif not is_draft:
                    {}
                elif self.is_serving and draft_on_serve:
                    {}
                else: continue

            self.pages += 1
            self._words_count(markdown)
            
        return files
    
    def on_page_markdown(
        self, markdown: str, page: Page, config: config_options.Config, files, **kwargs
    ) -> str:
        if not self.enabled:
            return markdown
        
        if not self.config.get('enabled'):
            return markdown

        if page.meta.get("nostatistics"):
            return markdown
        
        if page.meta.get("statistics"):

            log.info(f"pages: {self.pages}, words: {self.words}, codes: {self.codes}, images: {self.images}")

            markdown = re.sub(
                self.config.get("pages_placeholder"),
                str(self.pages),
                markdown,
                flags=re.IGNORECASE,
            )

            markdown = re.sub(
                self.config.get("words_placeholder"),
                str(self.words),
                markdown,
                flags=re.IGNORECASE,
            )

            markdown = re.sub(
                self.config.get("codes_placeholder"),
                str(self.codes),
                markdown,
                flags=re.IGNORECASE,
            )

            markdown = re.sub(
                self.config.get("images_placeholder"),
                str(self.images),
                markdown,
                flags=re.IGNORECASE,
            )

        if self.config.get("page_statistics") == False:
            return markdown

        if page.meta.get("hide") and "statistics" in page.meta["hide"]:
            return markdown
        
        include_path = self.config.get('include_path')
        exclude_path = self.config.get('exclude_path')
        src_path = page.file.src_path
        if include_path and not re.match(include_path, src_path):
            return markdown
        if exclude_path and re.match(exclude_path, src_path):
            return markdown

        page_check_metadata = self.config.get("page_check_metadata")
        if page_check_metadata == "" or page.meta.get(page_check_metadata):
            code_lines = 0
            images = len(re.findall("<img.*>", markdown)) + len(re.findall(r'!\[[^\]]*\]\([^)]*\)', markdown))
            chinese, english, codes = self._split_markdown(markdown)
            words = len(chinese) + len(english.split())
            for code in codes:
                code_lines += len(code.splitlines()) - 2
            
            lines = markdown.splitlines()
            h1 = -1
            for idx, line in enumerate(lines):
                if re.match(r"\s*# ", line): # ATX syntax
                    h1 = idx
                    break
                if re.match(r"=+\s*$", line) and idx > 0 and lines[idx - 1]: # Setext syntax
                    h1 = idx
                    break
            try:
                read_time = round(
                    words / self.config.get("words_per_minute") + \
                    code_lines / self.config.get("codelines_per_minute")
                )
            except ZeroDivisionError:
                read_time = 0

            page_statistics_content = Template(self.template).render(
                words = words,
                code_lines = code_lines,
                images = images,
                read_time = read_time,
                page_read_time = self.config.get("page_read_time"),
                page_images = self.config.get("page_images"),
                config = config,
            )

            lines.insert(h1 + 1, page_statistics_content)
            markdown = "\n".join(lines)

            # Add to page meta information, for developers
            page.meta["statistics_page_words"] = words
            page.meta["statistics_page_codes_lines"] = code_lines
            page.meta["statistics_page_images"] = images
            page.meta["statistics_page_read_time"] = read_time

        return markdown

    def _words_count(self, markdown: str) -> None:
        self.images += len(re.findall("<img.*>", markdown)) + len(re.findall(r'!\[[^\]]*\]\([^)]*\)', markdown))
        chinese, english, codes = self._split_markdown(markdown)
        self.words += len(chinese) + len(english.split())
        for code in codes:
            self.codes += len(code.splitlines()) - 2

    def _split_markdown(self, markdown: str) -> tuple:
        markdown, codes = self._clean_markdown(markdown)
        chinese = "".join(re.findall(r'[\u4e00-\u9fa5]', markdown))
        english = " ".join(re.findall(r'[a-zA-Z0-9]*?(?![a-zA-Z0-9])', markdown))
        return chinese, english, codes
    
    def _filter_out_diagrams(self, codes: list[str]) -> list[str]:
        ret = []
        for code in codes:
            res = re.match(r"(`{3,}|~{3,})(?P<lang>\w*)", code.splitlines()[0])
            lang = res.group("lang") if res else ""
            if lang not in self.config.get("ignore_languages"):
                ret.append(code)
        return ret
    
    def _clean_markdown(self, markdown: str) -> Tuple[str, list]:
        codes = re.findall(r'(~~~[^\n].*?~~~|```[^\n].*?```)', markdown, re.S)
        codes = self._filter_out_diagrams(codes)
        markdown = re.sub(r'(~~~[^\n].*?~~~|```[^\n].*?```)', '', markdown, flags=re.DOTALL | re.MULTILINE)
        markdown = re.sub(r'<!--.*?-->', '', markdown, flags=re.DOTALL | re.MULTILINE)
        markdown = markdown.replace('\t', '    ')
        markdown = re.sub(r'[ ]{2,}', '    ', markdown)
        markdown = re.sub(r'^\[[^]]*\][^(].*', '', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'{#.*}', '', markdown)
        markdown = markdown.replace('\n', ' ')
        markdown = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', markdown)
        markdown = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', markdown)
        markdown = re.sub(r'</?[^>]*>', '', markdown)
        markdown = re.sub(r'[#*`~\-–^=<>+|/:]', '', markdown)
        markdown = re.sub(r'\[[0-9]*\]', '', markdown)
        markdown = re.sub(r'[0-9#]*\.', '', markdown)
        return markdown, codes
