from docstr_md.python import PySoup, compile_md
from docstr_md.src_href import Github

src_href = Github('https://github.com/dsbowen/flask-download-btn')

path = 'flask_download_btn/__init__.py'
soup = PySoup(path=path, parser='sklearn', src_href=src_href)
compile_md(soup, compiler='sklearn', outfile='docs_md/manager.md')

path = 'flask_download_btn/download_btn_mixin.py'
soup = PySoup(path=path, parser='sklearn', src_href=src_href)
soup.rm_properties()
soup.objects[-1].rm_methods('handle_form_functions', 'create_file_functions')
soup.import_path = 'flask_download_btn'
compile_md(soup, compiler='sklearn', outfile='docs_md/download_btn_mixin.md')