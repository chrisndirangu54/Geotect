from nonlinear_coupled import solve_staggered_hm,benchmark_suite
from pki import digest_payload
from diggs_validation import validate_xml

def test_digest_stable():
    assert digest_payload({"b":2,"a":1})==digest_payload({"a":1,"b":2})

def test_xml_validation_with_inline_schema():
    x=b'<root><x>1</x></root>'
    s=b'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="root"><xs:complexType><xs:sequence><xs:element name="x" type="xs:int"/></xs:sequence></xs:complexType></xs:element></xs:schema>'''
    assert validate_xml(x,schema_bytes=s)["valid"]

def test_nonlinear_coupled_smoke():
    out=solve_staggered_hm(width_m=20,height_m=10,nx=5,ny=5,iterations=2)
    assert out["iterations"]>=1
    assert out["fem"]["max_displacement_m"]>=0

def test_benchmarks():
    assert benchmark_suite()["passed"]
