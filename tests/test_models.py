from models import CompanyIntelligence


def test_confidence_is_bounded():
    item = CompanyIntelligence(
        domain="example.com",
        company_overview="Example builds software.",
        target_audience_icp="Developers.",
        data_confidence_score=0.8,
    )
    assert item.data_confidence_score == 0.8
