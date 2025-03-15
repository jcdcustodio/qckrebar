from rebarcalc import *
import pytest


wclength = clengths_metric


def test_get_optimal_clength():
    cut_1, cut_2, cut_3 = 2.5, 1.1, 3.0
    assert get_optimal_clength(cut_1, wclength) == 7.5
    assert get_optimal_clength(cut_2, wclength) == 9.0
    assert get_optimal_clength(cut_3, wclength) == 6.0


def test_estimate_clength():
    clength_1, reqd_qty_1, wclength_1 = 1.1, 16, 9.0
    assert estimate_clength(clength_1, reqd_qty_1, wclength_1) == 2

    clength_2, reqd_qty_2, wclength_2 = 2.5, 12, 7.5
    assert estimate_clength(clength_2, reqd_qty_2, wclength_2) == 4


def test_use_excess_length():
    estimate_clength(1.1, 16, 9.0)
    assert bool(excess_inventory) == True


def test_record_cut():
    estimate_clength(1.1, 16, 9.0)
    assert bool(cut_record) == True


def test_get_estimate_1():
    # Catch invalid input

    invalid_1 = {"foo":"bar"}
    invalid_2 = {"2.25": "13"}
    invalid_3 = {"2.25": 13}
    invalid_4 = {2.25: "13"}

    with pytest.raises(ValueError):
        get_estimate(invalid_1.items(), wclength)
    with pytest.raises(ValueError):
        get_estimate(invalid_2.items(), wclength)
    with pytest.raises(ValueError):
        get_estimate(invalid_3.items(), wclength)
    with pytest.raises(ValueError):
        get_estimate(invalid_4.items(), wclength)


def test_get_estimate_2():
    # Process valid input

    sample_sched_1 = {3:36, 6:22}
    output_1 = get_estimate(sample_sched_1.items(), wclength)

    assert output_1[0] == {6.0: 40}
    assert output_1[1] == {}
    assert bool(output_1[2]) == True

    sample_sched_2 = {1.1: 22}
    output_2 = get_estimate(sample_sched_2.items(), wclength)

    assert output_2[0] == {9.0: 3}
    assert output_2[1] == {0.2: 2, 2.4: 1}
    assert bool(output_2[2]) == True

