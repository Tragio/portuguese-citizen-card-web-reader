import logging
from dataclasses import dataclass
from typing import final

logger = logging.getLogger(__name__)


@dataclass
class CardField:
    name: str
    v1_range: tuple[int, int] | None
    v2_tag: int | None


@final
class CitizenCardAttributes:
    # Field definitions for V1 and V2 Citizen Card data
    FIELD_DEFINITIONS = {
        "issuingEntity": CardField("issuingEntity", (0, 39), 0xC0),
        "country": CardField("country", (40, 80), 0xC1),
        "documentType": CardField("documentType", (120, 154), 0xC2),
        "documentNumber": CardField("documentNumber", (154, 182), 0xC3),
        "documentVersion": CardField("documentVersion", (214, 230), 0xC4),
        "validityBeginDate": CardField("validityBeginDate", (230, 250), 0xC5),
        "localofRequest": CardField("localofRequest", (250, 310), 0xC6),
        "validityEndDate": CardField("validityEndDate", (310, 330), 0xC7),
        "surname": CardField("surname", (330, 450), 0xC8),
        "name": CardField("name", (450, 570), 0xC9),
        "gender": CardField("gender", (570, 572), 0xCA),
        "nationality": CardField("nationality", (572, 578), 0xCB),
        "dateOfBirth": CardField("dateOfBirth", (578, 598), 0xCC),
        "height": CardField("height", (598, 606), 0xCD),
        "civilianIdNumber": CardField("civilianIdNumber", (606, 624), 0xD0),
        "surnameFather": CardField("surnameFather", (864, 984), 0xD1),
        "givenNameFather": CardField("givenNameFather", (984, 1104), 0xD2),
        "surnameMother": CardField("surnameMother", (624, 744), 0xD3),
        "givenNameMother": CardField("givenNameMother", (744, 864), 0xD4),
        "taxNo": CardField("taxNo", (1104, 1122), 0xD5),
        "socialSecurityNo": CardField("socialSecurityNo", (1122, 1144), 0xD6),
        "healthNo": CardField("healthNo", (1144, 1162), 0xD7),
        "accidentalIndications": CardField("accidentalIndications", (1162, 1282), 0xD8),
        # V1 only fields
        "documentNumberPAN": CardField("documentNumberPAN", (182, 214), None),
        "mrz1": CardField("mrz1", (1282, 1312), None),
        "mrz2": CardField("mrz2", (1312, 1342), None),
        "mrz3": CardField("mrz3", (1342, 1372), None),
    }

    # V2 tags identifiers
    DG13_TAG: int = 0x6D
    DG13_L: int = 0x82

    # Marks the end of V2 data
    ICC_AUT_PK = bytes([0x7F, 0x49])

    def __init__(self, data: bytes):
        self.data = data
        self.attributes: dict[str, str] = {}
        self._parse_data()

    def _decode_field(self, data_slice: bytes) -> str:
        """
        Decode field data and remove null bytes
        """
        return (
            data_slice.decode("utf-8").replace("\x00", "").strip() if data_slice else ""
        )

    def _parse_v1(self) -> None:
        """
        Parse V1 Citizen Card data
        """
        try:
            for field_name, field_def in self.FIELD_DEFINITIONS.items():
                if field_def.v1_range:
                    start, end = field_def.v1_range
                    try:
                        self.attributes[field_name] = self._decode_field(
                            self.data[start:end] if len(self.data) >= end else b""
                        )
                    except UnicodeDecodeError as e:
                        logger.error(f"Error decoding field {field_name}: {e}")
                        self.attributes[field_name] = ""

        except Exception as e:
            logger.error(f"Error parsing V1 Citizen Card data: {e}")
            self.attributes = {field: "" for field in self.FIELD_DEFINITIONS}

    def _parse_v2(self) -> None:
        """
        Parse V2 Citizen Card data
        """
        try:
            parsed = 4  # Skip header - 4 bytes
            while parsed < len(self.data):
                if self.data[parsed : parsed + 2] == self.ICC_AUT_PK:
                    break

                tag = self.data[parsed]
                parsed += 1
                length = self.data[parsed]
                parsed += 1
                value = self.data[parsed : parsed + length]

                for field_name, field_def in self.FIELD_DEFINITIONS.items():
                    if field_def.v2_tag and tag == field_def.v2_tag:
                        self.attributes[field_name] = self._decode_field(value)
                        break

                parsed += length

        except Exception as e:
            logger.error(f"Error parsing V2 card data: {e}")
            raise

    def _parse_data(self) -> None:
        """
        Parse Citizen Card data based on version
        """
        if self.is_v2(self.data):
            self._parse_v2()
        else:
            self._parse_v1()

    def as_dict(self) -> dict[str, str]:
        """
        Return card attributes as a dictionary
        """
        return self.attributes

    def is_v2(self, data: bytes) -> bool:
        """
        Check if data is V2 or V1 Citizen Card
        """
        return data[0] == self.DG13_TAG and data[1] == self.DG13_L
