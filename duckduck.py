from duckduckgo_search import DDGS
from pathlib import Path
from hashlib import md5
import requests, itertools, shutil
from tqdm import tqdm

def scrape_images(
    class_queries: dict[str, list[str]],
    root_dir: str | Path = "dataset",
    max_per_query: int   = 100,
    img_size: tuple[int, int] | None = None,  # (w, h) → фильтр по размеру
    region: str = "wt-wt",                    # world-wide
):
    """
    Скачивает изображения DuckDuckGo по запросам.
      class_queries = {"cats": ["cute kitten", ...], "dogs": ["gsd puppy", ...]}
      root_dir      — корень датасета (будет создан).
      max_per_query — ограничение DDG-результатов на один запрос.
      img_size      — минимальное (width, height); None → любое.
    """

    root = Path(root_dir);  root.mkdir(exist_ok=True, parents=True)

    def _download(url: str, fname: Path):
        try:
            r = requests.get(url, timeout=10, stream=True, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            with fname.open("wb") as f:
                shutil.copyfileobj(r.raw, f)
            return True
        except Exception:
            return False

    with DDGS() as ddgs:
        for cls, queries in class_queries.items():
            cls_dir = root / cls
            cls_dir.mkdir(exist_ok=True)
            print(f"\n⬇️  Класс “{cls}” — {len(queries)} запрос(ов)")

            for q in queries:
                seen_hashes = set()    # чтобы не сохранять дубликаты из одного запроса
                print(f"  » {q!r}")

                for res in itertools.islice(
                        ddgs.images(q, region=region, safesearch="off", max_results=max_per_query),
                        max_per_query):

                    url = res.get("image") or res.get("thumbnail")   # иногда thumbnail есть, image — нет
                    if not url:
                        continue

                    # Фильтр по размеру (если задан)
                    if img_size:
                        w, h = res.get("width", 0), res.get("height", 0)
                        if w < img_size[0] or h < img_size[1]:
                            continue

                    # Формируем имя файла по md5(url).ext
                    ext  = url.split("?")[0].split(".")[-1][:5]  # jpeg?size= -> jpeg
                    name = f"{md5(url.encode()).hexdigest()}.{ext}"
                    file = cls_dir / name

                    # Пропускаем, если такой уже скачан
                    if file.exists() or name in seen_hashes:
                        continue

                    ok = _download(url, file)
                    if ok:
                        seen_hashes.add(name)

                print(f"    сохранено: {len(seen_hashes)} файл(ов)")

    print("\n✅  Готово!")

# ------------------- пример вызова -------------------

if __name__ == "__main__":
    queries = {
        "bmw_x6": [
            "bmw x6 car",
            "bmw x6 2022",
            "bmw x6 suv",
            "bmw x6 side view",
            "bmw x6 interior",
            "bmw x6 on the road"
        ],
        "ford_mustang": [
            "ford mustang car",
            "ford mustang 2021",
            "ford mustang gt",
            "ford mustang red",
            "ford mustang convertible",
            "ford mustang interior"
        ],
    }
    scrape_images(
        class_queries = queries,
        root_dir      = "cars_dataset",
        max_per_query = 100,
        img_size      = (200, 200)      # минимальный размер
    )