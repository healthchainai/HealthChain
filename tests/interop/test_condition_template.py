import pytest
import xmltodict

from healthchain.interop import create_interop

PROBLEM_RELATIONSHIP = """
<entryRelationship inversionInd="false" typeCode="SUBJ">
    <observation classCode="OBS" moodCode="EVN">
        <code code="64572001" codeSystem="2.16.840.1.113883.6.96" />
        <statusCode code="completed" />
        <effectiveTime>
            <low value="20220216" />
        </effectiveTime>
        <value code="385093006" codeSystem="2.16.840.1.113883.6.96"
            displayName="Community acquired pneumonia" />
    </observation>
</entryRelationship>
"""

OTHER_RELATIONSHIP = """
<entryRelationship inversionInd="true" typeCode="SUBJ">
    <act classCode="ACT" moodCode="EVN">
        <code code="1" codeSystem="1.2.840.114350.1.13.525.3.7.2.768076" />
    </act>
</entryRelationship>
"""


def _problem_entry(*relationships: str) -> dict:
    xml = f"<entry><act classCode='ACT' moodCode='EVN'>{''.join(relationships)}</act></entry>"
    return xmltodict.parse(xml)["entry"]


@pytest.mark.parametrize(
    "relationships",
    [
        (PROBLEM_RELATIONSHIP,),
        (PROBLEM_RELATIONSHIP, OTHER_RELATIONSHIP),
        (OTHER_RELATIONSHIP, PROBLEM_RELATIONSHIP),
    ],
    ids=["one-relationship", "observation-first", "observation-second"],
)
def test_problem_act_with_several_entry_relationships_keeps_code_and_onset(
    relationships: tuple,
) -> None:
    engine = create_interop()

    conditions = engine.fhir_generator.generate_resources_from_cda_section_entries(
        [_problem_entry(*relationships)], "problems"
    )

    assert len(conditions) == 1
    assert conditions[0].code.coding[0].code == "385093006"
    assert conditions[0].onsetDateTime is not None
