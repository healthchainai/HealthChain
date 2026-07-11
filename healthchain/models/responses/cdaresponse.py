import base64
import logging

from pydantic import BaseModel
from typing import Optional, Dict

from healthchain.utils.utils import search_key


log = logging.getLogger(__name__)


def _import_xmltodict():
    try:
        import xmltodict

        return xmltodict
    except (ImportError, ModuleNotFoundError) as e:
        raise ImportError(
            "CDA support requires the cda extra. Install it with: "
            "pip install healthchain[cda]"
        ) from e


class CdaResponse(BaseModel):
    document: str
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict):
        """
        Loads data from dict (xmltodict format)
        """
        xmltodict = _import_xmltodict()
        return cls(document=xmltodict.unparse(data))

    def model_dump(self, *args, **kwargs) -> Dict:
        """
        Dumps document as dict with xmltodict
        """
        xmltodict = _import_xmltodict()
        return xmltodict.parse(self.document)

    def model_dump_xml(self, *args, **kwargs) -> str:
        """
        Decodes and dumps document as an xml string
        """
        xmltodict = _import_xmltodict()
        xml_dict = xmltodict.parse(self.document)
        document = search_key(xml_dict, "tns:Document")
        if document is None:
            log.warning("Couldn't find document under namespace 'tns:Document")
            return ""

        cda = base64.b64decode(document).decode("UTF-8")

        return cda
