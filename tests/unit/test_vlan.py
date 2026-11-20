"""Test for the VLAN functions."""

import glob
import os

import pytest

from netutils import vlan

MOCK_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "mock", "vlan")
JSON_FILE = "_sent.json"
TXT_FILE = "_sent.txt"


@pytest.mark.parametrize("_file", glob.glob(f"{MOCK_DIR}/to_config/*{JSON_FILE}"))
def test_to_config_success(_file, get_json_data):
    truncate_file = os.path.join(MOCK_DIR, _file[: -len(JSON_FILE)])

    sent_data = get_json_data(os.path.join(MOCK_DIR, _file))
    received_data = get_json_data(truncate_file + "_received.json")
    assert vlan.vlanlist_to_config(**sent_data) == received_data


@pytest.mark.parametrize("sent_data", [{"vlan_list": [4095]}, {"vlan_list": [0]}])
def test_to_config_failure(sent_data):
    with pytest.raises(ValueError, match=r"Valid VLAN range*"):
        vlan.vlanlist_to_config(**sent_data)
    with pytest.raises(ValueError, match="Minimum grouping size must be equal to or greater than one."):
        vlan.vlanlist_to_config("switchport trunk allowed vlan 1025,1069-1072", min_grouping_size=0)


@pytest.mark.parametrize("sent_data", [{"vlan_list": []}])
def test_to_empty_error(sent_data):
    with pytest.raises(ValueError, match=r"The `vlan_list` argument provided*"):
        vlan.vlanlist_to_config(**sent_data)


@pytest.mark.parametrize("_file", glob.glob(f"{MOCK_DIR}/to_list/*{TXT_FILE}"))
def test_to_list_success(_file, get_text_data, get_json_data):
    truncate_file = os.path.join(MOCK_DIR, _file[: -len(TXT_FILE)])

    sent_data = get_text_data(os.path.join(MOCK_DIR, _file))
    received_data = get_json_data(truncate_file + "_received.json")
    assert vlan.vlanconfig_to_list(sent_data) == received_data


def test_to_list_failure():
    with pytest.raises(ValueError, match=r"Valid VLAN range*"):
        vlan.vlanconfig_to_list("switchport trunk allowed vlan 1025,1069-1072,4099")
    with pytest.raises(ValueError, match=r"There were non-digits and dashes*"):
        vlan.vlanconfig_to_list("switchport trunk allowed vlan 1025,1069-1072,BADDATA")
    with pytest.raises(ValueError, match=r"No digits found in `switchport trunk allowed vlan BADDATA`"):
        vlan.vlanconfig_to_list("switchport trunk allowed vlan BADDATA")


# ---------------------------------------------------------------------------
# Edge cases: vlanlist_to_config
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "vlan_list, kwargs, expected",
    [
        # Boundary VLAN IDs on their own
        ([1], {}, ["1"]),
        ([4094], {}, ["4094"]),
        ([1, 4094], {}, ["1,4094"]),
        # Boundary IDs at the edges of a compressed range
        ([1, 2, 3], {}, ["1-3"]),
        ([4092, 4093, 4094], {}, ["4092-4094"]),
        ([4093, 4094], {}, ["4093,4094"]),
        ([4093, 4094], {"min_grouping_size": 2}, ["4093-4094"]),
        ([1, 2, 3, 4092, 4093, 4094], {}, ["1-3,4092-4094"]),
        # Duplicates and ordering at the boundaries
        ([4094, 1, 4094, 1], {}, ["1,4094"]),
        # min_grouping_size=1 with valid boundary IDs never compresses
        ([1, 2, 3, 4094], {"min_grouping_size": 1}, ["1,2,3,4094"]),
    ],
)
def test_to_config_boundaries(vlan_list, kwargs, expected):
    assert vlan.vlanlist_to_config(vlan_list, **kwargs) == expected


def test_to_config_full_range():
    assert vlan.vlanlist_to_config(list(range(1, 4095))) == ["1-4094"]


def test_to_config_line_length_boundary():
    # "100," + 9 four-digit VLANs joined by commas == exactly 48 characters (the default first_line_len).
    vlans = [100] + list(range(1000, 1018, 2))
    result = vlan.vlanlist_to_config(vlans)
    assert result == ["100,1000,1002,1004,1006,1008,1010,1012,1014,1016"]
    assert len(result[0]) == 48

    # One more VLAN pushes it over the limit and onto a second line.
    assert vlan.vlanlist_to_config(vlans + [1018]) == [
        "100,1000,1002,1004,1006,1008,1010,1012,1014,1016",
        "1018",
    ]


def test_to_config_empty_with_return_empty():
    assert vlan.vlanlist_to_config([], return_empty=True) == []


@pytest.mark.parametrize(
    "vlan_list",
    [[0], [4095], [-1], [0, 1], [4094, 4095], [0, 4095], [1, 2, 3, 4095], [0, 1, 2, 3]],
)
def test_to_config_out_of_range(vlan_list):
    with pytest.raises(ValueError, match=r"Valid VLAN range is 1-4094"):
        vlan.vlanlist_to_config(vlan_list)


@pytest.mark.parametrize("min_grouping_size", [0, -1])
def test_to_config_invalid_grouping_size(min_grouping_size):
    with pytest.raises(ValueError, match="Minimum grouping size must be equal to or greater than one."):
        vlan.vlanlist_to_config([1, 2, 3], min_grouping_size=min_grouping_size)


def test_to_config_empty_checked_before_grouping_size():
    with pytest.raises(ValueError, match=r"The `vlan_list` argument provided is empty"):
        vlan.vlanlist_to_config([], min_grouping_size=0)


@pytest.mark.xfail(
    strict=True,
    reason="Known bug: min_grouping_size=1 returns before the 1-4094 range check, so invalid IDs are accepted.",
)
@pytest.mark.parametrize("vlan_list", [[0], [4095]])
def test_to_config_out_of_range_grouping_size_one(vlan_list):
    with pytest.raises(ValueError, match=r"Valid VLAN range is 1-4094"):
        vlan.vlanlist_to_config(vlan_list, min_grouping_size=1)


# ---------------------------------------------------------------------------
# Edge cases: vlanconfig_to_list
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "vlan_config, expected",
    [
        ("1", [1]),
        ("4094", [4094]),
        ("1,4094", [1, 4094]),
        ("1-3", [1, 2, 3]),
        ("4092-4094", [4092, 4093, 4094]),
        ("4093-4094", [4093, 4094]),
        ("1-3,4092-4094", [1, 2, 3, 4092, 4093, 4094]),
        ("switchport trunk allowed vlan 1,4094", [1, 4094]),
        ("switchport trunk allowed vlan add 4094", [4094]),
    ],
)
def test_to_list_boundaries(vlan_config, expected):
    assert vlan.vlanconfig_to_list(vlan_config) == expected


def test_to_list_full_range():
    assert vlan.vlanconfig_to_list("switchport trunk allowed vlan 1-4094") == list(range(1, 4095))


@pytest.mark.parametrize("vlan_config", ["4095", "1,4095", "4094-4095", "1-4095", "switchport trunk allowed vlan 4095"])
def test_to_list_above_max(vlan_config):
    with pytest.raises(ValueError, match=r"Valid VLAN range is 1-4094, found 4095"):
        vlan.vlanconfig_to_list(vlan_config)


@pytest.mark.parametrize(
    "vlan_config",
    ["switchport trunk allowed vlan 1,4094,BAD", "1-3,x", "10 "],
)
def test_to_list_trailing_garbage(vlan_config):
    with pytest.raises(ValueError, match=r"There were non-digits and dashes found"):
        vlan.vlanconfig_to_list(vlan_config)


@pytest.mark.parametrize("vlan_config", ["switchport trunk allowed vlan none", "x"])
def test_to_list_no_digits(vlan_config):
    with pytest.raises(ValueError, match=r"No digits found in"):
        vlan.vlanconfig_to_list(vlan_config)


@pytest.mark.xfail(strict=True, reason="Known bug: no lower-bound check, so VLAN 0 is accepted.")
def test_to_list_below_min():
    with pytest.raises(ValueError, match=r"Valid VLAN range is 1-4094"):
        vlan.vlanconfig_to_list("switchport trunk allowed vlan 0,1")


@pytest.mark.xfail(strict=True, reason="Known bug: an empty string raises IndexError instead of ValueError.")
def test_to_list_empty_string():
    with pytest.raises(ValueError):
        vlan.vlanconfig_to_list("")


@pytest.mark.xfail(
    strict=True,
    reason="Known bug: a run of 3+ consecutive VLANs shorter than min_grouping_size keeps only its first two VLANs.",
)
@pytest.mark.parametrize(
    "vlan_list, min_grouping_size, expected",
    [([1, 2, 3], 4, ["1,2,3"]), ([4091, 4092, 4093, 4094], 5, ["4091,4092,4093,4094"])],
)
def test_to_config_short_group_not_truncated(vlan_list, min_grouping_size, expected):
    assert vlan.vlanlist_to_config(vlan_list, min_grouping_size=min_grouping_size) == expected
