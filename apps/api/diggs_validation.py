from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import tempfile,urllib.request

def validate_xml(xml_bytes:bytes,schema_bytes:bytes|None=None,schema_url:str|None=None)->dict:
    try:
        from lxml import etree
    except Exception as exc: raise RuntimeError("lxml is required for DIGGS XML validation") from exc
    if schema_bytes is None:
        if not schema_url: raise ValueError("schema_bytes or schema_url is required")
        with urllib.request.urlopen(schema_url,timeout=20) as r:schema_bytes=r.read()
    parser=etree.XMLParser(resolve_entities=False,no_network=True,huge_tree=False)
    try:doc=etree.fromstring(xml_bytes,parser)
    except etree.XMLSyntaxError as exc:return {"valid":False,"stage":"xml","errors":[str(exc)]}
    try:schema_doc=etree.fromstring(schema_bytes,parser);schema=etree.XMLSchema(schema_doc)
    except Exception as exc:return {"valid":False,"stage":"schema","errors":[str(exc)]}
    valid=schema.validate(doc)
    errors=[{"line":e.line,"column":e.column,"message":e.message,"domain":e.domain_name,"type":e.type_name} for e in schema.error_log]
    return {"valid":bool(valid),"stage":"xsd","errors":errors,"xml_sha256":sha256(xml_bytes).hexdigest(),"schema_sha256":sha256(schema_bytes).hexdigest()}

def validate_with_registry(xml_bytes:bytes,schema_url:str,expected_sha256:str|None=None)->dict:
    with urllib.request.urlopen(schema_url,timeout=20) as r:schema=r.read()
    digest=sha256(schema).hexdigest()
    if expected_sha256 and digest.lower()!=expected_sha256.lower():
        return {"valid":False,"stage":"schema_integrity","errors":[f"Schema digest mismatch: {digest}"]}
    out=validate_xml(xml_bytes,schema_bytes=schema);out["schema_url"]=schema_url
    return out


OFFICIAL_DIGGS3_ARCHIVE="https://github.com/DIGGSml/schema-dev/archive/refs/tags/3.0.0.zip"

def validate_official_diggs3(xml_bytes:bytes,archive_url:str=OFFICIAL_DIGGS3_ARCHIVE)->dict:
    import io,zipfile,tempfile,shutil,os
    from urllib.parse import urlparse
    host=(urlparse(archive_url).hostname or "").lower()
    if host not in {"github.com","codeload.github.com"}:raise ValueError("Official DIGGS bundle URL must be hosted by GitHub")
    with urllib.request.urlopen(archive_url,timeout=45) as r:bundle=r.read()
    bundle_sha=sha256(bundle).hexdigest();root=tempfile.mkdtemp(prefix="diggs3-schema-")
    try:
        with zipfile.ZipFile(io.BytesIO(bundle)) as z:
            for member in z.infolist():
                target=os.path.realpath(os.path.join(root,member.filename))
                if not target.startswith(os.path.realpath(root)+os.sep):raise ValueError("Unsafe ZIP path")
            z.extractall(root)
        candidates=list(Path(root).rglob("Diggs.xsd"))
        if not candidates:raise RuntimeError("Official DIGGS bundle did not contain Diggs.xsd")
        entry=candidates[0]
        from lxml import etree
        parser=etree.XMLParser(resolve_entities=False,no_network=True,huge_tree=False)
        schema_doc=etree.parse(str(entry),parser)
        schema=etree.XMLSchema(schema_doc)
        try:doc=etree.fromstring(xml_bytes,parser)
        except etree.XMLSyntaxError as exc:return {"valid":False,"stage":"xml","errors":[str(exc)],"schema_bundle_sha256":bundle_sha}
        valid=schema.validate(doc)
        errors=[{"line":e.line,"column":e.column,"message":e.message,"domain":e.domain_name,"type":e.type_name} for e in schema.error_log]
        return {"valid":bool(valid),"stage":"official_diggs_3_xsd","errors":errors,"xml_sha256":sha256(xml_bytes).hexdigest(),
          "schema_bundle_sha256":bundle_sha,"schema_entrypoint":str(entry.relative_to(root)),"release":"3.0.0","archive_url":archive_url}
    finally:shutil.rmtree(root,ignore_errors=True)
