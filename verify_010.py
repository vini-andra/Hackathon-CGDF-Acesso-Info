import json

GABARITO = '/home/vinicius/sistema_identificacao_dados_sensiveis/resultados/gabarito_010.json'
RELATORIO = '/home/vinicius/sistema_identificacao_dados_sensiveis/resultados/relatorio_dados_teste_010_v2.json'

def main():
    try:
        with open(GABARITO) as f: g = json.load(f)
        with open(RELATORIO) as f: r = json.load(f)
    except Exception as e:
        print(e)
        return

    truth = {item['id']: item['sensivel'] for item in (g.get('respostas') or g.get('dados', []))}
    pred = {item['id']: item['classificacao_predita'] for item in r['resultados']}

    vp, vn, fp, fn = [], [], [], []

    for _id, real in truth.items():
        p = pred.get(_id, False)
        if real and p: vp.append(_id)
        elif not real and not p: vn.append(_id)
        elif not real and p: fp.append(_id)
        elif real and not p: fn.append(_id)

    print(f"VP: {len(vp)} IDs: {sorted(vp)}")
    print(f"VN: {len(vn)} IDs: {sorted(vn)}")
    print(f"FP: {len(fp)} IDs: {sorted(fp)}")
    print(f"FN: {len(fn)} IDs: {sorted(fn)}")
    
    acc = (len(vp) + len(vn)) / len(truth)
    print(f"Acuracia: {acc:.2%}")

if __name__ == '__main__':
    main()
