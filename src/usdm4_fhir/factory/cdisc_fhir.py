from usdm4.api.code import Code


class CDISCFHIR:
    @classmethod
    def from_c201264(cls, code: Code) -> str:
        """Converts a CDISC code for reletive timing to the equivalent FHIR value"""
        map = {"After": "after", "Before": "before", "Fixed Reference": "concurrent"}
        result = map.get(code.decode, "concurrent")
        return result
