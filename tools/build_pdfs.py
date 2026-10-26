#!/usr/bin/env python3
"""Build from an isolated copy and compare extracted text with supplied PDFs."""
from pathlib import Path
import subprocess,shutil,re,concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build';BUILD.mkdir(exist_ok=True)
DOCS={'main':'manuscript.pdf','supplementary':'ESM_1.pdf','titlepage_mtap':'title_page.pdf','cover_letter_mtap':'cover_letter.pdf'}
def text(p):return re.sub(r'\s+',' ',subprocess.check_output(['pdftotext',str(p),'-'],text=True)).strip()
def pages(p):return int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(p)],text=True),re.M).group(1))
def run(doc):
 work=BUILD/doc;work.mkdir(exist_ok=True)
 for f in (ROOT/'source').iterdir():
  if f.is_file():shutil.copy2(f,work/f.name)
 commands=[['pdflatex','-interaction=nonstopmode','-halt-on-error',doc+'.tex']]
 if doc in ('main','supplementary'):commands.append(['bibtex',doc])
 commands += [['pdflatex','-interaction=nonstopmode','-halt-on-error',doc+'.tex']]*2
 with (BUILD/(doc+'-build.txt')).open('w') as log:
  for cmd in commands:subprocess.run(cmd,cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True)
 old=ROOT/'submission'/DOCS[doc];new=work/(doc+'.pdf')
 if pages(old)!=pages(new) or text(old)!=text(new):raise RuntimeError('Rebuild differs from supplied PDF: '+doc)
 return f'PASS: {doc}: {pages(new)} pages; extracted text matches supplied PDF.'
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for result in pool.map(run,DOCS):print(result,flush=True)
