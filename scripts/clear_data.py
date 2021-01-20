import os
import glob
import shutil
from collections import defaultdict

GRAFANA_DATA_DIR = os.getenv('GRAFANA_DATA_DIR')


def main():
    d = defaultdict(list)
    paths = glob.glob(os.path.join(GRAFANA_DATA_DIR, 'account_*-*'))
    for p in paths:
        dt = os.path.basename(p)[8:].split('-')[0]
        d[dt].append(p)
    for paths in d.values():
        keep_path = max(paths)
        for p in paths:
            if p != keep_path:
                shutil.rmtree(p)


if __name__ == "__main__":
    main()
