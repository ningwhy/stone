"""Persist inspected held-object masks; source and SAM files stay untouched."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'art/calibration.json';c=json.loads(p.read_text())
restore={
'zhang-portrait':[[69,479],[77,469],[92,465],[108,473],[116,496],[181,500],[249,494],[252,485],[266,483],[278,489],[286,520],[321,612],[348,666],[383,727],[379,735],[337,730],[243,718],[198,724],[161,644],[130,597],[101,548],[80,508]],
'zhang-chibi':[[385,565],[429,443],[440,408],[476,412],[528,423],[556,415],[561,408],[569,402],[580,405],[590,413],[588,421],[559,450],[521,568],[478,574],[422,565],[400,571]],
'leng-portrait':[[350,809],[414,739],[544,624],[554,630],[559,646],[565,649],[575,660],[577,677],[586,680],[454,750],[422,767],[360,816]],
'leng-chibi':[[335,656],[374,602],[422,509],[433,516],[439,517],[446,529],[454,528],[464,539],[466,548],[475,552],[477,561],[485,568],[488,576],[387,621],[342,659]]}
for a in c['assets']:
 if a['id'] in restore:a['restorePolygons']=[restore[a['id']]]
p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
print('Retained newspapers and fans in four inspected character assets.')
