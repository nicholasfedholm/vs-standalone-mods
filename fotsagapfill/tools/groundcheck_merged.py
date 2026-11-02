"""Run groundcheck against the merged output (work/merged_ex/all) instead of work/stage."""
import os, sys, runpy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'work'))
os.environ['GC_TMP'] = os.path.join(ROOT, 'work', '_gc_merged')
import groundcheck
groundcheck.STAGE = os.path.join(ROOT, 'work', 'merged_ex', 'all')
groundcheck.main()
