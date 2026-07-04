#!/usr/bin/env python3
"""Download HuggingFace datasets used by FoodBridge."""

from pathlib import Path

from huggingface_hub import hf_hub_download, list_repo_files

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "huggingface"

SUPPLY_CHAIN_REPO = "IshaanPotle27/global-food-supply-chain-models-and-data"
GDELT_REPO = "Laurieqq/gdelt-food-security-data"


def download_supply_chain() -> Path:
    path = hf_hub_download(
        repo_id=SUPPLY_CHAIN_REPO,
        filename="food_supply_chain_data.csv",
        repo_type="dataset",
        local_dir=str(DATA / "supply_chain"),
    )
    return Path(path)


def download_gdelt() -> list[Path]:
    files = sorted(
        f
        for f in list_repo_files(GDELT_REPO, repo_type="dataset")
        if f.startswith("data/gdelt_") and f.endswith(".csv")
    )
    paths: list[Path] = []
    for filename in files:
        path = hf_hub_download(
            repo_id=GDELT_REPO,
            filename=filename,
            repo_type="dataset",
            local_dir=str(DATA / "gdelt"),
        )
        paths.append(Path(path))
    return paths


def main() -> None:
    print("Downloading supply chain dataset...")
    sc = download_supply_chain()
    print(f"  -> {sc}")

    print("Downloading GDELT food security dataset...")
    gdelt = download_gdelt()
    print(f"  -> {len(gdelt)} files in {DATA / 'gdelt'}")


if __name__ == "__main__":
    main()
