# Usage with Notebooks

Bu rehber, frameworkün notebook ile tek varlık ve çoklu portföy akışında nasıl çalıştırılacağını gösterir.

## 1) Ortam Kurulumu

```bash
make bootstrap
make lint
make test
make smoke
```

Notebook çalıştırmak için:

```bash
python -m pip install jupyterlab
jupyter lab notebooks/real_data_workflow.ipynb
```

## 2) Çalıştırılacak Notebook

- `notebooks/real_data_workflow.ipynb`

Notebook içeriği:
- config/custom parametre seçimi
- asset discovery (ccxt varsa doğrudan, değilse fallback liste)
- market/news/macro ingestion (public endpoint örnekleri)
- feature engineering ve inceleme
- rolling window optimize/backtest (OOS ayrımı)
- signal -> intent -> risk -> portfolio akışı (`TradeFlow`)
- tek varlık ve çoklu portföy metrik özeti

## 3) Fail-Proof Onboarding Notu

- Ağ veya üçüncü taraf kaynak erişimi yoksa notebook hücreleri açıklayıcı hata üretir.
- CI tarafında notebook smoke kontrolü `make smoke` içindeki `scripts/notebook_smoke_check.py` ile doğrulanır.
