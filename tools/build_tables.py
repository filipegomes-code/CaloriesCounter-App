"""Converte as tabelas de composição de alimentos para os JSON que a app usa.

Uso:
  python3 tools/build_tables.py insa  caminho/insa_tca.xlsx          > data/insa.json
  python3 tools/build_tables.py usda  caminho/pasta_csv_sr_legacy    > data/usda.json

INSA: https://portfir.insa.min-saude.pt/ (Composição de Alimentos > Descarregar Excel). Precisa de openpyxl.
USDA: https://fdc.nal.usda.gov/download-datasets (SR Legacy, CSV). Só biblioteca padrão.

Formato de saída: {"fonte", "versao", "alimentos": [[id, nome, kcal, proteina, hidratos, gordura, fibra], ...]}
Valores por 100 g. Hidratos = hidratos disponíveis (sem fibra), como nos rótulos europeus.
"""
import csv, json, os, sys


def r(x):
    try:
        return round(float(x), 1)
    except (TypeError, ValueError):
        return 0.0


def insa(path):
    import openpyxl
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    rows = ws.iter_rows(values_only=True)
    next(rows)
    head = [str(h or "").split("\n")[0].strip() for h in next(rows)]
    col = {name: head.index(name) for name in ("Cod", "Nome do alimento", "Energia", "Proteínas", "Hidratos de carbono", "Lípidos", "Fibra")}
    out = []
    for row in rows:
        if not row[col["Cod"]] or not row[col["Nome do alimento"]]:
            continue
        out.append([str(row[col["Cod"]]).strip(), " ".join(str(row[col["Nome do alimento"]]).split()),
                    round(r(row[col["Energia"]])), r(row[col["Proteínas"]]), r(row[col["Hidratos de carbono"]]),
                    r(row[col["Lípidos"]]), r(row[col["Fibra"]])])
    out.sort(key=lambda a: a[1])
    return {"fonte": "Base de Dados da Composição de Alimentos. Instituto Nacional de Saúde Doutor Ricardo Jorge, I. P. - INSA",
            "versao": ws.title.split("_v")[-1].strip() if "_v" in ws.title else ws.title, "alimentos": out}


def usda(folder):
    def read(name):
        with open(os.path.join(folder, name), newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    skip = {"3"}  # Baby Foods
    foods = {f["fdc_id"]: f["description"] for f in read("food.csv") if f["food_category_id"] not in skip}
    want = {"1008": "kcal", "1003": "p", "1005": "h", "1004": "g", "1079": "f"}
    vals = {}
    for n in read("food_nutrient.csv"):
        k = want.get(n["nutrient_id"])
        if k and n["fdc_id"] in foods:
            vals.setdefault(n["fdc_id"], {})[k] = r(n["amount"])
    out = []
    for fid, desc in foods.items():
        v = vals.get(fid, {})
        if "kcal" not in v:
            continue
        fib = v.get("f", 0.0)
        out.append([fid, desc, round(v["kcal"]), v.get("p", 0.0), round(max(0.0, v.get("h", 0.0) - fib), 1), v.get("g", 0.0), fib])
    out.sort(key=lambda a: a[1])
    return {"fonte": "USDA FoodData Central, SR Legacy", "versao": "2018-04", "alimentos": out}


if __name__ == "__main__":
    kind, path = sys.argv[1], sys.argv[2]
    data = insa(path) if kind == "insa" else usda(path)
    json.dump(data, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(data['alimentos'])} alimentos", file=sys.stderr)
