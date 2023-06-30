import pytest
from pandas import DataFrame

from src.lake_modelling.utils.lake_model import Lake, LimeProduct, Model

LIME_PRODUCT_NAME = "SK2"
FLOW_PROFILE = "kyst"

test_lake = Lake(area=0.001, depth=0.05, tau=0.8, flow_prof=FLOW_PROFILE)
test_product = LimeProduct(LIME_PRODUCT_NAME)
test_model = Model(lake=test_lake, lime_product=test_product)


class TestLakeProperties:
    def test_lake_volume_calculation(self):
        assert test_lake.volume == 50000

    def test_lake_mean_annual_flow(self):
        assert test_lake.mean_annual_flow == 5208.0

    def test_lake_monthly_flows(self):
        month = 8
        flow = 3646.0

        assert isinstance(test_lake.monthly_flows, dict)
        assert test_lake.monthly_flows[month] == flow

    def test_valid_lake_pH_0_A_pH(self):
        lake_1 = Lake(pH_lake0=4.5, colour_lake0=0.5)
        lake_2 = Lake(pH_lake0=4.5, colour_lake0=3)
        lake_3 = Lake(pH_lake0=4.5, colour_lake0=7)
        lake_4 = Lake(pH_lake0=5.5, colour_lake0=0.5)
        lake_5 = Lake(pH_lake0=5.5, colour_lake0=4)
        lake_6 = Lake(pH_lake0=5.5, colour_lake0=21)

        lake_7 = Lake(pH_lake0=2, colour_lake0=21)
        lake_8 = Lake(pH_lake0=5.5, colour_lake0=15)

        good_lakes = [lake_1, lake_2, lake_3, lake_4, lake_5, lake_6]
        bad_lakes = [lake_7, lake_8]

        for lake in good_lakes:
            assert isinstance(lake.pH_0, float)
            assert isinstance(lake.A_pH, float)

        for lake in bad_lakes:
            with pytest.raises(ValueError):
                lake.pH_0
            with pytest.raises(ValueError):
                lake.A_pH


class TestLimeProduct:
    def test_valid_lime_product_name(self):
        with pytest.raises(KeyError):
            bad_product_name = LimeProduct(name="ipsum lorem")

    def test_lime_properties(self):
        test_product._get_lime_properties(LIME_PRODUCT_NAME)

        assert isinstance(test_product.ca_pct, float)
        assert isinstance(test_product.mg_pct, float)
        assert isinstance(test_product.dry_fac, float)
        assert isinstance(test_product.col_depth, float)
        assert len(test_product.id_list) == 5
        assert len(test_product.od_list) == 5

    def test_inst_dissolution(self):
        prod = test_product
        pH = 5
        dose = 10

        d = prod.get_instantaneous_dissolution(pH, dose)

        assert d == 60.0


class TestModel:
    def test_method_factor(self):
        lake = test_lake
        prod = test_product
        model_wet = test_model
        model_dry = Model(lake=lake, lime_product=prod, spr_meth="dry")

        assert model_wet.method_fac == 1
        assert model_dry.method_fac == 0.6

    def test_C_inst0(self):
        assert round(test_model.C_inst0, 6) == 1.993075

    def test_C_bott0(self):
        assert round(test_model.C_bott0, 6) == 0.623098

    def test_pH_from_delta_Ca(self):
        # TO DO: test this method
        pass

    def test_model_returns_a_valid_dataframe(self):
        df = test_model.run()

        assert isinstance(df, DataFrame)
        assert not df.empty
