"""Checked DESNZ 2026 reference constants, not customer data.

Contains public sector information licensed under OGL v3.0, except stated exceptions.
Source: UK Government GHG Conversion Factors for Company Reporting, full set.
Values independently checked against the downloaded original workbook cells.
Only the limited operational boundary documented in README.md is enabled here.
"""
from dataclasses import asdict, dataclass

SOURCE_URL = 'https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026'
WORKBOOK_URL = 'https://assets.publishing.service.gov.uk/media/6a29392bade52dc0882218a8/ghg-conversion-factors-2026-full-set.xlsx'
WORKBOOK_SHA256 = 'b5c4f2f86cdc74707337b2fb013b44ded189a1b528f5e29ea99856ba65ae0205'


@dataclass(frozen=True)
class Factor:
    factor_id: str
    value: float
    unit: str
    worksheet: str
    cell: str
    boundary: str
    geography: str = 'UK'
    year: int = 2026
    source_url: str = SOURCE_URL
    workbook_url: str = WORKBOOK_URL
    workbook_sha256: str = WORKBOOK_SHA256
    verified_on: str = '2026-10-10'

    def record(self):
        return asdict(self)


DEFAULT_FACTORS = {
    'grid_generation': Factor('UK_GRID_GENERATION_2026', .13096, 'kgCO2e/kWh',
        'UK electricity', 'E25', 'Electricity generation only; excludes fuel upstream and grid losses.'),
    'grid_losses': Factor('UK_GRID_TD_2026', .01299, 'kgCO2e/kWh',
        'Transmission and distribution', 'E22', 'Generation associated with transmission/distribution losses per purchased kWh.'),
    'gas_gross': Factor('UK_GAS_GROSS_CV_2026', .18231, 'kgCO2e/kWh_gross',
        'Fuels', 'D42', 'Natural gas combustion, gross calorific-value basis; excludes upstream fuel.'),
    'gas_net': Factor('UK_GAS_NET_CV_2026', .20199, 'kgCO2e/kWh_net',
        'Fuels', 'D41', 'Natural gas combustion, net calorific-value basis; excludes upstream fuel.'),
    'petrol': Factor('UK_AVERAGE_PETROL_CAR_DIRECT_2026', .16152, 'kgCO2e/km',
        'Passenger vehicles', 'H54', 'Average petrol car direct operating emissions; excludes fuel upstream/manufacture.'),
    'diesel': Factor('UK_AVERAGE_DIESEL_CAR_DIRECT_2026', .17265, 'kgCO2e/km',
        'Passenger vehicles', 'D54', 'Average diesel car direct operating emissions; excludes fuel upstream/manufacture.'),
}
