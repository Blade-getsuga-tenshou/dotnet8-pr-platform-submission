import pandas as pd
from quality import check_build_linkage


def test_low_linkage_fails():
    builds = pd.DataFrame({"build_id": [1, 2, 3, 4, 5]})
    commits = pd.DataFrame({"build_sk": [1]})
    result, _ = check_build_linkage(builds, commits)
    assert result["status"] == "FAIL"


def test_full_linkage_passes():
    builds = pd.DataFrame({"build_id": [1, 2]})
    commits = pd.DataFrame({"build_sk": [1, 2]})
    result, _ = check_build_linkage(builds, commits)
    assert result["status"] == "PASS"