"""Tests for notebook-friendly helper utilities."""

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

pd = pytest.importorskip("pandas")
pytest.importorskip("numpy")

from synqc_live.notebook_helpers import quickstart_demo


def test_quickstart_demo_returns_dataframes():
    iter_df, adapt_df = quickstart_demo(num_iterations=2, plot=False)

    assert isinstance(iter_df, pd.DataFrame)
    assert not iter_df.empty
    assert isinstance(adapt_df, pd.DataFrame)
