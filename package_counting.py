from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
root=Path(__file__).resolve().parent
for folder in ['Exilir_SoftAP_Logger','Exilir_Step_Counter']:
    with ZipFile(root.parent/(folder+'.zip'),'w',ZIP_DEFLATED) as z:
        for p in (root/folder).rglob('*'):
            if p.is_file():z.write(p,p.relative_to(root))
with ZipFile(root.parent/'Hands_On_Lab_Exilir.zip','w',ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.exe','.obj','.pdb']:
            z.write(p,p.relative_to(root.parent))
    z.write(root.parent/'template_hasil.csv','template_hasil.csv')
print('Updated 3 ZIP packages.')
