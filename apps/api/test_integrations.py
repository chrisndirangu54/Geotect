import pytest
from vendor_connectors import integration_catalog
from integration_routes import _safe_url

def test_catalog_contains_major_vendors():
    c=integration_catalog()
    for key in ["esri_arcgis","seequent_evo","archicad","micromine_origin","micromine_nexus","ogc_api_features"]:
        assert key in c

def test_safe_url_rejects_local_and_http():
    with pytest.raises(Exception): _safe_url("http://example.com")
    with pytest.raises(Exception): _safe_url("https://127.0.0.1/test")
    assert _safe_url("https://services.arcgis.com/example")=="https://services.arcgis.com/example"

def test_safe_url_allowlist():
    assert _safe_url("https://api.seequent.com/x",["seequent.com"]).startswith("https://")
    with pytest.raises(Exception): _safe_url("https://example.com/x",["seequent.com"])


def test_second_wave_catalog():
    c=integration_catalog()
    for key in ["autodesk_aps","civil3d","revit","bentley_itwin","openground","trimble_connect","datamine_studio","deswik","maptek","maptek_vulcan","plaxis","geostudio","modflow_flopy"]:
        assert key in c
    assert c["modflow_flopy"]["mode"]=="native"
